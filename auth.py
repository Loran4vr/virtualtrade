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
    
    # Create and register the Google blueprint
    google_bp = make_google_blueprint(
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        scope=["profile", "email"],
        redirect_to="auth.callback",
        authorized_url="/login/google/authorized",  # Updated to match frontend route
        redirect_url="/login/google/authorized"  # Updated to match frontend route
    )
    app.register_blueprint(google_bp, url_prefix="/login")
    logger.debug("Google OAuth blueprint registered")

@auth_bp.route('/login')
def login():
    """Redirect to Google OAuth login"""
    logger.debug("Login route accessed")
    if not google.authorized:
        logger.debug("User not authorized, redirecting to Google login")
        return redirect(url_for("google.login"))
    logger.debug("User already authorized, redirecting to callback")
    return redirect(url_for("auth.callback"))

@auth_bp.route('/callback')
def callback():
    """Handle the OAuth callback"""
    logger.debug("Callback route accessed")
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
    
    # Store user info in session
    session['user'] = {
        'id': user_info.get('id'),
        'email': user_info.get('email'),
        'name': user_info.get('name'),
        'picture': user_info.get('picture')
    }
    logger.debug("User info stored in session")
    
    # Redirect to the frontend root for React Router
    return redirect('/')

@auth_bp.route('/logout')
def logout():
    """Log out the user"""
    logger.debug("Logout route accessed")
    session.pop('user', None)
    return redirect(url_for('static', filename='index.html'))

@auth_bp.route('/user')
def get_user():
    """Get the current user info"""
    logger.debug("User info route accessed")
    if 'user' not in session:
        logger.debug("No user in session")
        return jsonify({'authenticated': False}), 401
    
    logger.debug(f"User found in session: {session['user'].get('email')}")
    return jsonify({
        'authenticated': True,
        'user': session['user']
    })

