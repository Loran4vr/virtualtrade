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
    # NEW DEBUG: Print all environment variables at the start of create_app
    print("DEBUG: create_app: os.environ content:")
    for key, value in os.environ.items():
        print(f"  {key}={value}")
    print("DEBUG: create_app: End of os.environ content")

    app = Flask(__name__, static_folder='static')
    CORS(app)
    
    # Determine config_name based on environment variable directly inside create_app
    config_name = os.getenv('FLASK_ENV', 'development')
    print(f"DEBUG: create_app: Loading Flask configuration: {config_name}")
    
    # Use WhiteNoise to serve static files
    app.wsgi_app = WhiteNoise(app.wsgi_app, root=os.path.join(app.root_path, 'static'))
    app.wsgi_app.add_files(os.path.join(app.root_path, 'static'), prefix='/')

    print(f"Flask static_folder: {os.path.join(app.root_path, 'static')}")
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Explicit session configuration
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Debug print actual cookie settings from app.config
    print(f"DEBUG: Flask app.config cookie settings: Secure={app.config.get('SESSION_COOKIE_SECURE')}, HttpOnly={app.config.get('SESSION_COOKIE_HTTPONLY')}, SameSite={app.config.get('SESSION_COOKIE_SAMESITE')}")
    
    # Ensure SQLALCHEMY_DATABASE_URI is set
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    print(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Initialize database
    db.init_app(app)

    # Initialize Flask-Login
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
        logger.debug("SECRET_KEY not loaded or is None.")

    # Debug print cookie settings
    logger.debug(f"Cookie settings: Secure={app.config.get('SESSION_COOKIE_SECURE')}, HttpOnly={app.config.get('SESSION_COOKIE_HTTPONLY')}, SameSite={app.config.get('SESSION_COOKIE_SAMESITE')}")

    # Initialize Google OAuth
    if app.config.get('DEBUG'):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    
    # Create the Google blueprint
    google_bp = make_google_blueprint(
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        scope=["profile", "email"],
        redirect_to="index",
        authorized_url="/auth/google/authorized",  # This is the path relative to the blueprint
        storage=SessionStorage()
    )
    app.register_blueprint(google_bp, url_prefix='/auth/google', name='google_oauth')
    logger.debug("Google OAuth blueprint registered directly with app")

    # NEW DEBUG: Check Flask's perception of Google OAuth URLs
    with app.test_request_context():
        try:
            login_url = url_for("google_oauth.login", _external=True)
            logger.debug(f"DEBUG: Calculated google.login URL: {login_url}")
        except Exception as e:
            logger.debug(f"DEBUG: Error calculating google.login URL: {e}")

        try:
            authorized_url = url_for("google_oauth.authorized", _external=True)
            logger.debug(f"DEBUG: Calculated google.authorized URL: {authorized_url}")
        except Exception as e:
            logger.debug(f"DEBUG: Error calculating google.authorized URL: {e}")

    # Initialize Stripe
    init_stripe(app)

    # Handle Google OAuth callback for user creation/login
    @oauth_authorized.connect_via(google_bp)
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
        session.clear()
        session['user_id'] = user.id
        session.permanent = True
        session.modified = True
        
        # Store OAuth state in session
        session['oauth_state'] = request.args.get('state')
        logger.debug(f"DEBUG:main:google_logged_in: Stored OAuth state in session: {session.get('oauth_state')}")
        print(f"DEBUG:main:google_logged_in: Session user_id set to: {session.get('user_id')}")
        print(f"DEBUG:main:google_logged_in: Session is permanent: {session.permanent}")
        print(f"DEBUG:main:google_logged_in: Session type: {type(session)}")

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
        return jsonify({'status': 'ok'}), 200

    # Register blueprints
    app.register_blueprint(create_auth_blueprint(app), url_prefix='/auth')
    app.register_blueprint(market_data_bp, url_prefix='/api/market')
    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
    
    return app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app = create_app() # Call without argument
    logger.info("Starting Flask development server...")
    app.run(host='0.0.0.0', port=port)

# Gunicorn will import 'application' and use it directly.
# This ensures create_app() is called once to get the app instance.
application = create_app()

