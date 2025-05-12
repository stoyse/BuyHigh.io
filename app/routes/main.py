from flask import Blueprint, render_template, redirect, url_for, flash, request, g, jsonify, session
from flask_login import login_required, current_user
from app.models import User, Portfolio, Asset, Transaction
from app import db
from datetime import datetime, timedelta
import random

main = Blueprint('main', __name__)

# Other routes...

@main.route('/dashboard')
@login_required
def dashboard():
    # Get recent transactions
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(5).all()
    
    # Fetch user's portfolio
    user_assets = Portfolio.query.filter_by(user_id=current_user.id).all()
    
    # Initialize portfolio data
    portfolio_data = {
        'success': True,
        'portfolio': [],
        'best_performer': 'N/A',
        'best_performer_pct': 0.0
    }
    
    portfolio_total_value = 0
    best_performance = -float('inf')
    
    # Process each asset in the portfolio
    for user_asset in user_assets:
        # Get asset details
        asset = Asset.query.get(user_asset.asset_id)
        if not asset:
            continue
        
        # Calculate current value
        current_value = user_asset.quantity * asset.current_price
        portfolio_total_value += current_value
        
        # Calculate performance
        if user_asset.purchase_price > 0:
            performance = ((asset.current_price - user_asset.purchase_price) / user_asset.purchase_price) * 100
        else:
            performance = 0
            
        # Check if it's the best performer
        if performance > best_performance:
            best_performance = performance
            portfolio_data['best_performer'] = asset.symbol
            portfolio_data['best_performer_pct'] = performance
        
        # Add to portfolio data
        portfolio_data['portfolio'].append({
            'symbol': asset.symbol,
            'name': asset.name,
            'quantity': user_asset.quantity,
            'purchase_price': user_asset.purchase_price,
            'current_price': asset.current_price,
            'performance': performance,
            'type': asset.asset_type
        })
    
    # Generate random dog message for companion
    dog_messages = [
        "Buy high, sell higher! This is the way! 🚀",
        "Diamond hands will be rewarded! 💎🙌",
        "Never sell, only HODL! The moon is waiting! 🌕",
        "Fear is temporary, gains are forever! 📈",
        "This dip is just a discount! Buy now! 🛒",
        "Today's red candles are tomorrow's green rockets! 🚀",
        "Apes together strong! 🦍",
        "Paper hands lose money, diamond hands gain glory! 💰"
    ]
    dog_message = random.choice(dog_messages)
    
    return render_template('dashboard.html', 
                           recent_transactions=recent_transactions,
                           portfolio_data=portfolio_data,
                           portfolio_total_value=portfolio_total_value,
                           dog_message=dog_message)

# Other routes...
