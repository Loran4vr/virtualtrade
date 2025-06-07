from flask import Blueprint, redirect, url_for, session, jsonify, current_app
from flask_dance.contrib.google import make_google_blueprint, google
import os
import json

auth_bp = Blueprint('auth', __name__)

def init_google_oauth(app):
    """Initialize Google OAuth with Flask-Dance"""
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
        authorized_url="/google/authorized"  # This ensures consistent redirect URI
    )
    app.register_blueprint(google_bp, url_prefix="/login")

@auth_bp.route('/login')
def login():
    """Redirect to Google OAuth login"""
    if not google.authorized:
        return redirect(url_for("google.login"))
    return redirect(url_for("auth.callback"))

@auth_bp.route('/callback')
def callback():
    """Handle the OAuth callback"""
    if not google.authorized:
        return redirect(url_for("google.login"))
    
    # Get user info from Google
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "Failed to fetch user info from Google", 400
    
    user_info = resp.json()
    
    # Store user info in session
    session['user'] = {
        'id': user_info.get('id'),
        'email': user_info.get('email'),
        'name': user_info.get('name'),
        'picture': user_info.get('picture')
    }
    
    # Redirect to the frontend dashboard
    return redirect(url_for('static', filename='index.html'))

@auth_bp.route('/logout')
def logout():
    """Log out the user"""
    session.pop('user', None)
    return redirect(url_for('static', filename='index.html'))

@auth_bp.route('/user')
def get_user():
    """Get the current user info"""
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    
    return jsonify({
        'authenticated': True,
        'user': session['user']
    })

