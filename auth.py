# -*- coding: utf-8 -*-
import os
import logging
from flask import Blueprint, redirect, url_for, session, request, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import make_google_blueprint, google
from models import User, db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("##### DEBUG: auth.py file has been loaded and executed! #####")

def create_auth_blueprint(app):
    # Get the base URL from environment variable or default to localhost
    is_production = os.environ.get('FLASK_ENV') == 'production'
    if is_production:
        base_url = 'https://virtualtrade.onrender.com'
    else:
        base_url = 'http://localhost:5000'
    
    logger.debug(f"Environment: {'Production' if is_production else 'Development'}")
    logger.debug(f"Using base URL: {base_url}")
    
    auth_bp = Blueprint('auth', __name__)
    
    # Create Google OAuth blueprint
    google_bp = make_google_blueprint(
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        scope=['profile', 'email'],
        redirect_url='/auth/google/google/authorized'
    )
    
    # Register the Google blueprint with a unique name
    app.register_blueprint(google_bp, url_prefix='/auth/google')
    logger.debug("Google OAuth blueprint registered")
    
    @auth_bp.route('/login')
    def login():
        logger.debug("Login route accessed")
        if current_user.is_authenticated:
            logger.debug(f"User already authenticated: {current_user.email}")
            return redirect(url_for('main.index'))
        logger.debug("Redirecting to Google OAuth login")
        return redirect(url_for('google.login'))
    
    @auth_bp.route('/logout')
    @login_required
    def logout():
        logger.debug(f"Logout requested for user: {current_user.email}")
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
    
    @google_bp.route('/authorized')
    def authorized():
        """Handle Google OAuth callback."""
        if not google.authorized:
            return redirect(url_for('auth.login'))
        
        resp = google.get('/oauth2/v2/userinfo')
        if not resp.ok:
            return redirect(url_for('auth.login'))
        
        google_info = resp.json()
        google_user_id = str(google_info['id'])
        
        # Get or create user
        user = User.query.filter_by(google_id=google_user_id).first()
        if not user:
            logger.debug(f"Creating new user for Google ID: {google_user_id}")
            user = User(
                google_id=google_user_id,
                email=google_info['email'],
                name=google_info.get('name', ''),
                picture=google_info.get('picture', '')
            )
            db.session.add(user)
            db.session.commit()
            logger.debug(f"Created new user: {user.email}")
        else:
            logger.debug(f"Found existing user: {user.email}")
        
        login_user(user)
        logger.debug(f"User logged in successfully: {user.email}")
        return redirect(url_for('main.index'))
    
    return auth_bp

