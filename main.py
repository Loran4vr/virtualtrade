from flask import Flask, render_template, send_from_directory, jsonify, session, redirect, url_for, request
import os
from dotenv import load_dotenv
from auth import auth_bp, init_google_oauth
from market_data import market_data_bp
from portfolio import portfolio_bp
from config import config
from backend.models import db, User, Portfolio, Transaction, Subscription # Corrected import path
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps

# Load environment variables
load_dotenv()

# Subscription plans
SUBSCRIPTION_PLANS = {
    'basic': {
        'name': 'Basic',
        'price': 100,
        'credit': 100000,  # 1 lakh
        'duration_days': 30
    },
    'standard': {
        'name': 'Standard',
        'price': 250,
        'credit': 250000,  # 2.5 lakhs
        'duration_days': 30
    },
    'premium': {
        'name': 'Premium',
        'price': 475,
        'credit': 500000,  # 5 lakhs
        'duration_days': 30
    },
    'ultimate': {
        'name': 'Ultimate',
        'price': 925,
        'credit': 1000000,  # 10 lakhs
        'duration_days': 30
    }
}

# Free tier limit
FREE_TIER_LIMIT = 1000000  # 10 lakhs

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='static', static_url_path='')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize database
    db.init_app(app)

    # Initialize Google OAuth
    init_google_oauth(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(market_data_bp, url_prefix='/api/market')
    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')

    # Helper function to check subscription status
    def check_subscription(user_id):
        subscription = Subscription.query.filter_by(user_id=user_id).first()
        if not subscription:
            return False, FREE_TIER_LIMIT
        
        if subscription.expires_at < datetime.utcnow():
            return False, FREE_TIER_LIMIT
        
        return True, subscription.credit_limit

    # Helper function to check trading limits
    def check_trading_limit(user_id, amount):
        has_subscription, limit = check_subscription(user_id)
        portfolio = Portfolio.query.filter_by(user_id=user_id).first()
        
        if not portfolio:
            return False, "Portfolio not found"
        
        total_value = portfolio.cash_balance
        # Loop through holdings if they exist
        if portfolio.holdings: 
            for holding in portfolio.holdings:
                total_value += holding.quantity * holding.avg_price
        
        if total_value + amount > limit:
            return False, f"Trading limit exceeded. Current limit: ₹{limit:,}"
        
        return True, None

    # Decorator to check trading limits
    def trading_limit_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user_id'):
                return jsonify({'error': 'Not authenticated'}), 401
            return f(*args, **kwargs)
        return decorated_function
    
    # Catch-all route for React Router (only for non-static, non-api, non-auth)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def index(path):
        if path.startswith('api/') or path.startswith('auth/'):
            return 'Not Found', 404
        return send_from_directory(app.static_folder, 'index.html')
    
    # API routes
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'ok'})
    
    # Subscription endpoints
    @app.route('/api/subscription/plans')
    def get_subscription_plans():
        print("GET /api/subscription/plans hit") # Debug print
        return jsonify(SUBSCRIPTION_PLANS)

    @app.route('/api/subscription/status')
    def get_subscription_status():
        print("GET /api/subscription/status hit") # Debug print
        if not session.get('user_id'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        has_subscription, limit = check_subscription(session['user_id'])
        subscription = Subscription.query.filter_by(user_id=session['user_id']).first()
        
        return jsonify({
            'has_subscription': has_subscription,
            'trading_limit': float(limit),
            'subscription': subscription.to_dict() if subscription else None
        })

    @app.route('/api/subscription/purchase', methods=['POST'])
    def purchase_subscription():
        print("POST /api/subscription/purchase hit") # Debug print
        if not session.get('user_id'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.json
        plan_id = data.get('plan_id')
        
        if plan_id not in SUBSCRIPTION_PLANS:
            return jsonify({'error': 'Invalid plan'}), 400
        
        plan = SUBSCRIPTION_PLANS[plan_id]
        
        # Here you would integrate with a payment gateway
        # For now, we'll just create the subscription
        
        subscription = Subscription.query.filter_by(user_id=session['user_id']).first()
        if not subscription:
            subscription = Subscription(user_id=session['user_id'])
        
        subscription.plan_id = plan_id
        subscription.credit_limit = plan['credit']
        subscription.price_paid = plan['price']
        subscription.starts_at = datetime.utcnow()
        subscription.expires_at = datetime.utcnow() + timedelta(days=plan['duration_days'])
        
        db.session.add(subscription)
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription purchased successfully',
            'subscription': subscription.to_dict()
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    # Use production config if FLASK_ENV is set to production
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(config_name)
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

