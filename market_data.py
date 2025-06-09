from flask import Blueprint, jsonify, request, current_app
import requests
import os
from datetime import datetime, timedelta
import json

market_data_bp = Blueprint('market_data', __name__)

# Alpha Vantage API key
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', 'demo')

# Cache for storing market data to reduce API calls
market_data_cache = {}
cache_expiry = {}

def get_cached_data(cache_key, expiry_minutes=15):
    """Get data from cache if available and not expired"""
    if cache_key in market_data_cache and cache_key in cache_expiry:
        if datetime.now() < cache_expiry[cache_key]:
            return market_data_cache[cache_key]
    return None

def set_cached_data(cache_key, data, expiry_minutes=15):
    """Store data in cache with expiry time"""
    market_data_cache[cache_key] = data
    cache_expiry[cache_key] = datetime.now() + timedelta(minutes=expiry_minutes)

@market_data_bp.route('/search', methods=['GET'])
def search_symbol():
    """Search for a stock symbol"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    cache_key = f"search_{query}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return jsonify(cached_data)
    
    url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={query}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch data from Alpha Vantage'}), 500
    
    data = response.json()
    
    # Filter for Indian stocks (NSE/BSE)
    if 'bestMatches' in data:
        indian_stocks = [stock for stock in data['bestMatches'] 
                        if stock['4. region'] == 'India' or 
                           '.BSE' in stock['1. symbol'] or 
                           '.NSE' in stock['1. symbol']]
        result = indian_stocks
    else:
        result = []
    
    set_cached_data(cache_key, result)
    return jsonify(result)

@market_data_bp.route('/quote', methods=['GET'])
def get_quote():
    """Get current quote for a symbol"""
    symbol = request.args.get('symbol', '')
    if not symbol:
        return jsonify({'error': 'Symbol parameter is required'}), 400
    
    cache_key = f"quote_{symbol}"
    cached_data = get_cached_data(cache_key, expiry_minutes=1)  # Short cache for quotes
    if cached_data:
        return jsonify(cached_data)
    
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch data from Alpha Vantage'}), 500
    
    data = response.json()
    set_cached_data(cache_key, data)
    return jsonify(data)

@market_data_bp.route('/intraday', methods=['GET'])
def get_intraday():
    """Get intraday data for a symbol"""
    symbol = request.args.get('symbol', '')
    interval = request.args.get('interval', '5min')
    
    if not symbol:
        return jsonify({'error': 'Symbol parameter is required'}), 400
    
    cache_key = f"intraday_{symbol}_{interval}"
    cached_data = get_cached_data(cache_key, expiry_minutes=5)
    if cached_data:
        return jsonify(cached_data)
    
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch data from Alpha Vantage'}), 500
    
    data = response.json()
    set_cached_data(cache_key, data)
    return jsonify(data)

@market_data_bp.route('/daily', methods=['GET'])
def get_daily():
    """Get daily data for a symbol"""
    symbol = request.args.get('symbol', '')
    outputsize = request.args.get('outputsize', 'compact')
    
    if not symbol:
        return jsonify({'error': 'Symbol parameter is required'}), 400
    
    cache_key = f"daily_{symbol}_{outputsize}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return jsonify(cached_data)
    
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize={outputsize}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch data from Alpha Vantage'}), 500
    
    data = response.json()
    set_cached_data(cache_key, data)
    return jsonify(data)

@market_data_bp.route('/top-gainers-losers', methods=['GET'])
def get_top_gainers_losers():
    """Get top gainers and losers"""
    cache_key = "top_gainers_losers"
    cached_data = get_cached_data(cache_key, expiry_minutes=60)  # Cache for 1 hour
    if cached_data:
        return jsonify(cached_data)
    
    url = f"https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch data from Alpha Vantage'}), 500
    
    data = response.json()
    set_cached_data(cache_key, data)
    return jsonify(data)

