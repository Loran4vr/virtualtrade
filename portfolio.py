from flask import Blueprint, jsonify, request, session
from datetime import datetime
import uuid

portfolio_bp = Blueprint('portfolio', __name__)

# In-memory storage for user portfolios (in a real app, this would be a database)
portfolios = {}
transactions = {}

@portfolio_bp.route('/initialize', methods=['POST'])
def initialize_portfolio():
    """Initialize a new portfolio for a user"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user']['id']
    
    # Check if portfolio already exists
    if user_id in portfolios:
        return jsonify({'message': 'Portfolio already exists', 'portfolio': portfolios[user_id]})
    
    # Create new portfolio with initial virtual funds
    initial_balance = 1000000  # 10 Lakh INR
    portfolios[user_id] = {
        'cash_balance': initial_balance,
        'holdings': {},
        'created_at': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat()
    }
    
    # Initialize transactions list
    transactions[user_id] = []
    
    return jsonify({
        'message': 'Portfolio initialized successfully',
        'portfolio': portfolios[user_id]
    })

@portfolio_bp.route('/balance', methods=['GET'])
def get_balance():
    """Get user's cash balance"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user']['id']
    
    # Auto-initialize portfolio if not found
    if user_id not in portfolios:
        initial_balance = 1000000  # 10 Lakh INR
        portfolios[user_id] = {
            'cash_balance': initial_balance,
            'holdings': {},
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        transactions[user_id] = []
    
    return jsonify({
        'cash_balance': portfolios[user_id]['cash_balance']
    })

@portfolio_bp.route('/holdings', methods=['GET'])
def get_holdings():
    """Get user's current holdings"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user']['id']
    
    # Auto-initialize portfolio if not found
    if user_id not in portfolios:
        initial_balance = 1000000  # 10 Lakh INR
        portfolios[user_id] = {
            'cash_balance': initial_balance,
            'holdings': {},
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        transactions[user_id] = []
    
    return jsonify({
        'holdings': portfolios[user_id]['holdings']
    })

@portfolio_bp.route('/buy', methods=['POST'])
def buy_stock():
    """Buy a stock"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user']['id']
    
    if user_id not in portfolios:
        return jsonify({'error': 'Portfolio not found'}), 404
    
    data = request.json
    if not data or 'symbol' not in data or 'quantity' not in data or 'price' not in data:
        return jsonify({'error': 'Symbol, quantity, and price are required'}), 400
    
    symbol = data['symbol']
    quantity = int(data['quantity'])
    price = float(data['price'])
    
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400
    
    # Calculate total cost
    total_cost = quantity * price
    
    # Check if user has enough balance
    if portfolios[user_id]['cash_balance'] < total_cost:
        return jsonify({'error': 'Insufficient funds'}), 400
    
    # Update cash balance
    portfolios[user_id]['cash_balance'] -= total_cost
    
    # Update holdings
    if symbol in portfolios[user_id]['holdings']:
        # Average out the purchase price
        current_holding = portfolios[user_id]['holdings'][symbol]
        total_shares = current_holding['quantity'] + quantity
        avg_price = ((current_holding['quantity'] * current_holding['avg_price']) + total_cost) / total_shares
        
        portfolios[user_id]['holdings'][symbol] = {
            'quantity': total_shares,
            'avg_price': avg_price,
            'last_updated': datetime.now().isoformat()
        }
    else:
        portfolios[user_id]['holdings'][symbol] = {
            'quantity': quantity,
            'avg_price': price,
            'last_updated': datetime.now().isoformat()
        }
    
    # Record transaction
    transaction = {
        'id': str(uuid.uuid4()),
        'type': 'BUY',
        'symbol': symbol,
        'quantity': quantity,
        'price': price,
        'total': total_cost,
        'timestamp': datetime.now().isoformat()
    }
    
    transactions[user_id].append(transaction)
    
    # Update portfolio last updated timestamp
    portfolios[user_id]['last_updated'] = datetime.now().isoformat()
    
    return jsonify({
        'message': 'Stock purchased successfully',
        'transaction': transaction,
        'updated_balance': portfolios[user_id]['cash_balance'],
        'updated_holdings': portfolios[user_id]['holdings'][symbol]
    })

@portfolio_bp.route('/sell', methods=['POST'])
def sell_stock():
    """Sell a stock"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user']['id']
    
    if user_id not in portfolios:
        return jsonify({'error': 'Portfolio not found'}), 404
    
    data = request.json
    if not data or 'symbol' not in data or 'quantity' not in data or 'price' not in data:
        return jsonify({'error': 'Symbol, quantity, and price are required'}), 400
    
    symbol = data['symbol']
    quantity = int(data['quantity'])
    price = float(data['price'])
    
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400
    
    # Check if user has the stock and enough quantity
    if symbol not in portfolios[user_id]['holdings'] or portfolios[user_id]['holdings'][symbol]['quantity'] < quantity:
        return jsonify({'error': 'Insufficient holdings'}), 400
    
    # Calculate total sale value
    total_sale = quantity * price
    
    # Update cash balance
    portfolios[user_id]['cash_balance'] += total_sale
    
    # Update holdings
    current_holding = portfolios[user_id]['holdings'][symbol]
    remaining_quantity = current_holding['quantity'] - quantity
    
    if remaining_quantity > 0:
        portfolios[user_id]['holdings'][symbol]['quantity'] = remaining_quantity
        portfolios[user_id]['holdings'][symbol]['last_updated'] = datetime.now().isoformat()
    else:
        # Remove the holding if all shares are sold
        del portfolios[user_id]['holdings'][symbol]
    
    # Record transaction
    transaction = {
        'id': str(uuid.uuid4()),
        'type': 'SELL',
        'symbol': symbol,
        'quantity': quantity,
        'price': price,
        'total': total_sale,
        'timestamp': datetime.now().isoformat()
    }
    
    transactions[user_id].append(transaction)
    
    # Update portfolio last updated timestamp
    portfolios[user_id]['last_updated'] = datetime.now().isoformat()
    
    return jsonify({
        'message': 'Stock sold successfully',
        'transaction': transaction,
        'updated_balance': portfolios[user_id]['cash_balance'],
        'updated_holdings': portfolios[user_id]['holdings'].get(symbol, 'Fully sold')
    })

@portfolio_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """Get user's transaction history"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user']['id']
    
    if user_id not in transactions:
        return jsonify({'transactions': []})
    
    # Optional filtering by date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    filtered_transactions = transactions[user_id]
    
    if start_date:
        filtered_transactions = [t for t in filtered_transactions if t['timestamp'] >= start_date]
    
    if end_date:
        filtered_transactions = [t for t in filtered_transactions if t['timestamp'] <= end_date]
    
    return jsonify({
        'transactions': filtered_transactions
    })

@portfolio_bp.route('/reset', methods=['POST'])
def reset_portfolio():
    """Reset user's portfolio to initial state"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user']['id']
    
    # Create new portfolio with initial virtual funds
    initial_balance = 1000000  # 10 Lakh INR
    portfolios[user_id] = {
        'cash_balance': initial_balance,
        'holdings': {},
        'created_at': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat()
    }
    
    # Reset transactions list
    transactions[user_id] = []
    
    return jsonify({
        'message': 'Portfolio reset successfully',
        'portfolio': portfolios[user_id]
    })

