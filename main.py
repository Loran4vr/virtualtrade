from flask import Flask, render_template, jsonify, session, redirect, url_for, request, make_response, send_from_directory
import os
from dotenv import load_dotenv
from auth import create_auth_blueprint
from market_data import market_data_bp
from portfolio import portfolio_bp
from config import config
from models import db, User  # Import db from models.py
from datetime import datetime, timedelta, time, date
from decimal import Decimal
from functools import wraps
from flask_login import LoginManager
import logging
from backend.subscription import init_stripe, SUBSCRIPTION_PLANS
from whitenoise import WhiteNoise
import requests
from flask_cors import CORS
import gc
import stripe
from flask_dance.contrib.google import make_google_blueprint, google # Import make_google_blueprint and google

print("##### DEBUG: main.py file has been loaded and executed! #####")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Free tier limit
FREE_TIER_LIMIT = 1000000  # 10 lakhs

def create_app():
    """Create and configure the Flask application."""
    print("##### DEBUG: main.py file has been loaded and executed! #####")
    
    # Initialize logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting application initialization...")
    
    # Log environment variables
    logger.debug("Environment variables:")
    for key, value in os.environ.items():
        logger.debug(f"  {key}={value}")
    
    # Create Flask app
    app = Flask(__name__, static_folder='static', static_url_path='')
    
    # Set preferred URL scheme to HTTPS for Render deployments
    app.config['PREFERRED_URL_SCHEME'] = 'https'

    # Load configuration
    env = os.environ.get('FLASK_ENV', 'production')
    logger.info(f"Loading Flask configuration: {env}")
    
    if env == 'development':
        app.config.from_object('config.DevelopmentConfig')
    else:
        app.config.from_object('config.ProductionConfig')
    
    # Configure static files
    logger.debug(f"Static folder: {app.static_folder}")
    
    # Configure session cookie
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    logger.debug(f"Cookie settings: Secure={app.config['SESSION_COOKIE_SECURE']}, HttpOnly={app.config['SESSION_COOKIE_HTTPONLY']}, SameSite={app.config['SESSION_COOKIE_SAMESITE']}")
    
    # Initialize database
    logger.debug(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    db.init_app(app)
    
    # Create database tables if they don't exist
    logger.info("Initializing database...")
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.warning(f"Database tables may already exist: {str(e)}")
            # Continue execution even if tables exist
    
    # Initialize Flask-Login
    logger.info("Initializing Flask-Login...")
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Load user function
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Verify SECRET_KEY
    if not app.config['SECRET_KEY']:
        logger.error("SECRET_KEY is not set!")
        raise ValueError("SECRET_KEY must be set")
    logger.debug(f"SECRET_KEY loaded. Length: {len(app.config['SECRET_KEY'])}. Masked: {app.config['SECRET_KEY'][:5]}...{app.config['SECRET_KEY'][-5:]}")

    # Determine the external URL for Flask-Dance's base_url parameter
    external_base_url = app.config.get('RENDER_EXTERNAL_URL', 'http://localhost:5000')
    logger.debug(f"Flask-Dance base_url set to: {external_base_url}")

    # Create Google OAuth blueprint directly in main.py (standard Flask-Dance pattern)
    google_bp = make_google_blueprint(
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        scope=['profile', 'email'],
        redirect_url='/authorized'  # Relative to the blueprint's mount point
    )

    # Register Google blueprint with the app (setting its URL prefix)
    app.register_blueprint(google_bp, url_prefix='/auth/google')
    logger.info("Google OAuth blueprint registered")

    # Register the main auth blueprint
    logger.info("Registering authentication blueprint...")
    app.register_blueprint(create_auth_blueprint(app), url_prefix='/auth')
    logger.info("Auth blueprint registered")
    
    # Handle Google OAuth callback directly in main.py
    @google_bp.route('/authorized')
    def authorized():
        if not google.authorized:
            return redirect(url_for('auth.login'))
        
        resp = google.get('/oauth2/v2/userinfo')
        if not resp.ok:
            return redirect(url_for('auth.login'))
        
        google_info = resp.json()
        google_user_id = str(google_info['id'])
        
        user = User.query.filter_by(google_id=google_user_id).first()
        if not user:
            user = User(
                google_id=google_user_id,
                email=google_info['email'],
                name=google_info.get('name', '')
            )
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        return redirect('/')

    # Initialize Stripe (only if keys are available)
    logger.info("Initializing Stripe...")
    if app.config.get('STRIPE_SECRET_KEY'):
        stripe.api_key = app.config['STRIPE_SECRET_KEY']
        logger.info("Stripe initialized successfully")
    else:
        logger.warning("Stripe secret key not found, payment features will be disabled")
    
    # Register other blueprints
    logger.info("Registering other blueprints...")
    try:
        app.register_blueprint(market_data_bp, url_prefix='/api/market')
        logger.info("Market data blueprint registered")
    except Exception as e:
        logger.error(f"Error registering market data blueprint: {str(e)}")
        raise
    
    # Add error handlers
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(404)
    def not_found_error(error):
        logger.error(f"Not found error: {str(error)}", exc_info=True)
        return jsonify({'error': 'Not found'}), 404

    # Add catch-all route for React Router
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        try:
            if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
                return send_from_directory(app.static_folder, path)
            else:
                return send_from_directory(app.static_folder, 'index.html')
        except Exception as e:
            logger.error(f"Error serving static file: {str(e)}", exc_info=True)
            return jsonify({'error': 'Error serving static file'}), 500
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# Gunicorn will import 'application' and use it directly.
# This ensures create_app() is called once to get the app instance.
application = create_app()

