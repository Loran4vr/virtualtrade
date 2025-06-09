from flask import Flask, render_template, jsonify, session, redirect, url_for, request, make_response, send_from_directory
import os
from dotenv import load_dotenv
from auth import create_auth_blueprint
from market_data import market_data_bp
from portfolio import portfolio_bp
from config import config
from backend.models import db, User, Portfolio, Transaction, Subscription, HistoricalPrice
from datetime import datetime, timedelta, time, date
from decimal import Decimal
from functools import wraps
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.storage.session import SessionStorage  # Correct import
from sqlalchemy.orm.exc import NoResultFound # Added for oauth_authorized handler
import logging
from backend.subscription import init_stripe, SUBSCRIPTION_PLANS
from whitenoise import WhiteNoise
import requests
from flask_cors import CORS
from backend.database import get_db_connection
from backend.models import init_db
from backend.routes import register_routes
from backend.config import Config

print("##### DEBUG: main.py file has been loaded and executed! #####") # Added top-level print

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # This ensures logs go to stdout/stderr
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Free tier limit
FREE_TIER_LIMIT = 1000000  # 10 lakhs

def create_app():
    # NEW DEBUG: Print all environment variables at the start of create_app
    print("DEBUG: create_app: os.environ content:")
    for key, value in os.environ.items():
        print(f"  {key}={value}")
    print("DEBUG: create_app: End of os.environ content")

    app = Flask(__name__, static_folder='static')
    CORS(app)
    
    # Determine config_name based on environment variable directly inside create_app
    config_name = os.getenv('FLASK_ENV', 'development')
    print(f"DEBUG: create_app: Loading Flask configuration: {config_name}") # New print/log here
    
    # Use WhiteNoise to serve static files
    app.wsgi_app = WhiteNoise(app.wsgi_app, root=os.path.join(app.root_path, 'static'))
    app.wsgi_app.add_files(os.path.join(app.root_path, 'static'), prefix='/') # Add index.html at root

    print(f"Flask static_folder: {os.path.join(app.root_path, 'static')}") # Debug print
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Explicit session configuration
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Required for cross-site redirects
    app.config['SESSION_COOKIE_DOMAIN'] = None  # Let Flask determine the domain
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session lasts 7 days
    
    # Debug print actual cookie settings from app.config
    print(f"DEBUG: Flask app.config cookie settings: Secure={app.config.get('SESSION_COOKIE_SECURE')}, HttpOnly={app.config.get('SESSION_COOKIE_HTTPONLY')}, SameSite={app.config.get('SESSION_COOKIE_SAMESITE')}") # Added print
    
    # Ensure SQLALCHEMY_DATABASE_URI is set
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    print(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}") # Debug print

    # Initialize database
    db.init_app(app)

    # Debug print SECRET_KEY status
    secret_key = app.config.get('SECRET_KEY')
    if secret_key:
        logger.debug(f"SECRET_KEY loaded. Length: {len(secret_key)}. Masked: {secret_key[:5]}...{secret_key[-5:]}")
    else:
        logger.debug("SECRET_KEY not loaded or is None.")

    # Debug print cookie settings
    logger.debug(f"Cookie settings: Secure={app.config.get('SESSION_COOKIE_SECURE')}, HttpOnly={app.config.get('SESSION_COOKIE_HTTPONLY')}, SameSite={app.config.get('SESSION_COOKIE_SAMESITE')}")

    # Initialize Google OAuth directly in main.py
    # Set environment variables for development (if DEBUG is True)
    if app.config.get('DEBUG'):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    
    # Create the Google blueprint
    google_bp = make_google_blueprint(
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        scope=["profile", "email"],
        redirect_to="index", # Redirect to the root endpoint 'index' after successful OAuth
        storage=SessionStorage() # Use session storage explicitly with correct class
    )
    app.register_blueprint(google_bp, url_prefix='/auth') # Register google_bp with app directly, url_prefix corrected to '/auth'
    logger.debug("Google OAuth blueprint registered directly with app")

    # NEW DEBUG: Check Flask's perception of Google OAuth URLs
    with app.test_request_context():
        try:
            login_url = url_for("google.login", _external=True)
            logger.debug(f"DEBUG: Calculated google.login URL: {login_url}")
        except Exception as e:
            logger.debug(f"DEBUG: Error calculating google.login URL: {e}")

        try:
            authorized_url = url_for("google.authorized", _external=True)
            logger.debug(f"DEBUG: Calculated google.authorized URL: {authorized_url}")
        except Exception as e:
            logger.debug(f"DEBUG: Error calculating google.authorized URL: {e}")

    # Initialize Stripe (moved from module level)
    init_stripe(app)

    # Handle Google OAuth callback for user creation/login
    @oauth_authorized.connect_via(google_bp) # Connect via the blueprint instance
    def google_logged_in(blueprint, token):
        logger.debug(f"google_logged_in: Received token: {token is not None}")
        if not token:
            logger.error("google_logged_in: Token is None, returning False")
            return False

        resp = google.get("/oauth2/v2/userinfo")
        logger.debug(f"google_logged_in: Google user info response status: {resp.ok}")
        if not resp.ok:
            logger.error(f"google_logged_in: Failed to get user info: {resp.status_code} - {resp.text}")
            return False

        google_info = resp.json()
        google_user_id = google_info['id']

        # Find or create user
        user = User.query.filter_by(google_id=google_user_id).first()
        if user:
            logger.debug(f"google_logged_in: Found existing user: {user.email} (ID: {user.id})")
        else:
            user = User(
                google_id=google_user_id,
                email=google_info['email'],
                name=google_info['name'],
                picture=google_info.get('picture')
            )
            db.session.add(user)
            db.session.commit()
            logger.debug(f"google_logged_in: Created new user: {user.email} (ID: {user.id})")

        # Create session
        session.clear()  # Clear any existing session data
        session['user_id'] = user.id
        session.permanent = True
        session.modified = True  # Ensure session is marked as modified
        
        # Store OAuth state in session
        session['oauth_state'] = request.args.get('state')
        logger.debug(f"DEBUG:main:google_logged_in: Stored OAuth state in session: {session.get('oauth_state')}")
        print(f"DEBUG:main:google_logged_in: Session user_id set to: {session.get('user_id')}")
        print(f"DEBUG:main:google_logged_in: Session is permanent: {session.permanent}")
        print(f"DEBUG:main:google_logged_in: Session type: {type(session)}")

        # No direct access to cookie value from session object.
        # cookie_value = session.get_cookie_value()
        # if cookie_value:
        #     print(f"DEBUG:main:google_logged_in: Session cookie value: {cookie_value[:20]}...")
        # else:
        #     print("DEBUG:main:google_logged_in: No session cookie value found.")

        # Ensure the session is saved before redirecting
        session.modified = True

        # Redirect to the main page or dashboard after successful login
        resp = make_response(redirect('/'))
        
        logger.debug(f"google_logged_in: User {user.email} successfully logged in, user_id: {user.id}")
        logger.debug(f"google_logged_in: Full session after setting user_id: {dict(session)}")

        return resp
    
    # Test session route
    @app.route('/test-session')
    def test_session():
        session['test'] = 'Hello, World!'
        return jsonify({'session': dict(session)})
    
    # Register blueprints
    app.register_blueprint(create_auth_blueprint(), url_prefix='/auth') # Now calls the blueprint factory
    app.register_blueprint(market_data_bp, url_prefix='/api/market')
    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')

    # Create database tables if they don't exist (now handled by Dockerfile)
    # with app.app_context():
    #     db.create_all()

    # Removed duplicate portfolio related functions and routes. These are now handled by portfolio.py
    # Helper function to check subscription status
    # def check_subscription(user_id):
    #     subscription = Subscription.query.filter_by(user_id=user_id).first()
    #     if not subscription:
    #         return False, FREE_TIER_LIMIT
        
    #     if subscription.expires_at < datetime.utcnow():
    #         return False, FREE_TIER_LIMIT
        
    #     return True, subscription.credit_limit

    # Helper function to check trading limits
    # def check_trading_limit(user_id, amount):
    #     has_subscription, limit = check_subscription(user_id)
    #     portfolio = Portfolio.query.filter_by(user_id=user_id).first()
        
    #     if not portfolio:
    #         return False, "Portfolio not found"
        
    #     total_value = portfolio.cash_balance
    #     # Loop through holdings if they exist
    #     if portfolio.holdings: 
    #         for holding in portfolio.holdings:
    #             total_value += holding.quantity * holding.avg_price
        
    #     if total_value + amount > limit:
    #         return False, f"Trading limit exceeded. Current limit: ₹{limit:,}"
        
    #     return True, None

    # Decorator to check trading limits
    # def trading_limit_required(f):
    #     @wraps(f)
    #     def decorated_function(*args, **kwargs):
    #         if not session.get('user_id'):
    #             return jsonify({'error': 'Not authenticated'}), 401
    #         return f(*args, **kwargs)
    #     return decorated_function
    
    # Catch-all route for React Router (now handled by WhiteNoise)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(app.static_folder + '/' + path):
            return send_from_directory(app.static_folder, path)
        else:
            # Log the index.html path and its existence
            index_path = os.path.join(app.static_folder, 'index.html')
            logger.info(f"Attempting to serve index.html from: {index_path}")
            logger.info(f"index.html exists: {os.path.exists(index_path)}")
            if os.path.exists(index_path):
                with open(index_path, 'r') as f:
                    logger.info(f"index.html content preview: {f.read()[:200]}...")
            return send_from_directory(app.static_folder, 'index.html')
    
    # API routes
    @app.route('/api/health')
    def health_check():
        logger.debug("Health check requested")
        return jsonify({'status': 'ok'})
    
    # Subscription endpoints
    @app.route('/api/subscription/plans')
    def get_subscription_plans():
        logger.debug("GET /api/subscription/plans hit")
        return jsonify(SUBSCRIPTION_PLANS)

    @app.route('/api/subscription/status')
    def get_subscription_status():
        print("GET /api/subscription/status hit") # Debug print
        if not session.get('user_id'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Removed duplicate portfolio related functions and routes. These are now handled by portfolio.py
        # Helper function to check subscription status
        # has_subscription, limit = check_subscription(session['user_id'])
        # subscription = Subscription.query.filter_by(user_id=session['user_id']).first()
        
        return jsonify({
            'has_subscription': True,
            'trading_limit': float(FREE_TIER_LIMIT),
            'subscription': None
        })

    @app.route('/api/subscription/purchase', methods=['POST'])
    def purchase_subscription():
        print("POST /api/subscription/purchase hit") # Debug print
        if not session.get('user_id'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.json
        plan_id = data.get('plan_id')
        
        if plan_id not in SUBSCRIPTION_PLANS:
            return jsonify({'error': 'Invalid plan'}), 400
        
        plan = SUBSCRIPTION_PLANS[plan_id]
        
        # Here you would integrate with a payment gateway
        # For now, we'll just create the subscription
        
        subscription = Subscription.query.filter_by(user_id=session['user_id']).first()
        if not subscription:
            subscription = Subscription(user_id=session['user_id'])
        
        subscription.plan_id = plan_id
        subscription.credit_limit = plan['credit']
        subscription.price_paid = plan['price']
        subscription.starts_at = datetime.utcnow()
        subscription.expires_at = datetime.utcnow() + timedelta(days=plan['duration_days'])
        
        db.session.add(subscription)
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription purchased successfully',
            'subscription': subscription.to_dict()
        })

    # Market data endpoints
    @app.route('/api/market/quote/<symbol>')
    def get_stock_quote(symbol):
        api_key = current_app.config.get('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            return jsonify({'error': 'Alpha Vantage API key not configured'}), 500
        
        today = date.today()
        market_open_time = time(9, 15)  # 9:15 AM IST
        market_close_time = time(15, 30) # 3:30 PM IST
        current_time = datetime.now().time()

        # Check if market is currently open
        is_market_open = market_open_time <= current_time <= market_close_time
        
        # Try to get data from cache first
        cached_price = HistoricalPrice.query.filter_by(symbol=symbol).order_by(HistoricalPrice.date.desc()).first()

        if cached_price and (cached_price.date == today or not is_market_open):
            # If data is for today or market is closed, return cached data
            return jsonify({
                'symbol': cached_price.symbol,
                'open': float(cached_price.open) if cached_price.open else None,
                'high': float(cached_price.high) if cached_price.high else None,
                'low': float(cached_price.low) if cached_price.low else None,
                'price': float(cached_price.close) if cached_price.close else None,
                'volume': int(cached_price.volume) if cached_price.volume else None,
                'latest_trading_day': cached_price.date.isoformat(),
                'previous_close': float(cached_price.close) if cached_price.close else None,
                'change': None,
                'change_percent': None
            })

        # If not in cache or outdated (and market is open), fetch from Alpha Vantage Global Quote
        if is_market_open:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
            response = requests.get(url)
            data = response.json()
            
            if "Global Quote" in data:
                quote = data["Global Quote"]
                
                # Save to historical prices
                try:
                    daily_data = HistoricalPrice(
                        symbol=quote.get('01. symbol'),
                        date=datetime.strptime(quote.get('07. latest trading day'), '%Y-%m-%d').date(),
                        open=Decimal(str(quote.get('02. open'))),
                        high=Decimal(str(quote.get('03. high'))),
                        low=Decimal(str(quote.get('04. low'))),
                        close=Decimal(str(quote.get('05. price'))),
                        volume=int(quote.get('06. volume'))
                    )
                    db.session.add(daily_data)
                    db.session.commit()
                except Exception as e:
                    logger.error(f"Failed to save historical price for {symbol}: {e}")
                    db.session.rollback()

                return jsonify({
                    'symbol': quote.get('01. symbol'),
                    'open': float(quote.get('02. open')),
                    'high': float(quote.get('03. high')),
                    'low': float(quote.get('04. low')),
                    'price': float(quote.get('05. price')),
                    'volume': int(quote.get('06. volume')),
                    'latest_trading_day': quote.get('07. latest trading day'),
                    'previous_close': float(quote.get('08. previous close')),
                    'change': float(quote.get('09. change')),
                    'change_percent': quote.get('10. change percent')
                })
        
        # If market is closed or Global Quote failed, try fetching from TIME_SERIES_DAILY_ADJUSTED
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={api_key}"
        response = requests.get(url)
        data = response.json()

        if "Time Series (Daily)" in data:
            time_series = data["Time Series (Daily)"]
            latest_date_str = sorted(time_series.keys(), reverse=True)[0]
            latest_day_data = time_series[latest_date_str]

            try:
                daily_data = HistoricalPrice.query.filter_by(symbol=symbol, date=datetime.strptime(latest_date_str, '%Y-%m-%d').date()).first()
                if not daily_data:
                    daily_data = HistoricalPrice(
                        symbol=symbol,
                        date=datetime.strptime(latest_date_str, '%Y-%m-%d').date()
                    )
                daily_data.open = Decimal(str(latest_day_data.get('1. open')))
                daily_data.high = Decimal(str(latest_day_data.get('2. high')))
                daily_data.low = Decimal(str(latest_day_data.get('3. low')))
                daily_data.close = Decimal(str(latest_day_data.get('4. close')))
                daily_data.volume = int(latest_day_data.get('6. volume'))
                db.session.add(daily_data)
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to save historical time series data for {symbol}: {e}")
                db.session.rollback()

            return jsonify({
                'symbol': symbol,
                'open': float(daily_data.open) if daily_data.open else None,
                'high': float(daily_data.high) if daily_data.high else None,
                'low': float(daily_data.low) if daily_data.low else None,
                'price': float(daily_data.close) if daily_data.close else None,
                'volume': int(daily_data.volume) if daily_data.volume else None,
                'latest_trading_day': latest_date_str,
                'previous_close': float(daily_data.close) if daily_data.close else None,
                'change': None,
                'change_percent': None
            })

        return jsonify({'error': 'Could not retrieve quote for symbol', 'data': data}), 404

    @app.errorhandler(404)
    def not_found(e):
        # If it's a request for a static file that wasn't found, return a true 404
        if request.path.startswith('/static/'):
            return 'Static file not found', 404
        # Otherwise, serve the React app's index.html for client-side routing
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    # The config_name is now determined inside create_app()
    app = create_app() # Call without argument
    logger.info("Starting Flask development server...")
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

# Gunicorn will import 'application' and use it directly.
# This ensures create_app() is called once to get the app instance.
application = create_app()

