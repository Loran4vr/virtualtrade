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
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.storage.session import SessionStorage
from sqlalchemy.orm.exc import NoResultFound
import logging
from backend.subscription import init_stripe, SUBSCRIPTION_PLANS
from whitenoise import WhiteNoise
import requests
from flask_cors import CORS
from flask_login import LoginManager
import gc

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
    try:
        logger.info("Starting application initialization...")
        
        # NEW DEBUG: Print all environment variables at the start of create_app
        logger.debug("Environment variables:")
        for key, value in os.environ.items():
            logger.debug(f"  {key}={value}")

        app = Flask(__name__, static_folder='static')
        CORS(app)
        
        # Determine config_name based on environment variable directly inside create_app
        config_name = os.getenv('FLASK_ENV', 'development')
        logger.info(f"Loading Flask configuration: {config_name}")
        
        # Use WhiteNoise to serve static files
        app.wsgi_app = WhiteNoise(app.wsgi_app, root=os.path.join(app.root_path, 'static'))
        app.wsgi_app.add_files(os.path.join(app.root_path, 'static'), prefix='/')

        logger.debug(f"Static folder: {os.path.join(app.root_path, 'static')}")
        
        # Load configuration
        app.config.from_object(config[config_name])
        
        # Explicit session configuration
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'None'
        app.config['SESSION_COOKIE_DOMAIN'] = None
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
        
        logger.debug(f"Cookie settings: Secure={app.config.get('SESSION_COOKIE_SECURE')}, HttpOnly={app.config.get('SESSION_COOKIE_HTTPONLY')}, SameSite={app.config.get('SESSION_COOKIE_SAMESITE')}")
        
        # Ensure SQLALCHEMY_DATABASE_URI is set
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        logger.debug(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

        # Initialize database
        logger.info("Initializing database...")
        db.init_app(app)
        with app.app_context():
            try:
                db.create_all()
                logger.info("Database tables created successfully")
            except Exception as e:
                logger.error(f"Error creating database tables: {str(e)}", exc_info=True)
                raise

        # Initialize Flask-Login
        logger.info("Initializing Flask-Login...")
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        # Debug print SECRET_KEY status
        secret_key = app.config.get('SECRET_KEY')
        if secret_key:
            logger.debug(f"SECRET_KEY loaded. Length: {len(secret_key)}. Masked: {secret_key[:5]}...{secret_key[-5:]}")
        else:
            logger.warning("SECRET_KEY not loaded or is None.")

        # Initialize Google OAuth
        logger.info("Initializing Google OAuth...")
        if app.config.get('DEBUG'):
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
        
        # Create the Google blueprint
        google_bp = make_google_blueprint(
            client_id=app.config.get('GOOGLE_CLIENT_ID'),
            client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
            scope=["profile", "email"],
            redirect_to="index",
            authorized_url="/auth/google/authorized",
            storage=SessionStorage()
        )
        app.register_blueprint(google_bp, url_prefix='/auth/google', name='google_oauth')
        logger.info("Google OAuth blueprint registered")

        # Initialize Stripe
        logger.info("Initializing Stripe...")
        init_stripe(app)

        # Register blueprints
        logger.info("Registering blueprints...")
        app.register_blueprint(create_auth_blueprint(app), url_prefix='/auth')
        app.register_blueprint(market_data_bp, url_prefix='/api/market')
        app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')

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
                logger.error(f"Error serving path {path}: {str(e)}", exc_info=True)
                return jsonify({'error': 'Internal server error'}), 500

        # Add health check endpoint
        @app.route('/api/health')
        def health_check():
            try:
                # Test database connection
                db.session.execute('SELECT 1')
                return jsonify({
                    'status': 'ok',
                    'database': 'connected',
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }), 500

        # Clean up memory
        gc.collect()
        
        logger.info("Application initialization completed successfully")
        return app

    except Exception as e:
        logger.error(f"Error creating Flask app: {str(e)}", exc_info=True)
        raise

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# Gunicorn will import 'application' and use it directly.
# This ensures create_app() is called once to get the app instance.
application = create_app()

