# -*- coding: utf-8 -*-
import os
import logging
from flask import Blueprint, redirect, url_for, session, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import make_google_blueprint
from models import User, db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("##### DEBUG: auth.py file has been loaded and executed! #####")

def create_auth_blueprint(app):
    # Get the base URL from environment variable or default to localhost
    base_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost')
    logger.debug(f"Using base URL: {base_url}")
    
    auth_bp = Blueprint('auth', __name__)
    
    # Create Google OAuth blueprint
    google_bp = make_google_blueprint(
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        scope=['openid', 'email', 'profile'],
        redirect_url=f"{base_url}/auth/google/authorized"
    )
    
    # Register the Google blueprint with a unique name
    app.register_blueprint(google_bp, url_prefix='/auth/google', name='google_oauth')
    logger.debug("Google OAuth blueprint registered")
    
    @auth_bp.route('/login')
    def login():
        logger.debug("Login route accessed")
        if current_user.is_authenticated:
            logger.debug(f"User already authenticated: {current_user.email}")
            return redirect(url_for('main.index'))
        logger.debug("Redirecting to Google OAuth login")
        return redirect(url_for('google_oauth.login'))
    
    @auth_bp.route('/logout')
    @login_required
    def logout():
        logger.debug(f"Logout requested for user: {current_user.email}")
        logout_user()
        return redirect(url_for('main.index'))
    
    @auth_bp.route('/auth/google/authorized')
    def google_authorized():
        logger.debug("Google OAuth callback received")
        if not google_bp.session.authorized:
            error_reason = request.args.get('error_reason', 'unknown')
            error_description = request.args.get('error_description', 'unknown')
            logger.error(f"OAuth authorization failed: {error_reason} - {error_description}")
            flash('Access denied: reason={} error={}'.format(
                error_reason,
                error_description
            ))
            return redirect(url_for('main.index'))
        
        try:
            resp = google_bp.session.get('/oauth2/v2/userinfo')
            if not resp.ok:
                logger.error(f"Failed to fetch user info: {resp.status_code} - {resp.text}")
                flash('Failed to fetch user info from Google')
                return redirect(url_for('main.index'))
            
            google_info = resp.json()
            google_id = google_info['id']
            logger.debug(f"Received user info from Google: {google_info.get('email')}")
            
            # Find or create user
            user = User.query.filter_by(google_id=google_id).first()
            if not user:
                logger.debug(f"Creating new user for Google ID: {google_id}")
                user = User(
                    google_id=google_id,
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
            
        except Exception as e:
            logger.error(f"Error during Google OAuth callback: {str(e)}", exc_info=True)
            flash('An error occurred during login')
            return redirect(url_for('main.index'))
    
    return auth_bp

