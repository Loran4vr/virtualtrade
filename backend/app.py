from flask import Flask, request, jsonify, session, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from models import db, User, Portfolio, Transaction, Subscription
import json
from decimal import Decimal
import requests
from functools import wraps

load_dotenv()

app = Flask(__name__, static_folder='/app/static', static_url_path='/')
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///virtualtrade.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

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

# Google OAuth setup
google_bp = make_google_blueprint(
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    scope=['profile', 'email']
)
app.register_blueprint(google_bp, url_prefix='/auth')

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
        
        has_subscription, limit = check_subscription(session['user_id'])
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.errorhandler(404)
def not_found(e):
    # For any route not found by Flask, serve the React app's index.html
    # This allows client-side routing to take over
    return app.send_static_file('index.html')

@app.route('/auth/login')
def login():
    if not google.authorized:
        return redirect(url_for('google.login'))
    return redirect('/')

@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        return False

    resp = google.get('/oauth2/v2/userinfo')
    if not resp.ok:
        return False

    google_info = resp.json()
    google_user_id = google_info['id']

    # Find or create user
    user = User.query.filter_by(google_id=google_user_id).first()
    if not user:
        user = User(
            google_id=google_user_id,
            email=google_info['email'],
            name=google_info['name'],
            picture=google_info.get('picture')
        )
        db.session.add(user)
        db.session.commit()

    # Create session
    session['user_id'] = user.id
    return False

@app.route('/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/auth/user')
def get_user():
    if not session.get('user_id'):
        return jsonify({'authenticated': False})
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'authenticated': False})
    
    has_subscription, limit = check_subscription(user.id)
    
    return jsonify({
        'authenticated': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'picture': user.picture,
            'has_subscription': has_subscription,
            'trading_limit': limit
        }
    })

# Subscription endpoints
@app.route('/api/subscription/plans')
def get_subscription_plans():
    print("GET /api/subscription/plans hit")
    return jsonify(SUBSCRIPTION_PLANS)

@app.route('/api/subscription/status')
def get_subscription_status():
    print("GET /api/subscription/status hit")
    if not session.get('user_id'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    has_subscription, limit = check_subscription(session['user_id'])
    subscription = Subscription.query.filter_by(user_id=session['user_id']).first()
    
    return jsonify({
        'has_subscription': has_subscription,
        'trading_limit': limit,
        'subscription': subscription.to_dict() if subscription else None
    })

@app.route('/api/subscription/purchase', methods=['POST'])
def purchase_subscription():
    print("POST /api/subscription/purchase hit")
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

# Update portfolio endpoints to check trading limits
@app.route('/api/portfolio/buy', methods=['POST'])
@trading_limit_required
def buy_stock():
    if not session.get('user_id'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    symbol = data.get('symbol')
    quantity = int(data.get('quantity', 0))
    price = Decimal(str(data.get('price', 0)))
    
    # Check trading limit
    can_trade, error = check_trading_limit(session['user_id'], quantity * price)
    if not can_trade:
        return jsonify({'error': error}), 400
    
    portfolio = Portfolio.query.filter_by(user_id=session['user_id']).first()
    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404
    
    total_cost = quantity * price
    if portfolio.cash_balance < total_cost:
        return jsonify({'error': 'Insufficient funds'}), 400
    
    # Update portfolio
    portfolio.cash_balance -= total_cost
    
    # Update or create holding
    holding = next((h for h in portfolio.holdings if h.symbol == symbol), None)
    if holding:
        total_quantity = holding.quantity + quantity
        total_cost = (holding.quantity * holding.avg_price) + total_cost
        holding.avg_price = total_cost / total_quantity
        holding.quantity = total_quantity
    else:
        holding = Holding(
            symbol=symbol,
            quantity=quantity,
            avg_price=price
        )
        portfolio.holdings.append(holding)
    
    # Create transaction record
    transaction = Transaction(
        user_id=session['user_id'],
        symbol=symbol,
        quantity=quantity,
        price=price,
        type='buy'
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({
        'message': 'Stock purchased successfully',
        'portfolio': portfolio.to_dict()
    })

# ... rest of your existing code ...

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 