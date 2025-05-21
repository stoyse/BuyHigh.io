# HINWEIS: Diese Flask-Routen werden zu FastAPI migriert.
# Der neue FastAPI-Router befindet sich in buy_high_backend/api_router.py.
# Dieser Code dient als Referenz und wird schrittweise ersetzt.

from flask import Blueprint, request, jsonify, g, send_file, url_for, session, current_app
from datetime import datetime, timedelta
from utils.utils import login_required
import os
import utils.stock_data_api as stock_data
import database.handler.postgres.postgre_transactions_handler as transactions_handler
from database.handler.postgres.postgres_db_handler import add_analytics
import pandas as pd
import logging
import utils.auth as auth_module  # Fix the import path to match the correct module name
import database.handler.postgres.postgres_db_handler as db_handler
import database.handler.postgres.postgre_education_handler as education_handler
from utils.models import db, EasterEggRedemption  # db und EasterEggRedemption importieren
from buy_high_backend.pydantic_models import User  # User importieren

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

# CSRF-Schutz für bestimmte Routes deaktivieren
@api_bp.before_request
def csrf_exempt_for_easter_eggs():
    """Deaktiviert CSRF-Schutz für bestimmte API-Endpunkte"""
    if request.path == '/api/easter-egg/redeem':
        flask_csrf = current_app.extensions.get('csrf', None)
        if flask_csrf:
            flask_csrf._exempt_views.add(request.endpoint)

@api_bp.route('/login', methods=['POST'])
def api_login():
    """API-Route für die Benutzeranmeldung"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    # Add logging to help debug the issue
    logger.info(f"Login attempt for email: {email}")

    if not email or not password:
        logger.warning("Login attempt with missing email or password")
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    try:
        # Ensure we're using the correct function name from auth_module
        firebase_uid, id_token = auth_module.login_firebase_user_rest(email, password)
        logger.info(f"Firebase authentication successful for email: {email}, UID: {firebase_uid}")
        
        if not firebase_uid or not id_token:
            logger.warning(f"Firebase authentication returned empty UID or token for email: {email}")
            return jsonify({"success": False, "message": "Invalid email or password."}), 401

        # Get user from the database
        local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
        
        # If user doesn't exist in local DB, try to find by email or create new
        if not local_user:
            logger.info(f"No local user found with Firebase UID: {firebase_uid}, checking by email")
            local_user = db_handler.get_user_by_email(email)
            
            # Create new local user if not found
            if not local_user:
                logger.info(f"Creating new local user for email: {email}")
                username = email.split('@')[0]
                if db_handler.add_user(username, email, firebase_uid):
                    local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
                else:
                    logger.error(f"Failed to create local user for email: {email}")
                    return jsonify({"success": False, "message": "Failed to create user account."}), 500
            else:
                # Update the Firebase UID for existing user
                db_handler.update_firebase_uid(local_user['id'], firebase_uid)
                local_user['firebase_uid'] = firebase_uid
        
        if not local_user:
            logger.error(f"Critical error: Could not find or create local user for email: {email}")
            return jsonify({"success": False, "message": "User not found in the local database."}), 404

        # Set session data
        session.clear()
        session['logged_in'] = True
        session['user_id'] = local_user['id']
        session['firebase_uid'] = firebase_uid
        session['id_token'] = id_token
        session.permanent = True
        
        logger.info(f"Login successful for user ID: {local_user['id']}")
        logger.info(f"Session data set: user_id={session.get('user_id')}, firebase_uid={session.get('firebase_uid')}, logged_in={session.get('logged_in')}")
        
        # Update last login timestamp
        try:
            db_handler.update_last_login(local_user['id'])
        except Exception as e:
            logger.warning(f"Failed to update last login timestamp: {e}")
            # Non-critical error, continue

        # Return user ID in the response for frontend use
        return jsonify({
            "success": True, 
            "message": "Login successful.",
            "userId": local_user['id']
        }), 200
    except Exception as e:
        logger.error(f"Error during API login: {e}", exc_info=True)
        return jsonify({"success": False, "message": "An error occurred during login."}), 500

@api_bp.route('/stock-data')
@login_required
def api_stock_data():
    user_id_for_analytics = g.user.get('id') if hasattr(g, 'user') and g.user else None
    logger.info(f"Accessing /stock-data. g.user: {g.user if hasattr(g, 'user') else 'g.user not set'}")
    if hasattr(g, 'user') and g.user:
        logger.info(f"User ID from g.user: {g.user.get('id')}")
    else:
        logger.warning("No user found in g.user for @login_required route /stock-data")

    symbol = request.args.get('symbol', 'AAPL')
    timeframe = request.args.get('timeframe', '3M')
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
                update_asset_price(symbol, float(data[-1]['close'])) # Analytics inside update_asset_price
            except Exception as e:
                # Nur loggen, nicht abbrechen wenn Update fehlschlägt
                logger.error(f"Error updating asset price in database: {e}")
        
        # Änderung: Direkt das Array zurückgeben, nicht in einem Objekt verpacken
        return jsonify(data)
    except Exception as e:
        print(f"Error in /api/stock-data for {symbol} timeframe {timeframe}: {e}") # Log error
        return jsonify({'error': str(e), 'currency': 'USD'}), 500

# Neue Route für Funny Tips
@api_bp.route('/funny-tips', methods=['GET'])
@login_required # Annahme: Tipps erfordern Anmeldung
def api_get_funny_tips():
    """API-Endpunkt zum Abrufen von lustigen Tipps."""
    # Hier würden Sie normalerweise Tipps aus einer Datenbank oder einem Service laden
    # Für dieses Beispiel geben wir Dummy-Daten zurück
    tips = [
        {"id": 1, "tip": "Buy high, sell low. The secret to eternal brokerage fees."},
        {"id": 2, "tip": "If you don't know what you're doing, do it with conviction."},
        {"id": 3, "tip": "The market is like a box of chocolates... you never know what you're gonna get, but it's probably nuts."},
        {"id": 4, "tip": "Always diversify your portfolio: buy stocks in different shades of red."}
    ]
    return jsonify({"success": True, "tips": tips})


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


@api_bp.route('/assets')
@login_required
def api_get_assets():
    """API-Endpunkt zum Abrufen aller Assets oder nach Asset-Typ gefiltert"""
    asset_type = request.args.get('type', None)
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    
    result = transactions_handler.get_all_assets(active_only, asset_type)
    
    # Überprüfe, ob das Ergebnis None ist
    if result is None:
        logger.error(f"get_all_assets returned None for type={asset_type}, active_only={active_only}")
        return jsonify({
            "success": False,
            "message": "Failed to retrieve assets data. The database query returned no result.",
            "assets": []
        }), 500
    
    if result.get('success', False):
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


@api_bp.route('/upload/profile-picture', methods=['POST'])
@login_required
def api_upload_profile_picture():
    """API-Endpunkt zum Hochladen eines Profilbildes"""
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file part in the request."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file."}), 400

    try:
        # Get the application's root directory
        from flask import current_app
        upload_folder = os.path.join(current_app.root_path, 'static', 'user_data')
        
        # Create directory structure if it doesn't exist
        user_folder = os.path.join(upload_folder, str(g.user['id']))
        os.makedirs(user_folder, exist_ok=True)
        
        # Save the file with a secure filename
        from werkzeug.utils import secure_filename
        file_path = os.path.join(user_folder, f"profile_picture.png") # Consider unique filenames or overwriting logic
        file.save(file_path)
        
        # Update user profile in database to reference the new image
        # Assuming profile_pic_url is relative to static folder
        profile_pic_url = f"user_data/{g.user['id']}/profile_picture.png" # Adjusted path
        
        # Here you would update the user's profile in the database
        # Example: db_handler.update_user_profile_picture(g.user['id'], profile_pic_url)
        # For now, just logging
        logger.info(f"User {g.user['id']} profile picture path to be saved in DB: {profile_pic_url}")
        
        logger.info(f"Profile picture uploaded successfully for user {g.user['id']}")
        return jsonify({"success": True, "message": "File uploaded successfully.", "url": url_for('static', filename=profile_pic_url)}) # Return full URL
    
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"Error uploading file: {str(e)}"}), 500

@api_bp.route('/get/profile-picture/<user_id>', methods=['GET'])
@login_required
def api_get_profile_picture(user_id):
    """API-Endpunkt zum Abrufen des Profilbildes"""
    # Hier wird angenommen, dass der Pfad zum Profilbild in der Datenbank gespeichert ist
    # Zum Beispiel: db_handler.get_user_profile_picture(g.user['id'])
    
    # Dummy URL für das Beispiel
    profile_pic_url = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'static', 'user_data', str(user_id), 'profile_picture.png'
    )
    profile_pic_url = os.path.abspath(profile_pic_url)
    
    if os.path.exists(profile_pic_url):
        return send_file(profile_pic_url)
    else:
        return jsonify({"success": False, "message": "Profile picture not found."}), 404
    

@api_bp.route('/daily-quiz', methods=['GET'])
@login_required
def api_get_daily_quiz():
    """API-Endpunkt zum Abrufen des täglichen Quiz"""
    today = datetime.today().strftime('%Y-%m-%d')
    return jsonify(education_handler.get_daily_quiz(date=today))  # Keine Weiterleitungen, direkte Antwort


@api_bp.route('/user/<user_id>', methods=['GET'])
@login_required
def api_get_user_data(user_id):
    """API-Endpunkt zum Abrufen der Benutzerdaten"""
    return jsonify(db_handler.get_user_by_id(user_id=user_id))  # Keine Weiterleitungen, direkte Antwort

@api_bp.route('/user/transactions/<user_id>', methods=['GET'])
@login_required
def api_get_user_last_transactions(user_id):
    """API-Endpunkt zum Abrufen der letzten Transaktionen eines Benutzers"""
    transactions = transactions_handler.get_recent_transactions(user_id=user_id)
    if transactions:
        return jsonify(transactions)
    else:
        return jsonify({"success": False, "message": "No transactions found."}), 404

@api_bp.route('/user/portfolio/<user_id>', methods=['GET'])
@login_required
def api_get_portfolio(user_id):
    portfolio_data = transactions_handler.show_user_portfolio(user_id)
    return jsonify(portfolio_data)


@api_bp.route('/easter-egg/redeem', methods=['POST'])
def redeem_easter_egg():
    """
    Endpunkt zum Einlösen von Easter Egg-Codes
    Funktioniert sowohl für authentifizierte als auch für nicht authentifizierte Benutzer
    """
    logger.info("Easter egg redemption endpoint called")
    print("Easter egg redemption endpoint called")
    
    # Debug-Ausgabe für den Request
    print(f"Request headers: {request.headers}")
    print(f"Request content type: {request.content_type}")
    print(f"Request method: {request.method}")
    
    try:
        # Explizit Request-Body als raw data auslesen für Debug-Zwecke
        raw_data = request.get_data(as_text=True)
        print(f"Raw request data: {raw_data}")
        
        # JSON-Daten parsen
        data = request.get_json(force=True, silent=True)
        print(f"Parsed JSON data: {data}")
        
        if not data:
            logger.warning("No JSON data found in request")
            return jsonify({"success": False, "message": "Keine Daten gefunden. Bitte gib einen Code ein."}), 400
        
        if 'code' not in data:
            logger.warning("No code found in request data")
            return jsonify({"success": False, "message": "Kein Code in der Anfrage gefunden."}), 400
        
        code = data['code'].upper()
        logger.info(f"Processing easter egg code: {code}")
        
        # Standardmäßig ein Gast oder der aktuelle Benutzer
        user_id = None
        
        # Wenn Benutzer authentifiziert ist, seinen Account aktualisieren
        if hasattr(g, 'user') and g.user:
            user_id = g.user.get('id')
            
            # Immer den aktuellen Benutzer direkt aus der Datenbank laden, um die aktuelle Balance zu haben
            user_data_from_db = db_handler.get_user_by_id(user_id) # Renamed for clarity
            if not user_data_from_db: # Check if user object itself is None
                logger.warning(f"Benutzer {user_id} konnte nicht geladen werden für Easter Egg Einlösung (nicht in DB gefunden)")
                return jsonify({"success": False, "message": "Benutzer nicht gefunden"}), 404
                
            # Die tatsächliche aktuelle Balance aus der Datenbank holen
            current_balance = user_data_from_db.get('balance', 0) # Access balance directly
            print(f"Aktuelle Balance aus DB: {current_balance}")
            logger.info(f"Authenticated user: ID={user_id}, Current DB Balance={current_balance}")
        else:
            # Für Gast-Benutzer in der Session speichern
            guest_rewards = session.get('guest_rewards', {})
            current_balance = guest_rewards.get('balance', 0)
            logger.info(f"Guest user, session balance: {current_balance}")
        
        # Prüfen ob der Code bereits eingelöst wurde
        if user_id:
            # Vereinfachte Version für dieses Beispiel
            redeemed_codes = session.get(f"user_{user_id}_redeemed_codes", [])
            if code in redeemed_codes:
                logger.warning(f"Code {code} already redeemed by user {user_id}")
                return jsonify({
                    "success": False, 
                    "message": "Du hast diesen Code bereits eingelöst"
                })
        
        # Easter Egg Code Logik
        if code == "SECRETLAMBO":
            reward = 5000
            message = "Du hast einen virtuellen Lamborghini und 5000 Credits gewonnen!"
            reload = False
        elif code == "TOTHEMOON":
            reward = 1000
            message = "Deine Investitionen gehen TO THE MOON! +1000 Credits"
            reload = False
        elif code == "HODLGANG":
            reward = 2500
            message = "HODL! HODL! HODL! Du hast 2500 Credits für deine Diamond Hands erhalten!"
            reload = False
        elif code == "STONKS":
            # Spezielle Logik für den 4/20 Code
            today = datetime.now()
            if today.month == 4 and today.day == 20:
                reward = 4200
                message = "STONKS! Du hast den speziellen 4/20 Code gefunden! +4200 Credits"
            else:
                reward = 420
                message = "STONKS! Aber es ist nicht der richtige Tag für den vollen Bonus! +420 Credits"
            reload = False
        elif code == "1337":
            reward = 1337
            message = "Retro-Gaming-Modus aktiviert! +1337 Credits"
            reload = True  # Seite neu laden für den Retro-Modus
        else:
            logger.warning(f"Invalid easter egg code: {code}")
            return jsonify({
                "success": False, 
                "message": "Ungültiger Code"
            })
        
        # Belohnung anwenden - Wichtig: current_balance von der DB verwenden!
        new_balance = current_balance + reward
        logger.info(f"Reward applied: +{reward}, current balance: {current_balance}, new balance: {new_balance}")
        
        # Wenn wir einen authentifizierten Benutzer haben, aktualisiere die Datenbank
        if user_id:
            try:
                # Versuche zuerst, die update_user_balance Funktion zu verwenden
                update_result = db_handler.update_user_balance(user_id, new_balance)
                print(f"Update result: {update_result}")
                
                # Überprüfe, ob das Update funktioniert hat, indem wir die Balance nochmal abrufen
                user_data_after_update = db_handler.get_user_by_id(user_id) # Renamed for clarity
                if user_data_after_update: # Check if user object itself is not None
                    updated_balance = user_data_after_update.get('balance', current_balance) # Access balance directly
                    print(f"Balance nach Update: {updated_balance}")
                    
                    # Wenn die Balance nicht aktualisiert wurde, versuchen wir es mit einer direkten DB-Verbindung
                    if updated_balance != new_balance:
                        logger.warning(f"Balance wurde nicht korrekt aktualisiert: erwartet={new_balance}, ist={updated_balance}")
                        logger.warning("Versuche direktes Update mit SQL")
                        with transactions_handler.get_connection() as conn:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    UPDATE users SET balance = %s WHERE id = %s
                                """, (new_balance, user_id))
                                conn.commit()
                                logger.info(f"Direct database update for user {user_id} completed")
                else:
                    logger.error(f"Konnte Benutzerdaten nach Update nicht abrufen für Benutzer {user_id}")
                
                # Redeemed Code speichern
                redeemed_codes = session.get(f"user_{user_id}_redeemed_codes", [])
                redeemed_codes.append(code)
                session[f"user_{user_id}_redeemed_codes"] = redeemed_codes
                
                logger.info(f"Database updated for user {user_id}")
                
            except Exception as e:
                logger.exception(f"Konnte Easter Egg nicht in DB speichern: {str(e)}")
                # Trotzdem fortfahren und dem Benutzer die Belohnung anzeigen
        else:
            # Für Gast-Benutzer in der Session speichern
            guest_rewards = session.get('guest_rewards', {})
            guest_rewards['balance'] = new_balance
            guest_rewards['redeemed_codes'] = guest_rewards.get('redeemed_codes', []) + [code]
            session['guest_rewards'] = guest_rewards
            logger.info("Guest rewards updated in session")
        
        response_data = {
            "success": True,
            "message": message,
            "reload": reload,
            "reward": reward,
            "new_balance": new_balance,
            "debug": {
                "old_balance": current_balance,
                "reward": reward,
                "new_balance": new_balance
            }
        }
        logger.info(f"Successful response: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.exception(f"Easter Egg Fehler: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Easter Egg Fehler: {str(e)}",
            "error_details": str(e)
        }), 200  # 200 statt 500, um dem Frontend keine Fehler zu zeigen


@api_bp.route('/redeem-code', methods=['POST'])
@login_required
def api_redeem_code():
    """
    API-Endpunkt zum Einlösen von Promo- und Easter-Egg-Codes
    Benutzer muss authentifiziert sein (login_required)
    """
    data = request.get_json()
    if not data or 'code' not in data:
        return jsonify({"success": False, "message": "Bitte gib einen Code ein"}), 400
    
    code = data['code'].upper()
    user_id = g.user['id']
    
    # Versuche den User aus der Datenbank zu laden
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "message": "Benutzer nicht gefunden"}), 404
            
        # Prüfen, ob der Benutzer diesen Code bereits eingelöst hat
        existing_redemption = EasterEggRedemption.query.filter_by(
            user_id=user.id, code=code
        ).first()
        
        if existing_redemption:
            return jsonify({
                "success": False, 
                "message": "Du hast diesen Code bereits eingelöst"
            })
        
        # Code-Logik
        if code == "SECRETLAMBO":
            reward = 5000
            message = "Du hast einen virtuellen Lamborghini und 5000 Credits gewonnen!"
            reload = False
        elif code == "TOTHEMOON":
            reward = 1000
            message = "Deine Investitionen gehen TO THE MOON! +1000 Credits"
            reload = False
        elif code == "HODLGANG":
            reward = 2500
            message = "HODL! HODL! HODL! Du hast 2500 Credits für deine Diamond Hands erhalten!"
            reload = False
        elif code == "STONKS":
            # Spezielle Logik für den 4/20 Code
            today = datetime.now()
            if today.month == 4 and today.day == 20:
                reward = 4200
                message = "STONKS! Du hast den speziellen 4/20 Code gefunden! +4200 Credits"
            else:
                reward = 420
                message = "STONKS! Aber es ist nicht der richtige Tag für den vollen Bonus! +420 Credits"
            reload = False
        elif code == "1337":
            reward = 1337
            message = "Retro-Gaming-Modus aktiviert! +1337 Credits"
            reload = True  # Seite neu laden für den Retro-Modus
        else:
            return jsonify({
                "success": False, 
                "message": "Ungültiger Code"
            })
        
        # Code Einlösung speichern
        new_redemption = EasterEggRedemption(
            user_id=user.id,
            code=code,
            redeemed_at=datetime.now()
        )
        db.session.add(new_redemption)
        
        # Belohnung anwenden
        old_balance = user.balance if hasattr(user, 'balance') else 0
        if hasattr(user, 'balance'):
            user.balance += reward
        
        # Änderungen speichern
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": message,
            "reload": reload,
            "reward": reward,
            "new_balance": user.balance if hasattr(user, 'balance') else old_balance + reward
        })
    
    except Exception as e:
        try:
            db.session.rollback()
        except:
            pass
        
        logger.error(f"Fehler beim Einlösen des Codes: {str(e)}")
        
        return jsonify({
            "success": False,
            "message": "Ein Fehler ist aufgetreten. Bitte versuche es später noch einmal."
        }), 500


@api_bp.route('/health')
def api_health_check():
    """API-Endpunkt für den Gesundheitscheck der API"""
    return jsonify({"status": "ok", "message": "API is running."}), 200














