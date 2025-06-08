from flask import Blueprint, redirect, url_for, session, jsonify, current_app, request
from flask_dance.contrib.google import make_google_blueprint, google
import os
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def init_google_oauth(app):
    """Initialize Google OAuth with Flask-Dance"""
    logger.debug("Initializing Google OAuth")
    # Set environment variables for development
    if app.config.get('DEBUG'):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    
    # Create the Google blueprint
    google_bp = make_google_blueprint(
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        scope=["profile", "email"],
        redirect_to="auth.google_callback", # Changed to a specific name within auth_bp
        authorized_url="/auth/google/authorized", # Changed to match auth_bp prefix
        redirect_url="/auth/google/authorized"  # Changed to match auth_bp prefix
    )
    # Register the google_bp with auth_bp
    auth_bp.register_blueprint(google_bp, url_prefix="/google")
    logger.debug("Google OAuth blueprint registered with auth_bp")

@auth_bp.route('/login')
def login():
    """Redirect to Google OAuth login"""
    logger.debug("Login route accessed")
    if not google.authorized:
        logger.debug("User not authorized, redirecting to Google login")
        return redirect(url_for("google.login"))
    logger.debug("User already authorized, redirecting to frontend root")
    return redirect('/')

@auth_bp.route('/google/authorized') # This will be the actual callback URL within auth_bp
def google_callback():
    """Handle the OAuth callback"""
    logger.debug("Google callback route accessed")
    logger.debug(f"Request URL: {request.url}")
    logger.debug(f"Request args: {request.args}")
    
    if not google.authorized:
        logger.debug("User not authorized in callback, redirecting to Google login")
        return redirect(url_for("google.login"))
    
    # Get user info from Google
    logger.debug("Fetching user info from Google")
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        logger.error(f"Failed to fetch user info: {resp.status_code}")
        return "Failed to fetch user info from Google", 400
    
    user_info = resp.json()
    logger.debug(f"User info received: {user_info.get('email')}")
    
    # Store user info in session (main.py will handle user creation/update)
    session['user_id'] = user_info.get('id') # Store Google ID temporarily
    session['google_info'] = user_info # Store full info for main.py

    # Redirect to the frontend root for React Router
    return redirect('/')

@auth_bp.route('/logout')
def logout():
    """Log out the user"""
    logger.debug("Logout route accessed")
    session.pop('user_id', None)
    session.pop('google_info', None)
    return redirect('/') # Redirect to frontend root

@auth_bp.route('/user')
def get_user():
    """Get the current user info"""
    logger.debug("User info route accessed")
    if 'user_id' not in session:
        logger.debug("No user_id in session")
        return jsonify({'authenticated': False}), 401
    
    # Fetch user from DB using user_id from session
    from backend.models import User # Import here to avoid circular dependency
    user = User.query.get(session['user_id'])
    if not user:
        logger.debug(f"User with ID {session['user_id']} not found in DB")
        return jsonify({'authenticated': False}), 401

    logger.debug(f"User found in session: {user.email}")
    # The main.py will handle fetching subscription and trading limit
    return jsonify({
        'authenticated': True,
        'user': user.to_dict()
    })

