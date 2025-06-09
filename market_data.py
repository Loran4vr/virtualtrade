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
        print("Search query is empty")
        return jsonify({'error': 'Query parameter is required'}), 400
    
    print(f"Searching for stocks with query: {query}")
    
    cache_key = f"search_{query}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        print(f"Found cached data for query: {query}")
        return jsonify(cached_data)
    
    url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={query}&apikey={ALPHA_VANTAGE_API_KEY}"
    print(f"Making API request to: {url}")
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error from Alpha Vantage API: {response.status_code}")
        return jsonify({'error': 'Failed to fetch data from Alpha Vantage'}), 500
    
    data = response.json()
    print(f"Received data from Alpha Vantage: {data}")
    
    # Check for API errors
    if 'Error Message' in data:
        print(f"Alpha Vantage API error: {data['Error Message']}")
        return jsonify({'error': data['Error Message']}), 500
    
    if 'Note' in data:
        print(f"Alpha Vantage API note: {data['Note']}")
        return jsonify({'error': 'API rate limit reached. Please try again later.'}), 429
    
    # Filter for Indian stocks (NSE/BSE)
    if 'bestMatches' in data:
        indian_stocks = [stock for stock in data['bestMatches'] 
                        if stock['4. region'] == 'India' or 
                           '.BSE' in stock['1. symbol'] or 
                           '.NSE' in stock['1. symbol']]
        print(f"Filtered Indian stocks: {indian_stocks}")
        
        # Return the filtered bestMatches array
        data['bestMatches'] = indian_stocks
        set_cached_data(cache_key, data)
        return jsonify(data)
    else:
        print("No bestMatches found in response")
        return jsonify({'bestMatches': [], 'message': 'No matching stocks found'})

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

@market_data_bp.route('/stock/<symbol>', methods=['GET'])
def get_stock_data(symbol):
    """Get stock data for a symbol with specified interval"""
    interval = request.args.get('interval', 'daily') # Default to daily
    
    if not symbol:
        return jsonify({'error': 'Symbol is required'}), 400

    print(f"Fetching stock data for {symbol} with interval: {interval}")

    cache_key = f"stock_{symbol}_{interval}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        print(f"Found cached data for {symbol} ({interval})")
        return jsonify(cached_data)

    api_key = current_app.config.get('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        return jsonify({'error': 'Alpha Vantage API key not configured'}), 500

    url = ""
    time_series_key = ""
    
    # Determine which Alpha Vantage function to call based on interval
    if interval in ['1min', '5min']:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&outputsize=full&apikey={api_key}"
        time_series_key = f"Time Series ({interval})"
    elif interval == 'daily' or interval == '5day' or interval == '1month' or interval == '1year' or interval == 'lifetime':
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=full&apikey={api_key}" # Use outputsize=full for longer history
        time_series_key = "Time Series (Daily)"
    else:
        return jsonify({'error': 'Invalid interval specified'}), 400

    print(f"Making Alpha Vantage API request: {url}")
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error from Alpha Vantage API ({response.status_code}): {response.text}")
        return jsonify({'error': 'Failed to fetch data from Alpha Vantage'}), 500
    
    data = response.json()
    print(f"Received data from Alpha Vantage: {data}")

    if 'Error Message' in data:
        print(f"Alpha Vantage Error: {data['Error Message']}")
        return jsonify({'error': data['Error Message']}), 400
    
    if time_series_key not in data:
        print(f"No time series data found for {symbol} with interval {interval}")
        return jsonify({'error': 'No time series data found'}), 404
    
    time_series = data[time_series_key]
    
    # Process the data
    dates_raw = sorted(time_series.keys())
    
    # Limit data for '5day' interval to last 5 days (approx 5*24*60/interval_minutes if intraday)
    # For simplicity, we'll just take the last 5 days worth of data points from the daily series
    # or a recent subset for intraday. Let's aim for a reasonable number of points for display.
    
    processed_dates = []
    processed_prices = []
    current_price = None
    previous_close = None
    
    # Get the latest quote information for display
    latest_date_str = sorted(time_series.keys(), reverse=True)[0]
    latest_day_data = time_series[latest_date_str]

    # Use '4. close' for daily, and '4. close' for intraday
    current_price = float(latest_day_data.get('4. close', latest_day_data.get('5. adjusted close', 0.0)))
    
    # Try to get previous close for change calculation
    if len(dates_raw) > 1: # If there's more than one data point
        second_latest_date_str = sorted(time_series.keys(), reverse=True)[1]
        previous_close = float(time_series[second_latest_date_str].get('4. close', time_series[second_latest_date_str].get('5. adjusted close', 0.0)))
    
    change = None
    change_percent = None
    if current_price is not None and previous_close is not None:
        change = current_price - previous_close
        if previous_close != 0:
            change_percent = (change / previous_close) * 100

    # Populate processed_dates and processed_prices based on interval and desired display length
    if interval == 'daily':
        # Get last 30 days of daily data
        for date_str in sorted(time_series.keys(), reverse=True)[:30]:
            processed_dates.insert(0, date_str)
            processed_prices.insert(0, float(time_series[date_str].get('4. close', time_series[date_str].get('5. adjusted close'))))
    elif interval == '5day':
        # Get last 5 days of daily data (approx 5 data points)
        for date_str in sorted(time_series.keys(), reverse=True)[:5]:
            processed_dates.insert(0, date_str)
            processed_prices.insert(0, float(time_series[date_str].get('4. close', time_series[date_str].get('5. adjusted close'))))
    elif interval == '1month':
        # Get last 30 days of daily data
        for date_str in sorted(time_series.keys(), reverse=True)[:30]:
            processed_dates.insert(0, date_str)
            processed_prices.insert(0, float(time_series[date_str].get('4. close', time_series[date_str].get('5. adjusted close'))))
    elif interval == '1year':
        # Get last 365 days of daily data
        for date_str in sorted(time_series.keys(), reverse=True)[:365]:
            processed_dates.insert(0, date_str)
            processed_prices.insert(0, float(time_series[date_str].get('4. close', time_series[date_str].get('5. adjusted close'))))
    elif interval == 'lifetime':
        # Get all available daily data
        for date_str in sorted(time_series.keys()): # Sort chronologically for chart
            processed_dates.append(date_str)
            processed_prices.append(float(time_series[date_str].get('4. close', time_series[date_str].get('5. adjusted close'))))
    elif interval in ['1min', '5min']:
        # For intraday, take the most recent 200 data points for a meaningful chart
        for date_time_str in sorted(time_series.keys(), reverse=True)[:200]:
            processed_dates.insert(0, date_time_str)
            processed_prices.insert(0, float(time_series[date_time_str]['4. close']))

    processed_data = {
        'symbol': symbol,
        'price': current_price,
        'change': change,
        'change_percent': f"{change_percent:.2f}%" if change_percent is not None else None,
        'latest_trading_day': latest_date_str, # This could be date or datetime depending on interval
        'dates': processed_dates,
        'prices': processed_prices
    }
    
    set_cached_data(cache_key, processed_data)
    return jsonify(processed_data)

@market_data_bp.route('/indices', methods=['GET'])
def get_indices():
    """Get major Indian market indices"""
    cache_key = "indices"
    cached_data = get_cached_data(cache_key, expiry_minutes=5)  # Cache for 5 minutes
    if cached_data:
        return jsonify(cached_data)
    
    indices = {
        'NIFTY 50': '^NSEI',
        'SENSEX': '^BSESN',
        'BANK NIFTY': '^NSEBANK',
        'NIFTY IT': '^CNXIT',
        'NIFTY PHARMA': '^CNXPHARMA',
        'NIFTY AUTO': '^CNXAUTO',
        'NIFTY FMCG': '^CNXFMCG',
        'NIFTY METAL': '^CNXMETAL',
        'NIFTY REALTY': '^CNXREALTY'
    }
    
    results = {}
    for name, symbol in indices.items():
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if 'Global Quote' in data:
                    quote = data['Global Quote']
                    results[name] = {
                        'price': float(quote.get('05. price', 0)),
                        'change': float(quote.get('09. change', 0)),
                        'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                        'volume': int(quote.get('06. volume', 0))
                    }
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            continue
    
    set_cached_data(cache_key, results)
    return jsonify(results)

@market_data_bp.route('/sectors', methods=['GET'])
def get_sectors():
    """Get sector performance"""
    cache_key = "sectors"
    cached_data = get_cached_data(cache_key, expiry_minutes=15)  # Cache for 15 minutes
    if cached_data:
        return jsonify(cached_data)
    
    sectors = {
        'IT': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM'],
        'BANKING': ['HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'AXISBANK', 'SBIN'],
        'PHARMA': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'LUPIN', 'AUROPHARMA'],
        'AUTO': ['MARUTI', 'TATAMOTORS', 'M&M', 'HEROMOTOCO', 'BAJAJ-AUTO'],
        'FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR'],
        'METAL': ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'SAIL', 'JINDALSTEL'],
        'REALTY': ['DLF', 'SUNTV', 'GODREJPROP', 'OBEROIRLTY', 'PRESTIGE']
    }
    
    results = {}
    for sector, stocks in sectors.items():
        try:
            sector_data = []
            for stock in stocks:
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock}.BSE&apikey={ALPHA_VANTAGE_API_KEY}"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if 'Global Quote' in data:
                        quote = data['Global Quote']
                        sector_data.append({
                            'symbol': stock,
                            'price': float(quote.get('05. price', 0)),
                            'change': float(quote.get('09. change', 0)),
                            'change_percent': quote.get('10. change percent', '0%').replace('%', '')
                        })
            
            if sector_data:
                avg_change = sum(float(stock['change_percent']) for stock in sector_data) / len(sector_data)
                results[sector] = {
                    'change_percent': round(avg_change, 2),
                    'stocks': sector_data
                }
        except Exception as e:
            print(f"Error fetching {sector} sector: {e}")
            continue
    
    set_cached_data(cache_key, results)
    return jsonify(results)

@market_data_bp.route('/most-active', methods=['GET'])
def get_most_active():
    """Get most active stocks by volume"""
    cache_key = "most_active"
    cached_data = get_cached_data(cache_key, expiry_minutes=5)  # Cache for 5 minutes
    if cached_data:
        return jsonify(cached_data)
    
    url = f"https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch data'}), 500
    
    data = response.json()
    results = {
        'gainers': [],
        'losers': [],
        'most_active': []
    }
    
    if 'top_gainers' in data:
        results['gainers'] = data['top_gainers'][:5]
    if 'top_losers' in data:
        results['losers'] = data['top_losers'][:5]
    if 'most_actively_traded' in data:
        results['most_active'] = data['most_actively_traded'][:5]
    
    set_cached_data(cache_key, results)
    return jsonify(results)

