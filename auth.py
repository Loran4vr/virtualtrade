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
        redirect_to="/" # Redirect to the root after successful OAuth
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
        return redirect(url_for("auth.google.login"))
    logger.debug("User already authorized, redirecting to frontend root")
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

