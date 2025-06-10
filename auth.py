# -*- coding: utf-8 -*-
import os
import logging
from flask import Blueprint, redirect, url_for, session, request, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("##### DEBUG: auth.py file has been loaded and executed! #####")

def create_auth_blueprint(app):
    """Create and configure the authentication blueprint."""
    # Log environment
    env = app.config.get('FLASK_ENV', 'production')
    logger.debug(f"Environment: {env}")
    
    # Get base URL from environment
    base_url = app.config.get('RENDER_EXTERNAL_URL', 'http://localhost:5000')
    logger.debug(f"Using base URL: {base_url}")
    
    # Create auth blueprint
    auth_bp = Blueprint('auth', __name__)
    
    @auth_bp.route('/login')
    def login():
        """Redirect to Google OAuth login."""
        logger.debug("Login route accessed")
        logger.debug("Redirecting to Google OAuth login")
        # Now, we redirect to the Google OAuth login route defined in main.py's google_bp
        return redirect(url_for('google.login'))
    
    @auth_bp.route('/logout')
    @login_required
    def logout():
        """Log out the current user."""
        logout_user()
        return redirect(url_for('auth.login'))
    
    @auth_bp.route('/user')
    def get_user():
        """Get current user information."""
        if current_user.is_authenticated:
            return jsonify({
                'id': current_user.id,
                'email': current_user.email,
                'name': current_user.name,
                'is_authenticated': True
            })
        return jsonify({
            'is_authenticated': False
        })
    
    return auth_bp

