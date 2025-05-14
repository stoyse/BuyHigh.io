from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from utils import login_required
import stock_data_api as stock_data  # <-- NEU: Importiere das neue Modul
import database.handler.postgres.postgre_transactions_handler as transactions_handler
import pandas as pd # Import pandas for pd.notna()
import logging # Import logging module

# Logger für dieses Modul konfigurieren
logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/stock-data')
@login_required
def api_stock_data():
    symbol = request.args.get('symbol', 'AAPL')
    timeframe = request.args.get('timeframe', '3M')
    
    # Force fresh data flag hinzufügen
    force_fresh = request.args.get('fresh', 'false').lower() == 'true'
    
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
        # Immer direkt von der API laden, ohne Cache zu verwenden, wenn force_fresh gesetzt ist
        if force_fresh:
            logger.info(f"Force fresh data for {symbol}, timeframe: {timeframe}")
            df = stock_data.get_stock_data(symbol, period=period_param_for_1min, interval=interval_param, 
                                          start_date=start_date_str, end_date=end_date_str)
        else:
            logger.info(f"Getting cached or live data for {symbol}, timeframe: {timeframe}")
            df = stock_data.get_cached_or_live_data(symbol, timeframe)
        
        is_demo_data = getattr(df, 'is_demo', True) # Default to True if attribute missing or df is None
        
        logger.info(f"Data received for {symbol}: Demo = {is_demo_data}, Points = {len(df) if df is not None and not df.empty else 0}")
        
        if df is None or df.empty:
            # This block might be redundant if get_cached_or_live_data always returns a df (even demo)
            # For safety, ensure demo data is generated if df is still None or empty.
            logger.warning(f"DataFrame for {symbol} is None or empty. Generating explicit demo data.")
            is_minutes_demo = timeframe == '1MIN'
            demo_days = (end_date_dt - start_date_dt).days if start_date_dt is not None else 90
            
            # For 1MIN, demo_units should represent minutes, not days
            demo_units = 240 if is_minutes_demo else demo_days # 240 minutes for 1MIN demo
            
            df = stock_data.get_demo_stock_data(symbol, demo_units, is_minutes=is_minutes_demo)
            is_demo_data = True # Explicitly set as demo
            
            if df is None or df.empty: 
                logger.error(f"No data (including fallback demo) found for {symbol}. Returning empty list.")
                return jsonify({'data': [], 'is_demo': True, 'currency': 'USD', 'demo_reason': 'API key missing' if not stock_data.TWELVE_DATA_API_KEY else 'API request failed or empty data'})


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
        
        # Nach dem Laden der Daten, den letzten Kurs in der Assets-Datenbank aktualisieren
        # NUR wenn es KEINE Demo-Daten sind und Daten vorhanden sind
        if not is_demo_data and len(data) > 0 and data[-1].get('close') is not None:
            try:
                update_asset_price(symbol, float(data[-1]['close']))
            except Exception as e:
                # Nur loggen, nicht abbrechen wenn Update fehlschlägt
                logger.error(f"Error updating asset price in database: {e}")
        
        # Änderung: Direkt das Array zurückgeben, nicht in einem Objekt verpacken
        return jsonify(data)
    except Exception as e:
        print(f"Error in /api/stock-data for {symbol} timeframe {timeframe}: {e}") # Log error
        return jsonify({'error': str(e), 'currency': 'USD'}), 500

# Neue Hilfsfunktion zum Aktualisieren der Asset-Preise in der Datenbank
def update_asset_price(symbol, price):
    """Aktualisiert den letzten bekannten Preis eines Assets in der Datenbank"""
    try:
        with transactions_handler.get_connection() as conn:
            with conn.cursor() as cur:
                # Prüfen, ob das Asset existiert
                cur.execute("SELECT id FROM assets WHERE symbol = %s", (symbol,))
                asset_row = cur.fetchone()
                
                if not asset_row:
                    logger.warning(f"Asset mit Symbol '{symbol}' nicht gefunden, kann Preis nicht aktualisieren.")
                    return False
                
                # Preis in einer separaten Tabelle oder Feld aktualisieren
                # Hier verwenden wir eine einfache UPDATE-Anweisung anstatt einen neuen Typ zu erstellen
                cur.execute("""
                    UPDATE assets SET last_price = %s, last_price_updated = CURRENT_TIMESTAMP
                    WHERE symbol = %s
                """, (price, symbol))
                conn.commit()
                return True
    except Exception as e:
        logger.error(f"Error updating asset price in database: {e}", exc_info=True)
        return False

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

@api_bp.route('/assets')
@login_required
def api_get_assets():
    """API-Endpunkt zum Abrufen aller Assets oder nach Asset-Typ gefiltert"""
    asset_type = request.args.get('type', None)
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    
    result = transactions_handler.get_all_assets(active_only, asset_type)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@api_bp.route('/assets/<symbol>')
@login_required
def api_get_asset(symbol):
    """API-Endpunkt zum Abrufen eines bestimmten Assets anhand seines Symbols"""
    result = transactions_handler.get_asset_by_symbol(symbol)
    
    # Stellen Sie sicher, dass last_price nicht zurückgegeben wird, sondern nur default_price
    if result['success'] and 'asset' in result and result['asset']:
        # Wenn last_price vorhanden ist, entfernen
        if 'last_price' in result['asset']:
            del result['asset']['last_price']
        
        # last_price_updated Feld auch entfernen
        if 'last_price_updated' in result['asset']:
            del result['asset']['last_price_updated']
            
        # Falls default_price nicht gesetzt ist, einen Standardwert verwenden
        if 'default_price' not in result['asset'] or result['asset']['default_price'] is None:
            logger.warning(f"Asset {symbol} hat keinen default_price gesetzt!")
            result['asset']['default_price'] = 100.0  # Fallback-Wert
    
    return jsonify(result) if result['success'] else (jsonify(result), 404)

@api_bp.route('/status')
@login_required
def api_status():
    """API-Endpunkt, um den Status der API-Keys zu prüfen"""
    return jsonify({
        'api_key_configured': bool(stock_data.TWELVE_DATA_API_KEY),
        'timestamp': datetime.now().isoformat()
    })

# Dummy route from original app.py, can be removed if not used
@api_bp.route('/trade/<symbol>/')
@login_required
def api_stock_data_symbol(symbol):
    return jsonify({"message": f"Data for symbol {symbol} not yet implemented."}), 404
