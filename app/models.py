from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    balance = db.Column(db.Float, default=10000.0)  # Default starting balance
    profit_loss = db.Column(db.Float, default=0.0)
    profit_loss_percentage = db.Column(db.Float, default=0.0)
    total_trades = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pet_energy = db.Column(db.Integer, default=100)
    is_meme_mode = db.Column(db.Boolean, default=False)
    
    portfolio = db.relationship('Portfolio', backref='user', lazy='dynamic')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), index=True, unique=True)
    name = db.Column(db.String(100))
    asset_type = db.Column(db.String(50))  # stock, crypto, etc.
    current_price = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    
    portfolios = db.relationship('Portfolio', backref='asset', lazy='dynamic')
    transactions = db.relationship('Transaction', backref='asset', lazy='dynamic')

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'))
    quantity = db.Column(db.Float)
    purchase_price = db.Column(db.Float)  # Average purchase price
    
    __table_args__ = (db.UniqueConstraint('user_id', 'asset_id', name='uix_user_asset'),)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'))
    transaction_type = db.Column(db.String(10))  # buy or sell
    quantity = db.Column(db.Float)
    price_per_unit = db.Column(db.Float)
    total_cost = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Virtual property to get the asset symbol
    @property
    def asset_symbol(self):
        return self.asset.symbol if self.asset else "Unknown"
