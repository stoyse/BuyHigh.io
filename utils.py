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
        # Attempt to load user from session if not already loaded
        if not hasattr(g, 'user') or g.user is None:
            user_id = session.get('user_id')
            if user_id:
                try:
                    user = get_user_by_id(user_id)
                    if user:
                        g.user = user
                        logger.debug(f"User {user_id} loaded into g.user from session.")
                    else:
                        logger.warning(f"User ID {user_id} from session not found in DB.")
                        session.clear()
                        g.user = None
                except Exception as e:
                    logger.error(f"Error loading user {user_id} from DB in login_required: {e}")
                    g.user = None
            else:
                g.user = None

        # Add analytics for the check itself
        user_id_for_analytics = g.user.get('id') if hasattr(g, 'user') and g.user else None
        add_analytics(user_id_for_analytics, "login_required_check", f"utils:login_required:{view.__name__}")

        if g.user is None:
            # If the request is for an API endpoint, return JSON response
            if request.blueprint == 'api' or (hasattr(request, 'accept_mimetypes') and request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html):
                logger.warning(f"Unauthorized API access attempt to {request.path}. g.user is None.")
                return jsonify({"success": False, "message": "Authentication required. Please log in."}), 401
            # Otherwise, redirect to login page
            add_analytics(None, "login_required_redirect", f"utils:login_required:{view.__name__}")
            flash("You need to be logged in to view this page.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        
        add_analytics(user_id_for_analytics, "login_required_success", f"utils:login_required:{view.__name__}")
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
    if hasattr(g, 'user') and g.user is not None:
        return # Benutzer bereits geladen

    user_id = session.get('user_id')
    if user_id:
        try:
            user = get_user_by_id(user_id)
            if user:
                g.user = user
                logger.debug(f"User {user_id} loaded into g.user via load_user_from_session.")
            else:
                g.user = None
                session.clear() # Ungültige Session löschen
                logger.warning(f"User ID {user_id} from session not found in DB (load_user_from_session).")
        except Exception as e:
            logger.error(f"Error loading user {user_id} from DB in load_user_from_session: {e}")
            g.user = None
    else:
        g.user = None

def setup_before_request(app):
    """Registriert die `load_user_from_session` Funktion, um vor jeder Anfrage ausgeführt zu werden."""
    @app.before_request
    def before_request_callback():
        load_user_from_session()
        # Log session data for debugging
        # logger.debug(f"Session at start of request to {request.path}: {dict(session)}")
        # logger.debug(f"g.user at start of request to {request.path}: {g.user.get('id') if hasattr(g, 'user') and g.user else 'None'}")
