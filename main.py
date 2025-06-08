from flask import Flask, render_template, jsonify, session, redirect, url_for, request, make_response, send_from_directory
import os
from dotenv import load_dotenv
from auth import create_auth_blueprint
from market_data import market_data_bp
from portfolio import portfolio_bp
from config import config
from backend.models import db, User, Portfolio, Transaction, Subscription
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from sqlalchemy.orm.exc import NoResultFound # Added for oauth_authorized handler
import logging
from backend.subscription import init_stripe, SUBSCRIPTION_PLANS
from whitenoise import WhiteNoise

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

    app = Flask(__name__)
    
    # Determine config_name based on environment variable directly inside create_app
    config_name = os.getenv('FLASK_ENV', 'development')
    print(f"DEBUG: create_app: Loading Flask configuration: {config_name}") # New print/log here
    
    # Use WhiteNoise to serve static files
    app.wsgi_app = WhiteNoise(app.wsgi_app, root=os.path.join(app.root_path, 'static'))
    app.wsgi_app.add_files(os.path.join(app.root_path, 'static'), prefix='/') # Add index.html at root

    print(f"Flask static_folder: {os.path.join(app.root_path, 'static')}") # Debug print
    
    # Load configuration
    app.config.from_object(config[config_name])
    
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
        redirect_to="index" # Redirect to the root endpoint 'index' after successful OAuth
    )
    app.register_blueprint(google_bp, url_prefix='/auth/google') # Register google_bp with app directly
    logger.debug("Google OAuth blueprint registered directly with app")

    # Initialize Stripe (moved from module level)
    init_stripe(app)

    # Handle Google OAuth callback for user creation/login
    @oauth_authorized.connect_via(app) # Connect via the app instance
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
        session['user_id'] = user.id
        session.permanent = True
        logger.debug(f"google_logged_in: Session user_id set to {session.get('user_id')}. Session permanent: {session.permanent}")
        logger.debug(f"google_logged_in: User {user.email} successfully logged in, user_id: {user.id}")

        # NEW DEBUG PRINTS:
        print(f"DEBUG: google_logged_in: request.url = {request.url}")
        print(f"DEBUG: google_logged_in: request.url_root = {request.url_root}")
        print(f"DEBUG: google_logged_in: request.host = {request.host}")
        print(f"DEBUG: google_logged_in: request.is_secure = {request.is_secure}")
        print(f"DEBUG: google_logged_in: X-Forwarded-Proto = {request.headers.get('X-Forwarded-Proto')}")
        print(f"DEBUG: google_logged_in: X-Forwarded-Host = {request.headers.get('X-Forwarded-Host')}")
        print(f"DEBUG: google_logged_in: Full session after setting user_id: {dict(session)}") # Use dict(session) to ensure it's logged

        # Explicitly redirect to ensure session cookie is sent
        return redirect('/')
    
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

    # Helper function to check subscription status
    def check_subscription(user_id):
        subscription = Subscription.query.filter_by(user_id=user_id).first()
        if not subscription:
            return False, FREE_TIER_LIMIT
        
        if subscription.expires_at < datetime.utcnow():
            return False, FREE_TIER_LIMIT
        
        return True, subscription.credit_limit

    # Helper function to check trading limits
    def check_trading_limit(user_id, amount):
        has_subscription, limit = check_subscription(user_id)
        portfolio = Portfolio.query.filter_by(user_id=user_id).first()
        
        if not portfolio:
            return False, "Portfolio not found"
        
        total_value = portfolio.cash_balance
        # Loop through holdings if they exist
        if portfolio.holdings: 
            for holding in portfolio.holdings:
                total_value += holding.quantity * holding.avg_price
        
        if total_value + amount > limit:
            return False, f"Trading limit exceeded. Current limit: ₹{limit:,}"
        
        return True, None

    # Decorator to check trading limits
    def trading_limit_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user_id'):
                return jsonify({'error': 'Not authenticated'}), 401
            return f(*args, **kwargs)
        return decorated_function
    
    # Catch-all route for React Router (now handled by WhiteNoise)
    @app.route('/')
    def index():
        logger.debug(f"Handling request for path: {request.path}")
        response = make_response(send_from_directory(os.path.join(app.root_path, 'static'), 'index.html'))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
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
        
        has_subscription, limit = check_subscription(session['user_id'])
        subscription = Subscription.query.filter_by(user_id=session['user_id']).first()
        
        return jsonify({
            'has_subscription': has_subscription,
            'trading_limit': float(limit),
            'subscription': subscription.to_dict() if subscription else None
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
        
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
        response = requests.get(url)
        data = response.json()
        
        if "Global Quote" in data:
            quote = data["Global Quote"]
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
        return jsonify({'error': 'Could not retrieve quote for symbol', 'data': data}), 404

    @app.route('/api/market/search')
    def search_stock():
        query = request.args.get('q')
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400

        api_key = current_app.config.get('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            return jsonify({'error': 'Alpha Vantage API key not configured'}), 500
        
        url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={query}&apikey={api_key}"
        response = requests.get(url)
        data = response.json()

        if "bestMatches" in data:
            results = []
            for match in data["bestMatches"]:
                results.append({
                    'symbol': match.get('1. symbol'),
                    'name': match.get('2. name'),
                    'type': match.get('3. type'),
                    'region': match.get('4. region'),
                    'marketOpen': match.get('5. marketOpen'),
                    'marketClose': match.get('6. marketClose'),
                    'timezone': match.get('7. timezone'),
                    'currency': match.get('8. currency'),
                    'matchScore': float(match.get('9. matchScore'))
                })
            return jsonify(results)
        return jsonify([]), 200 # Return empty array if no matches
    
    # Portfolio endpoints
    @app.route('/api/portfolio/buy', methods=['POST'])
    @trading_limit_required
    def buy_stock():
        if not session.get('user_id'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.json
        symbol = data.get('symbol')
        quantity = int(data.get('quantity', 0))
        price = Decimal(str(data.get('price', 0)))
        
        # Check trading limit
        can_trade, error = check_trading_limit(session['user_id'], quantity * price)
        if not can_trade:
            return jsonify({'error': error}), 400
        
        portfolio = Portfolio.query.filter_by(user_id=session['user_id']).first()
        if not portfolio:
            # Create portfolio if it doesn't exist
            portfolio = Portfolio(user_id=session['user_id'], cash_balance=FREE_TIER_LIMIT)
            db.session.add(portfolio)
            db.session.commit() # Commit to get portfolio.id
            
        if portfolio.cash_balance < quantity * price:
            return jsonify({'error': 'Insufficient cash balance'}), 400
        
        holding = Holding.query.filter_by(portfolio_id=portfolio.id, symbol=symbol).first()
        if holding:
            new_quantity = holding.quantity + quantity
            new_avg_price = ((holding.quantity * holding.avg_price) + (quantity * price)) / new_quantity
            holding.quantity = new_quantity
            holding.avg_price = new_avg_price
        else:
            holding = Holding(portfolio_id=portfolio.id, symbol=symbol, quantity=quantity, avg_price=price)
            db.session.add(holding)
            
        portfolio.cash_balance -= (quantity * price)
        
        transaction = Transaction(
            user_id=session['user_id'],
            symbol=symbol,
            quantity=quantity,
            price=price,
            type='buy'
        )
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'message': 'Stock purchased successfully',
            'portfolio': portfolio.to_dict(),
            'transaction': transaction.to_dict()
        })

    @app.route('/api/portfolio/sell', methods=['POST'])
    @trading_limit_required
    def sell_stock():
        if not session.get('user_id'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.json
        symbol = data.get('symbol')
        quantity_to_sell = int(data.get('quantity', 0))
        price = Decimal(str(data.get('price', 0)))
        
        # Check trading limit (selling adds to cash, so limit check is different)
        # This check might need to be adjusted based on how selling affects total value for limit purposes
        
        portfolio = Portfolio.query.filter_by(user_id=session['user_id']).first()
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        holding = Holding.query.filter_by(portfolio_id=portfolio.id, symbol=symbol).first()
        if not holding or holding.quantity < quantity_to_sell:
            return jsonify({'error': 'Insufficient shares to sell'}), 400
            
        holding.quantity -= quantity_to_sell
        portfolio.cash_balance += (quantity_to_sell * price)
        
        if holding.quantity == 0:
            db.session.delete(holding)
            
        transaction = Transaction(
            user_id=session['user_id'],
            symbol=symbol,
            quantity=quantity_to_sell,
            price=price,
            type='sell'
        )
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'message': 'Stock sold successfully',
            'portfolio': portfolio.to_dict(),
            'transaction': transaction.to_dict()
        })

    @app.route('/api/portfolio', methods=['GET'])
    def get_portfolio():
        if not session.get('user_id'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        portfolio = Portfolio.query.filter_by(user_id=session['user_id']).first()
        if not portfolio:
            # If no portfolio, return a default empty one with free tier limit
            return jsonify({
                'id': None,
                'user_id': session['user_id'],
                'cash_balance': float(FREE_TIER_LIMIT),
                'created_at': datetime.utcnow().isoformat(),
                'holdings': []
            })
            
        return jsonify(portfolio.to_dict())

    @app.route('/api/transactions', methods=['GET'])
    def get_transactions():
        if not session.get('user_id'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.created_at.desc()).all()
        return jsonify([t.to_dict() for t in transactions])

    # Error handlers
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

