from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from utils import login_required
import stock_data
import transactions_handler

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/stock-data')
@login_required
def api_stock_data():
    symbol = request.args.get('symbol', 'AAPL')
    timeframe = request.args.get('timeframe', '3M')
    
    end_date_dt = datetime.now()
    start_date_dt = None
    interval_param = '1d' # Default for yfinance daily
    period_param = None

    if timeframe == '1MIN':
        period_param = '2d' # Fetch data for the last 2 days for 1-minute intervals
        interval_param = '1m'
        # For 1MIN, yfinance typically uses 'period' and 'interval'.
        # 'start_date' and 'end_date' might not be needed or could be used to narrow down from the '2d' period if necessary.
        # For simplicity, we'll rely on 'period' for 1MIN.
        start_date_str = (end_date_dt - timedelta(days=2)).strftime('%Y-%m-%d') # Example, adjust as needed
        end_date_str = end_date_dt.strftime('%Y-%m-%d')
    elif timeframe == '1W':
        start_date_dt = end_date_dt - timedelta(days=7)
    elif timeframe == '1M':
        start_date_dt = end_date_dt - timedelta(days=30)
    elif timeframe == '3M':
        start_date_dt = end_date_dt - timedelta(days=90)
    elif timeframe == '6M':
        start_date_dt = end_date_dt - timedelta(days=180)
    elif timeframe == '1Y':
        start_date_dt = end_date_dt - timedelta(days=365)
    elif timeframe == 'ALL':
        start_date_dt = end_date_dt - timedelta(days=1825) # 5 years
    else: # Default to 3M
        start_date_dt = end_date_dt - timedelta(days=90)

    if start_date_dt:
        start_date_str = start_date_dt.strftime('%Y-%m-%d')
    if not period_param: # Only format end_date_str if not using period for 1MIN
        end_date_str = end_date_dt.strftime('%Y-%m-%d')
    
    try:
        if timeframe == '1MIN':
            df = stock_data.get_stock_data(symbol, period=period_param, interval=interval_param)
        else:
            df = stock_data.get_stock_data(symbol, start=start_date_str, end=end_date_str, interval=interval_param)
        
        if df.empty:
            # Pass 'is_minutes' for demo data generation if timeframe is 1MIN
            is_minutes_demo = timeframe == '1MIN'
            demo_units = 240 if is_minutes_demo else (end_date_dt - start_date_dt).days if start_date_dt else 90
            df = stock_data.get_demo_stock_data(symbol, units=demo_units, is_minutes=is_minutes_demo)

        data = []
        for index, row in df.iterrows():
            # Ensure index is timezone-naive before formatting for consistency
            timestamp_to_format = index.tz_localize(None) if index.tzinfo else index
            data.append({
                'date': timestamp_to_format.strftime('%Y-%m-%dT%H:%M:%S'), # ISO format for JS Date constructor
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })
        
        return jsonify(data)
    except Exception as e:
        print(f"Error in /api/stock-data: {e}") # Log error
        return jsonify({'error': str(e)}), 500

@api_bp.route('/trade/buy', methods=['POST'])
@login_required
def api_buy_stock():
    data = request.get_json()
    symbol = data.get('symbol')
    quantity = data.get('quantity')
    price = data.get('price')

    if not all([symbol, quantity, price]):
        return jsonify({"success": False, "message": "Missing data for transaction."}), 400

    try:
        quantity = float(quantity)
        price = float(price)
        if quantity <= 0 or price <= 0:
            raise ValueError("Quantity and price must be positive.")
    except ValueError as e:
        return jsonify({"success": False, "message": f"Invalid input: {e}"}), 400

    user_id = g.user['id']
    result = transactions_handler.buy_stock(user_id, symbol, quantity, price)
    return jsonify(result)

@api_bp.route('/trade/sell', methods=['POST'])
@login_required
def api_sell_stock():
    data = request.get_json()
    symbol = data.get('symbol')
    quantity = data.get('quantity')
    price = data.get('price')

    if not all([symbol, quantity, price]):
        return jsonify({"success": False, "message": "Missing data for transaction."}), 400

    try:
        quantity = float(quantity)
        price = float(price)
        if quantity <= 0 or price <= 0:
            raise ValueError("Quantity and price must be positive.")
    except ValueError as e:
        return jsonify({"success": False, "message": f"Invalid input: {e}"}), 400
        
    user_id = g.user['id']
    result = transactions_handler.sell_stock(user_id, symbol, quantity, price)
    return jsonify(result)

@api_bp.route('/portfolio', methods=['GET'])
@login_required
def api_get_portfolio():
    user_id = g.user['id']
    portfolio_data = transactions_handler.show_user_portfolio(user_id)
    return jsonify(portfolio_data)

# Dummy route from original app.py, can be removed if not used
@api_bp.route('/trade/<symbol>/')
@login_required
def api_stock_data_symbol(symbol):
    # This route was empty in the original app.py
    # If it's needed, implement its functionality here.
    # For now, let's return a placeholder or an error.
    return jsonify({"message": f"Data for symbol {symbol} not yet implemented."}), 404
