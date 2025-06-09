# -*- coding: utf-8 -*-
import os
import logging
from flask import Blueprint, redirect, url_for, session, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import make_google_blueprint
from models import User, db

print("##### DEBUG: auth.py file has been loaded and executed! #####")

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
    
    # Register the Google blueprint with a unique name
    app.register_blueprint(google_bp, url_prefix='/auth/google', name='google_oauth')
    
    @auth_bp.route('/login')
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
        return redirect(url_for('google_oauth.login'))
    
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
    
    return auth_bp

