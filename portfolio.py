from flask import Blueprint, jsonify, request, session, current_app
from datetime import datetime, timedelta
from backend.models import db, User, Portfolio, Holding, Transaction, Subscription
from decimal import Decimal # Import Decimal
from functools import wraps

portfolio_bp = Blueprint('portfolio', __name__)

# Helper function to get the current user's ID from the session
def get_user_id():
    return session.get('user_id')

# Helper function to get the initial trading limit (free tier limit)
# Ensure FREE_TIER_LIMIT is defined somewhere accessible, e.g., in config or passed from main
# For now, let's define it here, assuming it's a constant.
FREE_TIER_LIMIT = 1000000.00 # 10 Lakh INR

def check_trading_limit(user_id, amount_change, is_sell=False):
    portfolio = Portfolio.query.filter_by(user_id=user_id).first()
    if not portfolio:
        # If no portfolio exists, it means the user hasn't initialized yet.
        # The trading limit check should probably happen *after* initialization.
        # For now, let's assume an uninitialized portfolio allows the first trade within free tier.
        # This might need refinement based on exact app logic.
        return True, None
    
    # Calculate current total value including cash and holdings
    current_total_value = portfolio.cash_balance
    for holding in portfolio.holdings:
        current_total_value += holding.quantity * holding.avg_price

    # Calculate the new total value after the proposed transaction
    # For a buy, amount_change is positive, so it adds to value
    # For a sell, amount_change is positive (amount received), but it should be subtracted from value if it's considered for limit
    # Assuming amount_change here is the value of the transaction (e.g., quantity * price)
    
    new_total_value = current_total_value
    if not is_sell: # Buying
        new_total_value = current_total_value + amount_change
    # If selling, the limit applies to the *total value* of holdings you can *have*, not what you can sell to free up cash.
    # So selling reducing total value is fine, unless the remaining portfolio exceeds the limit, which is unlikely
    # For simplicity, we'll only check the limit on buying/increasing portfolio value.

    # Get the user's current subscription limit
    # This part needs to be refined. If subscription logic is in main.py, it needs to be passed or re-implemented here.
    # For now, use the free tier limit.
    limit = FREE_TIER_LIMIT # This should come from user's subscription or default
    
    subscription = Subscription.query.filter_by(user_id=user_id).first()
    if subscription and subscription.expires_at > datetime.utcnow():
        limit = float(subscription.credit_limit)

    if new_total_value > limit:
        return False, f"Trading limit exceeded. Current limit: ₹{limit:,.2f}"
    
    return True, None

# Decorator to check trading limits and ensure user is authenticated
def trading_limit_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


@portfolio_bp.route('/initialize', methods=['POST'])
@trading_limit_required
def initialize_portfolio():
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    portfolio = Portfolio.query.filter_by(user_id=user_id).first()
    if portfolio:
        return jsonify({'message': 'Portfolio already exists', 'portfolio': portfolio.to_dict()})
    
    # Create new portfolio with initial virtual funds
    portfolio = Portfolio(user_id=user_id, cash_balance=Decimal(str(FREE_TIER_LIMIT)))
    db.session.add(portfolio)
    db.session.commit()
    
    return jsonify({
        'message': 'Portfolio initialized successfully',
        'portfolio': portfolio.to_dict()
    })

@portfolio_bp.route('/balance', methods=['GET'])
@trading_limit_required
def get_balance():
    user_id = get_user_id()
    portfolio = Portfolio.query.filter_by(user_id=user_id).first()
    if not portfolio:
    # Auto-initialize portfolio if not found
        # This should ideally be handled by the frontend calling /initialize explicitly once
        # For robustness, we can create it here if it doesn't exist, but it's better if the frontend manages it
        portfolio = Portfolio(user_id=user_id, cash_balance=Decimal(str(FREE_TIER_LIMIT)))
        db.session.add(portfolio)
        db.session.commit()
        return jsonify({'cash_balance': float(portfolio.cash_balance)})

    return jsonify({'cash_balance': float(portfolio.cash_balance)})

@portfolio_bp.route('/holdings', methods=['GET'])
@trading_limit_required
def get_holdings():
    user_id = get_user_id()
    portfolio = Portfolio.query.filter_by(user_id=user_id).first()
    if not portfolio:
        return jsonify({'holdings': []})

    return jsonify({'holdings': [h.to_dict() for h in portfolio.holdings]})

@portfolio_bp.route('/buy', methods=['POST'])
@trading_limit_required
def buy_stock():
    user_id = get_user_id()
    data = request.json
    symbol = data.get('symbol')
    quantity = int(data.get('quantity', 0))
    price = Decimal(str(data.get('price', 0)))
    
    if quantity <= 0 or price <= 0:
        return jsonify({'error': 'Quantity and price must be positive'}), 400
    
    total_cost = quantity * price
    
    can_trade, error_msg = check_trading_limit(user_id, total_cost, is_sell=False)
    if not can_trade:
        return jsonify({'error': error_msg}), 400

    portfolio = Portfolio.query.filter_by(user_id=user_id).first()
    if not portfolio:
        # This case should ideally be handled by frontend calling /initialize first
        # But if it happens, auto-initialize with free tier limit
        portfolio = Portfolio(user_id=user_id, cash_balance=Decimal(str(FREE_TIER_LIMIT)))
        db.session.add(portfolio)
        db.session.commit()
        db.session.refresh(portfolio) # Refresh to get the newly created portfolio object

    if portfolio.cash_balance < total_cost:
        return jsonify({'error': 'Insufficient cash balance'}), 400

    holding = Holding.query.filter_by(portfolio_id=portfolio.id, symbol=symbol).first()
    if holding:
        new_quantity = holding.quantity + quantity
        new_avg_price = ((holding.quantity * holding.avg_price) + total_cost) / new_quantity
        holding.quantity = new_quantity
        holding.avg_price = new_avg_price
    else:
        holding = Holding(portfolio_id=portfolio.id, symbol=symbol, quantity=quantity, avg_price=price)
        db.session.add(holding)

    portfolio.cash_balance -= total_cost

    transaction = Transaction(
        user_id=user_id,
        symbol=symbol,
        quantity=quantity,
        price=price,
        type='buy'
    )
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({
        'message': 'Stock purchased successfully',
        'portfolio': portfolio.to_dict(),
        'transaction': transaction.to_dict()
    })

@portfolio_bp.route('/sell', methods=['POST'])
@trading_limit_required
def sell_stock():
    user_id = get_user_id()
    data = request.json
    symbol = data.get('symbol')
    quantity_to_sell = int(data.get('quantity', 0))
    price = Decimal(str(data.get('price', 0)))

    if quantity_to_sell <= 0 or price <= 0:
        return jsonify({'error': 'Quantity and price must be positive'}), 400

    portfolio = Portfolio.query.filter_by(user_id=user_id).first()
    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404
    
    holding = Holding.query.filter_by(portfolio_id=portfolio.id, symbol=symbol).first()
    if not holding or holding.quantity < quantity_to_sell:
        return jsonify({'error': 'Insufficient shares to sell'}), 400

    holding.quantity -= quantity_to_sell
    portfolio.cash_balance += (quantity_to_sell * price)

    if holding.quantity == 0:
        db.session.delete(holding)

    transaction = Transaction(
        user_id=user_id,
        symbol=symbol,
        quantity=quantity_to_sell,
        price=price,
        type='sell'
    )
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({
        'message': 'Stock sold successfully',
        'portfolio': portfolio.to_dict(),
        'transaction': transaction.to_dict()
    })

@portfolio_bp.route('/transactions', methods=['GET'])
@trading_limit_required
def get_transactions():
    user_id = get_user_id()
    # Fetch transactions from the database
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.created_at.desc()).all()
    
    # Optional filtering by date range (frontend typically handles this, but backend can support)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    filtered_transactions = transactions
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        filtered_transactions = [t for t in filtered_transactions if t.created_at.date() >= start_date.date()]
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        filtered_transactions = [t for t in filtered_transactions if t.created_at.date() <= end_date.date()]
    
    return jsonify({'transactions': [t.to_dict() for t in filtered_transactions]})

@portfolio_bp.route('/reset', methods=['POST'])
@trading_limit_required
def reset_portfolio():
    user_id = get_user_id()
    portfolio = Portfolio.query.filter_by(user_id=user_id).first()

    if portfolio:
        # Delete all holdings associated with the portfolio
        Holding.query.filter_by(portfolio_id=portfolio.id).delete()
        db.session.delete(portfolio)
        db.session.commit()

    # Re-create portfolio with initial virtual funds
    portfolio = Portfolio(user_id=user_id, cash_balance=Decimal(str(FREE_TIER_LIMIT)))
    db.session.add(portfolio)
    db.session.commit()

    # Optionally, delete all past transactions for the user as well on reset
    # Transaction.query.filter_by(user_id=user_id).delete()
    # db.session.commit()
    
    return jsonify({
        'message': 'Portfolio reset successfully',
        'portfolio': portfolio.to_dict()
    })

