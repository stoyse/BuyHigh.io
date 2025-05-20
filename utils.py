import functools
from flask import g, flash, redirect, url_for, request, session, jsonify, current_app
from rich import print
from database.handler.postgres.postgres_db_handler import get_db_connection, add_analytics, get_user_by_id
import random
import datetime
import logging

logger = logging.getLogger(__name__)

# Decorator for routes that require login
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        # Verlasse dich darauf, dass load_user_from_session (via app.before_request) g.user gesetzt hat.
        if not hasattr(g, 'user') or g.user is None:
            # Loggen, dass g.user hier None ist, nachdem load_user_from_session gelaufen sein sollte.
            logger.warning(f"Access to {request.path} denied. g.user is None after before_request processing. session.get('user_id'): {session.get('user_id')}")
            
            if request.blueprint == 'api' or \
               (hasattr(request, 'accept_mimetypes') and \
                request.accept_mimetypes.accept_json and \
                not request.accept_mimetypes.accept_html):
                logger.warning(f"Unauthorized API access attempt to {request.path}. Responding with 401 JSON.")
                return jsonify({"success": False, "message": "Authentication required. Please log in."}), 401
            else:
                logger.info(f"User not logged in for non-API path {request.path}, redirecting to login page.")
                return redirect(url_for('auth.login', next=request.url))
        
        logger.debug(f"Accessing {request.path}. User in g: {g.user.get('id') if g.user else 'None'}")
        return view(**kwargs)
    return wrapped_view

# Decorator for routes that require developer access
def dev_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        user_id_for_analytics = g.user.get('id') if hasattr(g, 'user') and g.user else None
        add_analytics(user_id_for_analytics, "dev_required_check", f"utils:dev_required:{view.__name__}")

        if g.user is None:
            flash("You need to be logged in to access this page.", "warning")
            return redirect(url_for('auth.login', next=request.path))

        is_developer = False

        # 1. Prüfe direkt im g.user-Objekt auf das Feld 'is_dev'
        if isinstance(g.user, dict) and g.user.get('is_dev'):
            is_developer = True
        elif hasattr(g.user, 'is_dev') and getattr(g.user, 'is_dev'):
            is_developer = True

        # 2. Falls nicht, prüfe in der developers-Tabelle (DB)
        if not is_developer:
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        # Wichtig: user_id als INT vergleichen, nicht als STRING!
                        cur.execute("SELECT 1 FROM developers WHERE user_id = %s", (int(g.user['id']),))
                        add_analytics(g.user.get('id') if g.user else None, "dev_required_db_check", "utils")
                        row = cur.fetchone()
                        print(f'[dark orange3]SQL: SELECT 1 FROM developers WHERE user_id = {g.user["id"]} -> {row}[/]')
                        is_developer = row is not None
            except Exception as e:
                print(f'[red]Fehler bei dev_required DB-Check: {e}[/]')

        if not is_developer:
            add_analytics(user_id_for_analytics, "dev_required_fail", f"utils:dev_required:{view.__name__}")
            flash("You don't have developer access to this page.", "error")
            return redirect(url_for('main.index'))

        add_analytics(user_id_for_analytics, "dev_required_success", f"utils:dev_required:{view.__name__}")
        return view(**kwargs)
    return wrapped_view

def process_easter_egg(code):
    """Process an easter egg code and award credits to the user if valid."""
    if not g.user:
        return False, "You need to be logged in to claim easter eggs!"
    
    valid_codes = {
        "HODLGANG": {"credits": 100, "message": "HODL GANG! 💎 +100 Credits for your diamond hands!"},
        "BUYHIGH": {"credits": 250, "message": "Buy High, Sell Low! That's the spirit! +250 Credits"},
        "DIAMONDHANDS": {"credits": 500, "message": "Diamond hands rewarded! +500 Credits"},
        "TOTHEMOON": {"credits": 420, "message": "🚀 To the moon! +420 Credits"},
        "SELLLOW": {"credits": 200, "message": "Perfect timing to sell low! +200 Credits"},
        "STONKS": {"credits": 150, "message": "STONKS only go up! +150 Credits"},
        "APESSTRONG": {"credits": 300, "message": "Apes together strong! +300 Credits"},
        "SECRETLAMBO": {"credits": 1000, "message": "🏎️ Lambos unlocked! +1000 Credits"},
    }
    
    # Check if it's a valid code
    if code.upper() not in valid_codes:
        return False, "Invalid easter egg code!"
    
    code_data = valid_codes[code.upper()]
    user_id = g.user.get('id')
    
    try:
        # Check if this code has already been redeemed by this user
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if this code has been redeemed already
        cur.execute("SELECT id FROM easter_eggs_redeemed WHERE user_id = %s AND code = %s", 
                    (user_id, code.upper()))
        if cur.fetchone():
            return False, "You've already redeemed this easter egg!"
            
        # Award credits to the user
        cur.execute("UPDATE users SET balance = balance + %s WHERE id = %s", 
                   (code_data["credits"], user_id))
        
        # Record that this code has been redeemed
        cur.execute("INSERT INTO easter_eggs_redeemed (user_id, code, redeemed_at) VALUES (%s, %s, %s)",
                   (user_id, code.upper(), datetime.datetime.now()))
        
        conn.commit()
        add_analytics(user_id, f"easter_egg_redeemed_{code.upper()}", "utils:process_easter_egg")
        
        return True, code_data["message"]
    except Exception as e:
        return False, f"Error processing easter egg: {str(e)}"

def load_user_from_session():
    """Lädt den Benutzer aus der Session in g.user, falls vorhanden."""
    # Log the entire session dictionary at the beginning of the function
    logger.debug(f"load_user_from_session: Current session state for path {request.path}: {dict(session)}")

    if hasattr(g, 'user') and g.user is not None:
        logger.debug(f"User already loaded in g for request {request.path}. User ID: {g.user.get('id')}")
        return

    user_id_from_session = session.get('user_id')
    # Aktualisierte Log-Zeile, um den Pfad einzuschließen
    logger.debug(f"load_user_from_session: Attempting to load user. session.get('user_id') = {user_id_from_session} for path {request.path}")

    if user_id_from_session:
        try:
            # Stelle sicher, dass db_handler.get_user_by_id die Benutzerdaten als Dictionary zurückgibt
            user = get_user_by_id(user_id_from_session)
            if user:
                g.user = user  # Speichert das gesamte Benutzerobjekt (Dictionary)
                logger.info(f"User {user_id_from_session} loaded into g.user from session for path {request.path}. User data: {g.user}")
            else:
                logger.warning(f"User ID {user_id_from_session} from session not found in DB (called from load_user_from_session). Clearing session.")
                session.clear()  # Ungültige Session löschen
                g.user = None
        except Exception as e:
            logger.error(f"Error loading user {user_id_from_session} from DB in load_user_from_session: {e}", exc_info=True)
            g.user = None
    else:
        logger.debug(f"No user_id found in session (called from load_user_from_session for path {request.path}). g.user set to None.")
        g.user = None

def setup_before_request(app):
    """Registriert die `load_user_from_session` Funktion, um vor jeder Anfrage ausgeführt zu werden."""
    @app.before_request
    def before_request_callback():
        # Loggen des Session-Inhalts vor dem Laden des Benutzers für Debugging-Zwecke
        # logger.debug(f"Session state at start of before_request_callback for {request.path}: {dict(session)}")
        load_user_from_session()
        # logger.debug(f"g.user state after load_user_from_session for {request.path}: {g.user.get('id') if hasattr(g, 'user') and g.user else 'None'}")
