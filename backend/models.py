from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(120), unique=True)
    name = db.Column(db.String(120))
    picture = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    portfolio = db.relationship('Portfolio', backref='user', uselist=False)
    transactions = db.relationship('Transaction', backref='user')
    subscription = db.relationship('Subscription', backref='user', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'picture': self.picture,
            'created_at': self.created_at.isoformat()
        }

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    cash_balance = db.Column(db.Numeric(15, 2), default=1000000)  # Default 10 lakhs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    holdings = db.relationship('Holding', backref='portfolio', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'cash_balance': float(self.cash_balance),
            'created_at': self.created_at.isoformat(),
            'holdings': [h.to_dict() for h in self.holdings]
        }

class Holding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'))
    symbol = db.Column(db.String(20))
    quantity = db.Column(db.Integer)
    avg_price = db.Column(db.Numeric(15, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'avg_price': float(self.avg_price),
            'created_at': self.created_at.isoformat()
        }

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    symbol = db.Column(db.String(20))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Numeric(15, 2))
    type = db.Column(db.String(10))  # 'buy' or 'sell'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'price': float(self.price),
            'type': self.type,
            'created_at': self.created_at.isoformat()
        }

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    plan_id = db.Column(db.String(20))  # 'basic', 'standard', 'premium', 'ultimate'
    credit_limit = db.Column(db.Numeric(15, 2))
    price_paid = db.Column(db.Numeric(10, 2))
    starts_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan_id': self.plan_id,
            'credit_limit': float(self.credit_limit),
            'price_paid': float(self.price_paid),
            'starts_at': self.starts_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'created_at': self.created_at.isoformat()
        }

class HistoricalPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    open = db.Column(db.Numeric(15, 2))
    high = db.Column(db.Numeric(15, 2))
    low = db.Column(db.Numeric(15, 2))
    close = db.Column(db.Numeric(15, 2))
    volume = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('symbol', 'date', name='_symbol_date_uc'),)

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'date': self.date.isoformat(),
            'open': float(self.open) if self.open else None,
            'high': float(self.high) if self.high else None,
            'low': float(self.low) if self.low else None,
            'close': float(self.close) if self.close else None,
            'volume': self.volume,
            'created_at': self.created_at.isoformat()
        } 