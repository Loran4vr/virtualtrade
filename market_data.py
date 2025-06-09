from flask import Blueprint, jsonify, request, current_app
import requests
import os
from datetime import datetime, timedelta
import json
import uuid
import yfinance as yf
from functools import lru_cache
import threading
import time

market_data_bp = Blueprint('market_data', __name__)

# Alpha Vantage API key
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', 'demo')

# Cache for storing market data to reduce API calls
market_data_cache = {}
cache_expiry = {}

# Cache for market data
market_data_cache = {}
cache_lock = threading.Lock()
CACHE_DURATION = 60  # seconds

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

def update_cache():
    while True:
        with cache_lock:
            current_time = datetime.now()
            market_data_cache.clear()
        time.sleep(CACHE_DURATION)

# Start cache update thread
cache_thread = threading.Thread(target=update_cache, daemon=True)
cache_thread.start()

@lru_cache(maxsize=100)
def get_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        return stock.info
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return None

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

@market_data_bp.route('/stock/search', methods=['GET'])
def search_stocks_alpha():
    """Search for stocks using Alpha Vantage API"""
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
    
    # Check for API errors
    if 'Error Message' in data:
        return jsonify({'error': data['Error Message']}), 500
    
    if 'Note' in data:
        return jsonify({'error': 'API rate limit reached. Please try again later.'}), 429
    
    # Filter for Indian stocks (NSE/BSE)
    if 'bestMatches' in data:
        indian_stocks = [stock for stock in data['bestMatches'] 
                        if stock['4. region'] == 'India' or 
                           '.BSE' in stock['1. symbol'] or 
                           '.NSE' in stock['1. symbol']]
        data['bestMatches'] = indian_stocks
        set_cached_data(cache_key, data)
        return jsonify(data)
    else:
        return jsonify({'bestMatches': [], 'message': 'No matching stocks found'})

@market_data_bp.route('/stock/technical/<symbol>', methods=['GET'])
def get_technical_indicators(symbol):
    """Get technical indicators for a stock"""
    cache_key = f"technical_{symbol}"
    cached_data = get_cached_data(cache_key, expiry_minutes=5)
    if cached_data:
        return jsonify(cached_data)
    
    try:
        # Get daily data for technical analysis
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}.BSE&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch stock data'}), 500
            
        data = response.json()
        if 'Time Series (Daily)' not in data:
            return jsonify({'error': 'Invalid data format'}), 500
            
        # Calculate technical indicators
        daily_data = data['Time Series (Daily)']
        dates = sorted(daily_data.keys())[:30]  # Last 30 days
        prices = [float(daily_data[date]['4. close']) for date in dates]
        
        # Calculate SMA (Simple Moving Average)
        sma_20 = sum(prices[:20]) / 20 if len(prices) >= 20 else None
        sma_50 = sum(prices[:50]) / 50 if len(prices) >= 50 else None
        
        # Calculate RSI (Relative Strength Index)
        if len(prices) >= 14:
            gains = [max(prices[i] - prices[i-1], 0) for i in range(1, len(prices))]
            losses = [max(prices[i-1] - prices[i], 0) for i in range(1, len(prices))]
            avg_gain = sum(gains[:14]) / 14
            avg_loss = sum(losses[:14]) / 14
            rsi = 100 - (100 / (1 + avg_gain/avg_loss)) if avg_loss != 0 else 100
        else:
            rsi = None
        
        # Calculate MACD (Moving Average Convergence Divergence)
        if len(prices) >= 26:
            ema_12 = sum(prices[:12]) / 12
            ema_26 = sum(prices[:26]) / 26
            macd = ema_12 - ema_26
            signal_line = sum(prices[:9]) / 9
            macd_histogram = macd - signal_line
        else:
            macd = signal_line = macd_histogram = None
        
        results = {
            'symbol': symbol,
            'indicators': {
                'sma_20': sma_20,
                'sma_50': sma_50,
                'rsi': rsi,
                'macd': {
                    'macd': macd,
                    'signal': signal_line,
                    'histogram': macd_histogram
                }
            },
            'current_price': prices[0] if prices else None,
            'price_change': prices[0] - prices[1] if len(prices) > 1 else None,
            'price_change_percent': ((prices[0] - prices[1]) / prices[1] * 100) if len(prices) > 1 else None
        }
        
        set_cached_data(cache_key, results)
        return jsonify(results)
    except Exception as e:
        print(f"Error calculating technical indicators: {e}")
        return jsonify({'error': 'Failed to calculate technical indicators'}), 500

@market_data_bp.route('/stock/fundamentals/<symbol>', methods=['GET'])
def get_fundamentals(symbol):
    """Get fundamental data for a stock"""
    cache_key = f"fundamentals_{symbol}"
    cached_data = get_cached_data(cache_key, expiry_minutes=60)  # Cache for 1 hour
    if cached_data:
        return jsonify(cached_data)
    
    try:
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}.BSE&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch fundamental data'}), 500
            
        data = response.json()
        if not data:
            return jsonify({'error': 'No data available'}), 404
            
        results = {
            'symbol': symbol,
            'name': data.get('Name'),
            'sector': data.get('Sector'),
            'industry': data.get('Industry'),
            'market_cap': float(data.get('MarketCapitalization', 0)),
            'pe_ratio': float(data.get('PERatio', 0)),
            'eps': float(data.get('EPS', 0)),
            'dividend_yield': float(data.get('DividendYield', 0)),
            'beta': float(data.get('Beta', 0)),
            '52_week_high': float(data.get('52WeekHigh', 0)),
            '52_week_low': float(data.get('52WeekLow', 0)),
            'volume': int(data.get('Volume', 0)),
            'avg_volume': int(data.get('AverageVolume', 0))
        }
        
        set_cached_data(cache_key, results)
        return jsonify(results)
    except Exception as e:
        print(f"Error fetching fundamental data: {e}")
        return jsonify({'error': 'Failed to fetch fundamental data'}), 500

@market_data_bp.route('/futures', methods=['GET'])
def get_futures():
    """Get available futures contracts"""
    cache_key = "futures"
    cached_data = get_cached_data(cache_key, expiry_minutes=5)
    if cached_data:
        return jsonify(cached_data)
    
    try:
        # Get NIFTY futures data
        url = "https://www.nseindia.com/api/equity-derivatives?index=NIFTY"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            futures = []
            
            for contract in data.get('data', []):
                if contract.get('instrumentType') == 'FUT':
                    futures.append({
                        'symbol': contract.get('symbol'),
                        'expiry': contract.get('expiryDate'),
                        'strike': float(contract.get('strikePrice', 0)),
                        'last_price': float(contract.get('lastPrice', 0)),
                        'change': float(contract.get('pChange', 0)),
                        'oi': int(contract.get('openInterest', 0)),
                        'volume': int(contract.get('totalTradedVolume', 0))
                    })
            
            set_cached_data(cache_key, futures)
            return jsonify(futures)
    except Exception as e:
        print(f"Error fetching futures data: {e}")
        return jsonify({'error': 'Failed to fetch futures data'}), 500

@market_data_bp.route('/options', methods=['GET'])
def get_options():
    """Get available options contracts"""
    cache_key = "options"
    cached_data = get_cached_data(cache_key, expiry_minutes=5)
    if cached_data:
        return jsonify(cached_data)
    
    try:
        # Get NIFTY options data
        url = "https://www.nseindia.com/api/equity-derivatives?index=NIFTY"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            options = {
                'calls': [],
                'puts': []
            }
            
            for contract in data.get('data', []):
                if contract.get('instrumentType') == 'OPT':
                    option_data = {
                        'symbol': contract.get('symbol'),
                        'expiry': contract.get('expiryDate'),
                        'strike': float(contract.get('strikePrice', 0)),
                        'last_price': float(contract.get('lastPrice', 0)),
                        'change': float(contract.get('pChange', 0)),
                        'oi': int(contract.get('openInterest', 0)),
                        'volume': int(contract.get('totalTradedVolume', 0)),
                        'implied_volatility': float(contract.get('impliedVolatility', 0))
                    }
                    
                    if contract.get('optionType') == 'CE':
                        options['calls'].append(option_data)
                    else:
                        options['puts'].append(option_data)
            
            set_cached_data(cache_key, options)
            return jsonify(options)
    except Exception as e:
        print(f"Error fetching options data: {e}")
        return jsonify({'error': 'Failed to fetch options data'}), 500

@market_data_bp.route('/futures/chain/<symbol>', methods=['GET'])
def get_futures_chain(symbol):
    """Get futures chain for a specific symbol"""
    cache_key = f"futures_chain_{symbol}"
    cached_data = get_cached_data(cache_key, expiry_minutes=5)
    if cached_data:
        return jsonify(cached_data)
    
    try:
        url = f"https://www.nseindia.com/api/equity-derivatives?symbol={symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            futures_chain = []
            
            for contract in data.get('data', []):
                if contract.get('instrumentType') == 'FUT':
                    futures_chain.append({
                        'expiry': contract.get('expiryDate'),
                        'last_price': float(contract.get('lastPrice', 0)),
                        'change': float(contract.get('pChange', 0)),
                        'oi': int(contract.get('openInterest', 0)),
                        'volume': int(contract.get('totalTradedVolume', 0)),
                        'basis': float(contract.get('basis', 0)),
                        'cost_of_carry': float(contract.get('costOfCarry', 0))
                    })
            
            set_cached_data(cache_key, futures_chain)
            return jsonify(futures_chain)
    except Exception as e:
        print(f"Error fetching futures chain: {e}")
        return jsonify({'error': 'Failed to fetch futures chain'}), 500

@market_data_bp.route('/options/chain/<symbol>', methods=['GET'])
def get_options_chain(symbol):
    """Get options chain for a specific symbol"""
    cache_key = f"options_chain_{symbol}"
    cached_data = get_cached_data(cache_key, expiry_minutes=5)
    if cached_data:
        return jsonify(cached_data)
    
    try:
        url = f"https://www.nseindia.com/api/equity-derivatives?symbol={symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            options_chain = {
                'expiry_dates': [],
                'strikes': [],
                'calls': {},
                'puts': {}
            }
            
            # Collect unique expiry dates and strikes
            for contract in data.get('data', []):
                if contract.get('instrumentType') == 'OPT':
                    expiry = contract.get('expiryDate')
                    strike = float(contract.get('strikePrice', 0))
                    
                    if expiry not in options_chain['expiry_dates']:
                        options_chain['expiry_dates'].append(expiry)
                    if strike not in options_chain['strikes']:
                        options_chain['strikes'].append(strike)
                    
                    option_data = {
                        'last_price': float(contract.get('lastPrice', 0)),
                        'change': float(contract.get('pChange', 0)),
                        'oi': int(contract.get('openInterest', 0)),
                        'volume': int(contract.get('totalTradedVolume', 0)),
                        'implied_volatility': float(contract.get('impliedVolatility', 0)),
                        'delta': float(contract.get('delta', 0)),
                        'gamma': float(contract.get('gamma', 0)),
                        'theta': float(contract.get('theta', 0)),
                        'vega': float(contract.get('vega', 0))
                    }
                    
                    if contract.get('optionType') == 'CE':
                        if expiry not in options_chain['calls']:
                            options_chain['calls'][expiry] = {}
                        options_chain['calls'][expiry][strike] = option_data
                    else:
                        if expiry not in options_chain['puts']:
                            options_chain['puts'][expiry] = {}
                        options_chain['puts'][expiry][strike] = option_data
            
            # Sort expiry dates and strikes
            options_chain['expiry_dates'].sort()
            options_chain['strikes'].sort()
            
            set_cached_data(cache_key, options_chain)
            return jsonify(options_chain)
    except Exception as e:
        print(f"Error fetching options chain: {e}")
        return jsonify({'error': 'Failed to fetch options chain'}), 500

@market_data_bp.route('/futures/place-order', methods=['POST'])
def place_futures_order():
    """Place a futures order"""
    try:
        data = request.json
        # Validate order data
        required_fields = ['symbol', 'expiry', 'quantity', 'order_type', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # In a real system, this would be saved to a database
        order = {
            'id': str(uuid.uuid4()),
            'symbol': data['symbol'],
            'expiry': data['expiry'],
            'quantity': int(data['quantity']),
            'order_type': data['order_type'],
            'price': float(data['price']),
            'status': 'PAPER_TRADING',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(order)
    except Exception as e:
        print(f"Error placing futures order: {e}")
        return jsonify({'error': 'Failed to place order'}), 500

@market_data_bp.route('/options/place-order', methods=['POST'])
def place_options_order():
    """Place an options order"""
    try:
        data = request.json
        # Validate order data
        required_fields = ['symbol', 'expiry', 'strike', 'option_type', 'quantity', 'order_type', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # In a real system, this would be saved to a database
        order = {
            'id': str(uuid.uuid4()),
            'symbol': data['symbol'],
            'expiry': data['expiry'],
            'strike': float(data['strike']),
            'option_type': data['option_type'],
            'quantity': int(data['quantity']),
            'order_type': data['order_type'],
            'price': float(data['price']),
            'status': 'PAPER_TRADING',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(order)
    except Exception as e:
        print(f"Error placing options order: {e}")
        return jsonify({'error': 'Failed to place order'}), 500

@market_data_bp.route('/portfolio/holdings', methods=['GET'])
def get_holdings():
    """Get user's holdings"""
    try:
        # In a real system, this would fetch from a database
        holdings = [
            {
                'symbol': 'RELIANCE',
                'quantity': 10,
                'average_price': 2500.50,
                'current_price': 2550.75,
                'value': 25507.50,
                'pnl': 507.50,
                'pnl_percentage': 2.03,
                'type': 'EQUITY'
            },
            {
                'symbol': 'NIFTY',
                'quantity': 1,
                'average_price': 19500.00,
                'current_price': 19650.25,
                'value': 19650.25,
                'pnl': 150.25,
                'pnl_percentage': 0.77,
                'type': 'FUTURES'
            },
            {
                'symbol': 'BANKNIFTY',
                'quantity': 2,
                'strike': 45000,
                'expiry': '2024-03-28',
                'option_type': 'CE',
                'average_price': 150.75,
                'current_price': 165.50,
                'value': 331.00,
                'pnl': 29.50,
                'pnl_percentage': 9.78,
                'type': 'OPTIONS'
            }
        ]
        return jsonify(holdings)
    except Exception as e:
        print(f"Error fetching holdings: {e}")
        return jsonify({'error': 'Failed to fetch holdings'}), 500

@market_data_bp.route('/portfolio/transactions', methods=['GET'])
def get_transactions():
    """Get user's transaction history"""
    try:
        # In a real system, this would fetch from a database
        transactions = [
            {
                'id': '1',
                'symbol': 'RELIANCE',
                'type': 'BUY',
                'quantity': 10,
                'price': 2500.50,
                'value': 25005.00,
                'timestamp': '2024-03-20T10:30:00',
                'order_type': 'MARKET',
                'status': 'COMPLETED'
            },
            {
                'id': '2',
                'symbol': 'NIFTY',
                'type': 'SELL',
                'quantity': 1,
                'price': 19650.25,
                'value': 19650.25,
                'timestamp': '2024-03-21T14:45:00',
                'order_type': 'LIMIT',
                'status': 'COMPLETED'
            }
        ]
        return jsonify(transactions)
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return jsonify({'error': 'Failed to fetch transactions'}), 500

@market_data_bp.route('/portfolio/watchlist', methods=['GET'])
def get_watchlist():
    """Get user's watchlist"""
    try:
        # In a real system, this would fetch from a database
        watchlist = [
            {
                'symbol': 'RELIANCE',
                'name': 'Reliance Industries',
                'last_price': 2550.75,
                'change': 2.03,
                'volume': 1500000,
                'market_cap': 1720000
            },
            {
                'symbol': 'TCS',
                'name': 'Tata Consultancy Services',
                'last_price': 3850.25,
                'change': -0.75,
                'volume': 850000,
                'market_cap': 1450000
            }
        ]
        return jsonify(watchlist)
    except Exception as e:
        print(f"Error fetching watchlist: {e}")
        return jsonify({'error': 'Failed to fetch watchlist'}), 500

@market_data_bp.route('/portfolio/watchlist', methods=['POST'])
def add_to_watchlist():
    """Add symbol to watchlist"""
    try:
        data = request.json
        if 'symbol' not in data:
            return jsonify({'error': 'Symbol is required'}), 400
        
        # In a real system, this would save to a database
        return jsonify({'message': f'Added {data["symbol"]} to watchlist'})
    except Exception as e:
        print(f"Error adding to watchlist: {e}")
        return jsonify({'error': 'Failed to add to watchlist'}), 500

@market_data_bp.route('/portfolio/watchlist/<symbol>', methods=['DELETE'])
def remove_from_watchlist(symbol):
    """Remove symbol from watchlist"""
    try:
        # In a real system, this would remove from a database
        return jsonify({'message': f'Removed {symbol} from watchlist'})
    except Exception as e:
        print(f"Error removing from watchlist: {e}")
        return jsonify({'error': 'Failed to remove from watchlist'}), 500

@market_data_bp.route('/orders/active', methods=['GET'])
def get_active_orders():
    """Get active orders"""
    try:
        # In a real system, this would fetch from a database
        active_orders = [
            {
                'id': '1',
                'symbol': 'RELIANCE',
                'type': 'BUY',
                'quantity': 5,
                'price': 2480.00,
                'order_type': 'LIMIT',
                'status': 'PENDING',
                'timestamp': '2024-03-22T09:15:00'
            }
        ]
        return jsonify(active_orders)
    except Exception as e:
        print(f"Error fetching active orders: {e}")
        return jsonify({'error': 'Failed to fetch active orders'}), 500

@market_data_bp.route('/orders/history', methods=['GET'])
def get_order_history():
    """Get order history"""
    try:
        # In a real system, this would fetch from a database
        order_history = [
            {
                'id': '1',
                'symbol': 'RELIANCE',
                'type': 'BUY',
                'quantity': 10,
                'price': 2500.50,
                'order_type': 'MARKET',
                'status': 'COMPLETED',
                'timestamp': '2024-03-20T10:30:00'
            }
        ]
        return jsonify(order_history)
    except Exception as e:
        print(f"Error fetching order history: {e}")
        return jsonify({'error': 'Failed to fetch order history'}), 500

@market_data_bp.route('/orders/<order_id>', methods=['PUT'])
def modify_order(order_id):
    """Modify an existing order"""
    try:
        data = request.json
        # In a real system, this would update in a database
        return jsonify({'message': f'Modified order {order_id}'})
    except Exception as e:
        print(f"Error modifying order: {e}")
        return jsonify({'error': 'Failed to modify order'}), 500

@market_data_bp.route('/orders/<order_id>', methods=['DELETE'])
def cancel_order(order_id):
    """Cancel an existing order"""
    try:
        # In a real system, this would update in a database
        return jsonify({'message': f'Cancelled order {order_id}'})
    except Exception as e:
        print(f"Error cancelling order: {e}")
        return jsonify({'error': 'Failed to cancel order'}), 500

@market_data_bp.route('/market/depth/<symbol>', methods=['GET'])
def get_market_depth(symbol):
    """Get market depth for a symbol"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Simulate market depth data
        last_price = info.get('regularMarketPrice', 0)
        spread = last_price * 0.001  # 0.1% spread
        
        bids = [
            {'price': last_price - spread * i, 'quantity': int(1000 * (1 - i/10))}
            for i in range(10)
        ]
        
        asks = [
            {'price': last_price + spread * i, 'quantity': int(1000 * (1 - i/10))}
            for i in range(10)
        ]
        
        return jsonify({
            'bids': bids,
            'asks': asks,
            'last_price': last_price,
            'volume': info.get('regularMarketVolume', 0),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error fetching market depth: {e}")
        return jsonify({'error': 'Failed to fetch market depth'}), 500

@market_data_bp.route('/market/chart/<symbol>', methods=['GET'])
def get_chart_data(symbol):
    """Get chart data for a symbol"""
    try:
        timeframe = request.args.get('timeframe', '1D')
        # In a real system, this would fetch from a market data provider
        chart_data = {
            'symbol': symbol,
            'timeframe': timeframe,
            'candles': [
                {
                    'timestamp': '2024-03-22T09:15:00',
                    'open': 2540.00,
                    'high': 2550.00,
                    'low': 2535.00,
                    'close': 2545.75,
                    'volume': 150000
                }
            ],
            'indicators': {
                'sma_20': 2530.25,
                'sma_50': 2520.50,
                'rsi': 65.5,
                'macd': {
                    'macd': 15.25,
                    'signal': 12.50,
                    'histogram': 2.75
                }
            }
        }
        return jsonify(chart_data)
    except Exception as e:
        print(f"Error fetching chart data: {e}")
        return jsonify({'error': 'Failed to fetch chart data'}), 500

@market_data_bp.route('/risk/margin', methods=['POST'])
def calculate_margin():
    """Calculate margin requirement for a trade"""
    try:
        data = request.json
        # In a real system, this would calculate based on exchange rules
        margin = {
            'initial_margin': 50000.00,
            'maintenance_margin': 40000.00,
            'available_margin': 100000.00,
            'utilized_margin': 50000.00
        }
        return jsonify(margin)
    except Exception as e:
        print(f"Error calculating margin: {e}")
        return jsonify({'error': 'Failed to calculate margin'}), 500

@market_data_bp.route('/risk/exposure', methods=['GET'])
def get_risk_exposure():
    """Get current risk exposure"""
    try:
        # In a real system, this would calculate based on positions
        exposure = {
            'total_exposure': 100000.00,
            'equity_exposure': 50000.00,
            'futures_exposure': 30000.00,
            'options_exposure': 20000.00,
            'net_delta': 0.75,
            'net_gamma': 0.25,
            'net_theta': -0.15,
            'net_vega': 0.10
        }
        return jsonify(exposure)
    except Exception as e:
        print(f"Error fetching risk exposure: {e}")
        return jsonify({'error': 'Failed to fetch risk exposure'}), 500

@market_data_bp.route('/market/overview', methods=['GET'])
def get_market_overview():
    try:
        indices = ['^NSEI', '^BSESN', '^NSEBANK']
        overview = {}
        
        for index in indices:
            data = get_stock_data(index)
            if data:
                overview[index] = {
                    'price': data.get('regularMarketPrice', 0),
                    'change': data.get('regularMarketChange', 0),
                    'change_percent': data.get('regularMarketChangePercent', 0)
                }
        
        return jsonify(overview)
    except Exception as e:
        print(f"Error fetching market overview: {e}")
        return jsonify({'error': 'Failed to fetch market overview'}), 500

@market_data_bp.route('/market/search', methods=['GET'])
def search_stocks_yahoo():
    """Search for stocks using Yahoo Finance API"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    cache_key = f"yahoo_search_{query}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return jsonify(cached_data)
    
    try:
        # Use yfinance to search for stocks
        tickers = yf.Tickers(query)
        results = []
        
        for symbol, ticker in tickers.tickers.items():
            try:
                info = ticker.info
                if info:
                    results.append({
                        'symbol': symbol,
                        'name': info.get('longName', ''),
                        'exchange': info.get('exchange', ''),
                        'type': info.get('quoteType', ''),
                        'currency': info.get('currency', '')
                    })
            except Exception as e:
                print(f"Error fetching info for {symbol}: {e}")
                continue
        
        data = {'results': results}
        set_cached_data(cache_key, data)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@market_data_bp.route('/market/stock/<symbol>', methods=['GET'])
def get_stock_data_route(symbol):
    try:
        interval = request.args.get('interval', '1d')
        stock = yf.Ticker(symbol)
        
        # Get historical data
        hist = stock.history(period='1mo', interval=interval)
        
        # Format data
        data = {
            'meta': {
                'symbol': symbol,
                'name': stock.info.get('longName', ''),
                'currency': stock.info.get('currency', ''),
                'exchange': stock.info.get('exchange', '')
            },
            'chartData': [
                {
                    'timestamp': index.strftime('%Y-%m-%d %H:%M:%S'),
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close'],
                    'volume': row['Volume']
                }
                for index, row in hist.iterrows()
            ],
            'indicators': {
                'sma_20': hist['Close'].rolling(window=20).mean().iloc[-1],
                'sma_50': hist['Close'].rolling(window=50).mean().iloc[-1],
                'rsi': calculate_rsi(hist['Close']),
                'macd': calculate_macd(hist['Close'])
            }
        }
        
        return jsonify(data)
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return jsonify({'error': 'Failed to fetch stock data'}), 500

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

def calculate_macd(prices, fast=12, slow=26, signal=9):
    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return {
        'macd': macd.iloc[-1],
        'signal': signal_line.iloc[-1],
        'histogram': (macd - signal_line).iloc[-1]
    }

