from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from utils import login_required
import stock_data
import database.handler.postgres.postgre_transactions_handler as transactions_handler
import pandas as pd # Import pandas for pd.notna()

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/stock-data')
@login_required
def api_stock_data():
    symbol = request.args.get('symbol', 'AAPL')
    timeframe = request.args.get('timeframe', '3M')
    
    end_date_dt = datetime.now()
    start_date_dt = None 
    
    # Parameter für den API-Aufruf vorbereiten
    period_param_for_1min = None # Nur für 1MIN timeframe
    # interval_param wird basierend auf timeframe gesetzt
    
    if timeframe == '1MIN':
        period_param_for_1min = '2d' 
        interval_param = '1m'
        start_date_dt = end_date_dt - timedelta(days=2) # Für Demo-Daten-Logik und ggf. start/end
    elif timeframe == '1W':
        interval_param = '1d' # yfinance default für tägliche Daten
        start_date_dt = end_date_dt - timedelta(days=7)
    elif timeframe == '1M':
        interval_param = '1d'
        start_date_dt = end_date_dt - timedelta(days=30)
    elif timeframe == '3M':
        interval_param = '1d'
        start_date_dt = end_date_dt - timedelta(days=90)
    elif timeframe == '6M':
        interval_param = '1d'
        start_date_dt = end_date_dt - timedelta(days=180)
    elif timeframe == '1Y':
        interval_param = '1d'
        start_date_dt = end_date_dt - timedelta(days=365)
    elif timeframe == 'ALL':
        interval_param = '1d'
        start_date_dt = end_date_dt - timedelta(days=1825) # 5 Jahre
    else: # Standard auf 3M
        interval_param = '1d'
        start_date_dt = end_date_dt - timedelta(days=90)

    end_date_str = end_date_dt.strftime('%Y-%m-%d')
    # Stelle sicher, dass start_date_str nur gesetzt wird, wenn start_date_dt nicht None ist
    start_date_str = start_date_dt.strftime('%Y-%m-%d') if start_date_dt else None
    
    try:
        if timeframe == '1MIN':
            df = stock_data.get_stock_data(symbol, period=period_param_for_1min, interval=interval_param)
        else:
            # Übergebe nur symbol, KEIN interval!
            df = stock_data.get_stock_data(symbol)
        
        if df is None or df.empty:
            is_minutes_demo = timeframe == '1MIN'
            demo_days = (end_date_dt - start_date_dt).days if start_date_dt is not None else 90 
            demo_units = 240 if is_minutes_demo else demo_days

            # KORREKTUR: Nur symbol und demo_units übergeben!
            df = stock_data.get_demo_stock_data(symbol, demo_units)

            if df is None or df.empty: 
                print(f"No data (including demo) found for {symbol}. Returning empty list.")
                return jsonify([]) 

        data = []
        # Ensure df is not None and has rows before iterating, and required columns exist
        if df is not None and not df.empty:
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_columns):
                print(f"Data for {symbol} is missing one or more required columns: {required_columns}. Available: {list(df.columns)}")
                return jsonify({'error': f'Data processing error: Missing columns for {symbol}', 'currency': 'USD'}), 500

            for index, row in df.iterrows():
                try:
                    # Ensure index is timezone-naive before formatting for consistency
                    timestamp_to_format = index.tz_localize(None) if index.tzinfo else index
                    
                    # Check for NaN or None before conversion
                    open_price = float(row['Open']) if pd.notna(row['Open']) else None
                    high_price = float(row['High']) if pd.notna(row['High']) else None
                    low_price = float(row['Low']) if pd.notna(row['Low']) else None
                    close_price = float(row['Close']) if pd.notna(row['Close']) else None
                    volume = int(row['Volume']) if pd.notna(row['Volume']) else None

                    # If any critical value is None after attempting conversion, skip this row
                    if any(v is None for v in [open_price, high_price, low_price, close_price, volume]):
                        print(f"Skipping row for {symbol} at {index} due to missing critical data after pd.notna check.")
                        continue

                    data.append({
                        'date': timestamp_to_format.strftime('%Y-%m-%dT%H:%M:%S'), # ISO format for JS Date constructor
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'volume': volume,
                        'currency': 'USD'  # Add currency information
                    })
                except (ValueError, TypeError) as e:
                    print(f"Error converting row data for {symbol} at {index}: {e}. Row: {row.to_dict()}")
                    continue # Skip rows with conversion errors
        
        return jsonify(data)
    except Exception as e:
        print(f"Error in /api/stock-data for {symbol} timeframe {timeframe}: {e}") # Log error
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'currency': 'USD'}), 500

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
    return jsonify({"message": f"Data for symbol {symbol} not yet implemented."}), 404
