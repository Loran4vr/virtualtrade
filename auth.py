# -*- coding: utf-8 -*-
from flask import Blueprint, redirect, url_for, session, jsonify, current_app, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import make_google_blueprint
import os
import json
import logging
from flask_dance.consumer import OAuth
from models import User, db

print("##### DEBUG: auth.py file has been loaded and executed! #####")

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_auth_blueprint(app):
    # Get the base URL from environment variable or default to localhost
    base_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost')
    
    auth_bp = Blueprint('auth', __name__)
    
    # Create Google OAuth blueprint
    google_bp = make_google_blueprint(
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        scope=['openid', 'email', 'profile'],
        redirect_url=f"{base_url}/auth/google/authorized"
    )
    
    app.register_blueprint(google_bp, url_prefix='/auth/google')
    
    @auth_bp.route('/login')
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
        return redirect(url_for('google.login'))
    
    @auth_bp.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('main.index'))
    
    @auth_bp.route('/auth/google/authorized')
    def google_authorized():
        if not google_bp.session.authorized:
            flash('Access denied: reason={} error={}'.format(
                request.args['error_reason'],
                request.args['error_description']
            ))
            return redirect(url_for('main.index'))
        
        resp = google_bp.session.get('/oauth2/v2/userinfo')
        if not resp.ok:
            flash('Failed to fetch user info from Google')
            return redirect(url_for('main.index'))
        
        google_info = resp.json()
        google_id = google_info['id']
        
        # Find or create user
        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            user = User(
                google_id=google_id,
                email=google_info['email'],
                name=google_info.get('name', ''),
                picture=google_info.get('picture', '')
            )
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        return redirect(url_for('main.index'))
    
    @auth_bp.route('/user')
    def get_user():
        """Get the current user info"""
        logger.debug("User info route accessed")
        if 'user_id' not in session:
            logger.debug(f"get_user: session['user_id'] is {session.get('user_id')}. No user_id in session.")
            return jsonify({'authenticated': False}), 401
        
        # Fetch user from DB using user_id from session
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

    return auth_bp

def init_oauth(app):
    oauth = OAuth(app)
    
    # Get the base URL from environment variable or default to localhost
    base_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost')
    
    google = oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        client_kwargs={'scope': 'openid email profile'},
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        redirect_uri=f"{base_url}/auth/google/authorized"
    )
    
    return google

