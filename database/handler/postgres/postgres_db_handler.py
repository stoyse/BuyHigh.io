import os
import psycopg2
import psycopg2.extras
import logging
from datetime import datetime
from rich import print
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus .env-Datei
load_dotenv()

logger = logging.getLogger(__name__)

# Stelle sicher, dass diese Funktion existiert und vor allen problematischen Importen definiert ist.
# Wenn sie bereits existiert, überprüfe auf zirkuläre Importe.
def app_api_request(api_name, endpoint, params=None, method='GET', data=None, headers=None):
    """
    Platzhalterfunktion für API-Anfragen.
    Implementiere hier die tatsächliche Logik für API-Anfragen.
    Diese Funktion wird von stock_data_api.py erwartet.
    """
    # Beispielimplementierung oder Verweis auf die tatsächliche Implementierung
    logger.info(f"app_api_request aufgerufen für: {api_name}, Endpoint: {endpoint}")
    # Hier sollte die Logik zum Ausführen der API-Anfrage stehen.
    # Zum Beispiel:
    # if api_name == "some_api":
    #     response = requests.request(method, endpoint, params=params, json=data, headers=headers)
    #     return response.json()
    return {"message": "app_api_request not fully implemented yet"}

# PostgreSQL-Verbindungsdetails aus .env
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = os.getenv('POSTGRES_PORT', '5432')
PG_DB = os.getenv('POSTGRES_DB', 'buyhigh')
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')

def get_db_connection():
    """Stellt eine Verbindung zur PostgreSQL-Datenbank her."""
    print('[bold blue]Connection to DB from Main Handler[/bold blue]')
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            dbname=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        conn.autocommit = False
        return conn
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Öffnen der PostgreSQL-Verbindung: {e}", exc_info=True)
        raise

def _parse_user_timestamps(user_row):
    if user_row is None:
        return None
    user_data = dict(user_row)
    for key in ['created_at', 'last_login']:
        val = user_data.get(key)
        if val and isinstance(val, str):
            try:
                user_data[key] = datetime.fromisoformat(val)
            except Exception:
                pass
    return user_data

def init_db():
    """Initialisiert den DB-Verbindungspool."""
    # add_analytics(event_type="init_db", details={"source": "postgres_db_handler:init_db"})
    conn = get_db_connection()
    try:
        logger.info("PostgreSQL: Verbindung erfolgreich hergestellt.")
    except psycopg2.Error as e:
        logger.error(f"Fehler während der DB-Initialisierung: {e}", exc_info=True)
        # add_analytics(event_type="init_db_error", details={"source": "postgres_db_handler:init_db", "error": str(e)})
    finally:
        conn.close()

def add_user(username, email, firebase_uid, provider='password'):
    # add_analytics(event_type="add_user_attempt", details={"email": email, "uid": firebase_uid, "source": "postgres_db_handler:add_user"})
    conn = get_db_connection()
    cur = conn.cursor()
    user_id_val = None
    try:
        cur.execute(
            "INSERT INTO users (username, email, firebase_uid, firebase_provider) VALUES (%s, %s, %s, %s) RETURNING id",
            (username, email, firebase_uid, provider)
        )
        user_id_val = cur.fetchone()[0]
        conn.commit()
        logger.info(f"Benutzer '{username}' erfolgreich mit ID {user_id_val} hinzugefügt.")
        # add_analytics(user_id=user_id_val, event_type="add_user_success", details={"email": email, "uid": firebase_uid, "user_id": user_id_val, "source": "postgres_db_handler:add_user"})
        return True
    except psycopg2.IntegrityError as e:
        conn.rollback()
        logger.error(f"Fehler beim Hinzufügen des Benutzers '{username}': {e}", exc_info=True)
        # add_analytics(event_type="add_user_integrity_error", details={"email": email, "error": str(e), "source": "postgres_db_handler:add_user"})
        return False
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"DB-Fehler beim Hinzufügen des Benutzers '{username}': {e}", exc_info=True)
        # add_analytics(event_type="add_user_db_error", details={"email": email, "error": str(e), "source": "postgres_db_handler:add_user"})
        return False
    finally:
        cur.close()
        conn.close()

def get_user_by_firebase_uid(firebase_uid, log_analytics_event=True):
    """
    Retrieves a user from the database by their Firebase UID.

    Args:
        firebase_uid: The Firebase UID of the user.
        log_analytics_event: Whether to log an analytics event for this action. Defaults to True.

    Returns:
        The user object if found, otherwise None.
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    user = None  # Initialize user to None
    try:
        cur.execute("SELECT * FROM users WHERE firebase_uid = %s", (firebase_uid,))
        user_row = cur.fetchone()
        if user_row:
            user = _parse_user_timestamps(user_row)
            if log_analytics_event:
                try:
                    # Call add_analytics with the primary user ID, event type, and details
                    # add_analytics(user_id=user['id'], event_type="get_user_by_firebase_uid", details={"firebase_uid": firebase_uid}, called_from_get_user=True)
                    pass # Analytics entfernt
                except Exception as e:
                    logger.error(f"Failed to log analytics event for get_user_by_firebase_uid (uid: {firebase_uid}): {e}")
        return user
    except psycopg2.Error as e:
        logger.error(f"Error searching for Firebase UID '{firebase_uid}': {e}", exc_info=True)
        # Avoid calling add_analytics here if it might lead to recursion during error handling
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_user_by_id(user_id):
    # add_analytics(user_id=user_id, event_type="get_user_by_id_call", details={"source_user_id": user_id, "source": "postgres_db_handler:get_user_by_id"})
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if user:
            return _parse_user_timestamps(user)
        return None
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Suchen nach Benutzer-ID '{user_id}': {e}", exc_info=True)
        # add_analytics(user_id=user_id, event_type="get_user_by_id_error", details={"source_user_id": user_id, "error": str(e), "source": "postgres_db_handler:get_user_by_id"})
        return None
    finally:
        cur.close()
        conn.close()

def get_user_by_username(username):
    # add_analytics(event_type="get_user_by_username_call", details={"username": username, "source": "postgres_db_handler:get_user_by_username"})
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if user:
            # add_analytics(user_id=user['id'], event_type="get_user_by_username_success", details={"username": username, "user_id": user['id'], "source": "postgres_db_handler:get_user_by_username"})
            return _parse_user_timestamps(user)
        else:
            # add_analytics(event_type="get_user_by_username_not_found", details={"username": username, "source": "postgres_db_handler:get_user_by_username"})
            return None
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Suchen nach Benutzername '{username}': {e}", exc_info=True)
        # add_analytics(event_type="get_user_by_username_error", details={"username": username, "error": str(e), "source": "postgres_db_handler:get_user_by_username"})
        return None
    finally:
        cur.close()
        conn.close()

def get_user_by_email(email: str):
    # add_analytics(event_type="get_user_by_email_call", details={"email": email, "source": "postgres_db_handler:get_user_by_email"})
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_row = cur.fetchone()
        if user_row:
            user = _parse_user_timestamps(user_row)
            # add_analytics(user_id=user['id'], event_type="get_user_by_email_success", details={"email": email, "user_id": user['id'], "source": "postgres_db_handler:get_user_by_email"})
            return user
        else:
            # add_analytics(event_type="get_user_by_email_not_found", details={"email": email, "source": "postgres_db_handler:get_user_by_email"})
            return None
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Suchen nach E-Mail '{email}': {e}", exc_info=True)
        # add_analytics(event_type="get_user_by_email_error", details={"email": email, "error": str(e), "source": "postgres_db_handler:get_user_by_email"})
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def update_user_firebase_uid(user_id: int, new_firebase_uid: str):
    """Updates the Firebase UID for a given user ID."""
    # add_analytics(user_id=user_id, event_type="update_firebase_uid_attempt", details={"target_user_id": user_id, "new_uid": new_firebase_uid, "source": "postgres_db_handler:update_user_firebase_uid"})
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET firebase_uid = %s WHERE id = %s",
            (new_firebase_uid, user_id)
        )
        conn.commit()
        if cur.rowcount > 0:
            logger.info(f"Firebase UID for user ID {user_id} updated to {new_firebase_uid}.")
            # add_analytics(user_id=user_id, event_type="update_firebase_uid_success", details={"target_user_id": user_id, "new_uid": new_firebase_uid, "source": "postgres_db_handler:update_user_firebase_uid"})
            return True
        else:
            logger.warning(f"No user found with ID {user_id} to update Firebase UID.")
            # add_analytics(user_id=user_id, event_type="update_firebase_uid_failed_not_found", details={"target_user_id": user_id, "source": "postgres_db_handler:update_user_firebase_uid"})
            return False
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"DB error updating Firebase UID for user ID {user_id}: {e}", exc_info=True)
        # add_analytics(user_id=user_id, event_type="update_firebase_uid_db_error", details={"target_user_id": user_id, "error": str(e), "source": "postgres_db_handler:update_user_firebase_uid"})
        return False
    finally:
        cur.close()
        conn.close()

def update_last_login(user_id_param):
    # add_analytics(user_id=user_id_param, event_type="update_last_login_call", details={"user_id_to_update": user_id_param, "source": "postgres_db_handler:update_last_login"})
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (user_id_param,))
        conn.commit()
        if cur.rowcount > 0:
            # add_analytics(user_id=user_id_param, event_type="update_last_login_success", details={"user_id_updated": user_id_param, "source": "postgres_db_handler:update_last_login"})
            return True
        else:
            # add_analytics(user_id=user_id_param, event_type="update_last_login_failed_no_row", details={"user_id_to_update": user_id_param, "source": "postgres_db_handler:update_last_login"})
            return False
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Aktualisieren der letzten Login-Zeit für Benutzer ID {user_id_param}: {e}", exc_info=True)
        # add_analytics(user_id=user_id_param, event_type="update_last_login_error", details={"user_id_to_update": user_id_param, "error": str(e), "source": "postgres_db_handler:update_last_login"})
        return False
    finally:
        cur.close()
        conn.close()

def delete_user(user_id_to_delete):
    # add_analytics(user_id=user_id_to_delete, event_type="delete_user_request", details={"user_id_to_delete": user_id_to_delete, "source": "postgres_db_handler:delete_user"})
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id_to_delete,))
        conn.commit()
        if cur.rowcount > 0:
            # add_analytics(user_id=user_id_to_delete, event_type="delete_user_success", details={"user_id_deleted": user_id_to_delete, "source": "postgres_db_handler:delete_user"})
            return True
        else:
            # add_analytics(user_id=user_id_to_delete, event_type="delete_user_failed_not_found", details={"user_id_to_delete": user_id_to_delete, "source": "postgres_db_handler:delete_user"})
            return False
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Löschen des Benutzers mit ID {user_id_to_delete}: {e}", exc_info=True)
        # add_analytics(user_id=user_id_to_delete, event_type="delete_user_error", details={"user_id_to_delete": user_id_to_delete, "error": str(e), "source": "postgres_db_handler:delete_user"})
        return False
    finally:
        cur.close()
        conn.close()

def get_all_users():
    # add_analytics(event_type="get_all_users_call", details={"source": "postgres_db_handler:get_all_users"})
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT id, username, email FROM users ORDER BY username")
        users = [dict(row) for row in cur.fetchall()]
        # add_analytics(event_type="get_all_users_success", details={"count": len(users), "source": "postgres_db_handler:get_all_users"})
        return users
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen aller Benutzer: {e}", exc_info=True)
        # add_analytics(event_type="get_all_users_error", details={"error": str(e), "source": "postgres_db_handler:get_all_users"})
        return []
    finally:
        cur.close()
        conn.close()

def get_all_profiles():
    # add_analytics(event_type="get_all_profiles_call", details={"source": "postgres_db_handler:get_all_profiles"})
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM users ORDER BY id")
        profiles = [dict(row) for row in cur.fetchall()]
        # add_analytics(event_type="get_all_profiles_success", details={"count": len(profiles), "source": "postgres_db_handler:get_all_profiles"})
        return profiles
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen aller Profile: {e}", exc_info=True)
        # add_analytics(event_type="get_all_profiles_error", details={"error": str(e), "source": "postgres_db_handler:get_all_profiles"})
        return []
    finally:
        cur.close()
        conn.close()




def create_asset(symbol, name, asset_type, exchange=None, currency="USD", 
                sector=None, industry=None, logo_url=None, description=None, default_price=None):
    """
    Erstellt ein neues Asset in der Datenbank.
    """
    # add_analytics(event_type="create_asset_attempt", details={"symbol": symbol, "type": asset_type, "source": "postgres_db_handler:create_asset"})
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO assets 
                    (symbol, name, asset_type, exchange, currency, sector, industry, logo_url, description, default_price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (symbol, name, asset_type, exchange, currency, sector, industry, logo_url, description, default_price))
                conn.commit()
                # add_analytics(event_type="create_asset_success", details={"symbol": symbol, "source": "postgres_db_handler:create_asset"})
                return True
    except Exception as e:
        logger.error(f"Fehler beim Erstellen eines Assets: {e}")
        # add_analytics(event_type="create_asset_error", details={"symbol": symbol, "error": str(e), "source": "postgres_db_handler:create_asset"})
        return False

def get_user_level(user_id_param):
    # add_analytics(user_id=user_id_param, event_type="get_user_level_call", details={"user_id_query": user_id_param, "source": "postgres_db_handler:get_user_level"})
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT level FROM users WHERE id = %s", (user_id_param,))
        level = cur.fetchone()
        if level:
            # add_analytics(user_id=user_id_param, event_type="get_user_level_success", details={"user_id_found": user_id_param, "level": level[0], "source": "postgres_db_handler:get_user_level"})
            return level[0]
        # add_analytics(user_id=user_id_param, event_type="get_user_level_not_found", details={"user_id_query": user_id_param, "source": "postgres_db_handler:get_user_level"})
        return None
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen des Levels für Benutzer ID {user_id_param}: {e}", exc_info=True)
        # add_analytics(user_id=user_id_param, event_type="get_user_level_error", details={"user_id_query": user_id_param, "error": str(e), "source": "postgres_db_handler:get_user_level"})
        return None
    finally:
        cur.close()
        conn.close()

def get_xp_levels():
    # add_analytics(event_type="get_xp_levels_call", details={"source": "postgres_db_handler:get_xp_levels"})
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM xp_levels ORDER BY level")
        levels = cur.fetchall()
        # add_analytics(event_type="get_xp_levels_success", details={"count": len(levels), "source": "postgres_db_handler:get_xp_levels"})
        return levels
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen der XP-Levels: {e}", exc_info=True)
        # add_analytics(event_type="get_xp_levels_error", details={"error": str(e), "source": "postgres_db_handler:get_xp_levels"})
        return []
    finally:
        cur.close()
        conn.close()

def get_xp_gains(action):
    # add_analytics(event_type="get_xp_gains_call", details={"action": action, "source": "postgres_db_handler:get_xp_gains"})
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT xp_amount FROM xp_gains WHERE action = %s", (action,))
        xp_gain = cur.fetchone()
        if xp_gain:
            # add_analytics(event_type="get_xp_gains_success", details={"action": action, "xp_amount": xp_gain[0], "source": "postgres_db_handler:get_xp_gains"})
            return xp_gain[0]
        # add_analytics(event_type="get_xp_gains_not_found", details={"action": action, "source": "postgres_db_handler:get_xp_gains"})
        return None
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen von XP-Gewinnen für Aktion '{action}': {e}", exc_info=True)
        # add_analytics(event_type="get_xp_gains_error", details={"action": action, "error": str(e), "source": "postgres_db_handler:get_xp_gains"})
        return None
    finally:
        cur.close()
        conn.close()

def manage_user_xp(action, user_id_param, quantity):
    # add_analytics(user_id=user_id_param, event_type="manage_user_xp_start", details={"action": action, "user_id_target": user_id_param, "quantity": quantity, "source": "postgres_db_handler:manage_user_xp"})
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        xp_to_add = get_xp_gains(action)
        if xp_to_add is None:
            logger.warning(f"Keine XP-Definition für Aktion '{action}' gefunden.")
            # add_analytics(user_id=user_id_param, event_type="manage_user_xp_no_xp_def", details={"action": action, "source": "postgres_db_handler:manage_user_xp"})
            return False

        cur.execute("UPDATE users SET xp = xp + %s WHERE id = %s", (xp_to_add, user_id_param))
        conn.commit()
        logger.info(f"{xp_to_add} XP für Aktion '{action}' zu Benutzer {user_id_param} hinzugefügt.")
        # add_analytics(user_id=user_id_param, event_type="manage_user_xp_success", details={"action": action, "xp_added": xp_to_add, "source": "postgres_db_handler:manage_user_xp"})
        
        check_user_level(user_id_param, get_user_xp(user_id_param))
        return True
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Verwalten von XP für Benutzer {user_id_param}, Aktion '{action}': {e}", exc_info=True)
        # add_analytics(user_id=user_id_param, event_type="manage_user_xp_error", details={"action": action, "error": str(e), "source": "postgres_db_handler:manage_user_xp"})
        return False
    finally:
        cur.close()
        conn.close()

def get_user_xp(user_id):
    # add_analytics(user_id=user_id, event_type="get_user_xp", details={"source": "postgres_db_handler:get_user_xp", "user_id": user_id})
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT xp FROM users WHERE id = %s", (user_id,))
        xp = cur.fetchone()
        if xp:
            return xp[0]
        return 0
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen von XP für Benutzer ID {user_id}: {e}", exc_info=True)
        # add_analytics(user_id=user_id, event_type="get_user_xp_error", details={"source": "postgres_db_handler:get_user_xp", "user_id": user_id, "error": str(e)})
        return 0
    finally:
        cur.close()
        conn.close()

def check_user_level(user_id, current_xp):
    # add_analytics(user_id=user_id, event_type="check_user_level_start", details={"source": "postgres_db_handler:check_user_level", "user_id": user_id, "current_xp": current_xp})
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT level FROM users WHERE id = %s", (user_id,))
        user_current_level_row = cur.fetchone()
        if not user_current_level_row:
            logger.warning(f"Benutzer {user_id} nicht gefunden für Level-Check.")
            return

        user_current_level = user_current_level_row['level']
        
        cur.execute("SELECT level, xp_required FROM xp_levels ORDER BY level DESC")
        levels_data = cur.fetchall()
        
        new_level = user_current_level
        for level_info in levels_data:
            if current_xp >= level_info['xp_required']:
                new_level = level_info['level']
                break

        if new_level != user_current_level:
            cur.execute("UPDATE users SET level = %s WHERE id = %s", (new_level, user_id))
            conn.commit()
            logger.info(f"Benutzer {user_id} Level aktualisiert von {user_current_level} auf {new_level}.")
            # add_analytics(user_id=user_id, event_type="user_level_up", details={"source": "postgres_db_handler:check_user_level", "old_level": user_current_level, "new_level": new_level})
        else:
            # add_analytics(user_id=user_id, event_type="user_level_no_change", details={"source": "postgres_db_handler:check_user_level", "level": user_current_level})
            pass # Analytics entfernt

    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Überprüfen/Aktualisieren des Benutzerlevels für ID {user_id}: {e}", exc_info=True)
        # add_analytics(user_id=user_id, event_type="check_user_level_error", details={"source": "postgres_db_handler:check_user_level", "error": str(e)})
    finally:
        cur.close()
        conn.close()

# def add_analytics(user_id: int = None, event_type: str = None, details: dict = None, called_from_get_user: bool = False):
#     """
#     Adds an analytics event to the database.
#
#     Args:
#         user_id: The ID of the user associated with the event. Can be None for system events.
#         event_type: The type of event (e.g., "login", "view_page"). This will be stored in the 'action' column.
#         details: Optional dictionary for additional event details.
#                  If it contains a 'source' key, its value will be stored in 'source_details'.
#                  The (remaining) dictionary will be stored as JSONB in the 'details' column.
#         called_from_get_user: Internal flag to prevent recursion with get_user_by_firebase_uid.
#     """
#     if event_type is None:
#         logger.warning("add_analytics called with no event_type. Skipping.")
#         return
#
#     conn = None
#     cur = None
#     actual_user_id = user_id
#
#     # Prepare details for DB insertion
#     db_details_payload = details.copy() if details else {}
#     source_details_val = db_details_payload.pop('source', None) if db_details_payload else None
#
#     try:
#         conn = get_db_connection()
#         cur = conn.cursor()
#
#         # The 'event_type' parameter is used for the 'action' column.
#         # 'source_details_val' is extracted from 'details' dict's 'source' key.
#         # The remaining 'db_details_payload' is stored in the 'details' JSONB column.
#         cur.execute(
#             "INSERT INTO analytics (user_id, action, source_details, details) VALUES (%s, %s, %s, %s)",
#             (actual_user_id, event_type, source_details_val, psycopg2.extras.Json(db_details_payload) if db_details_payload else None)
#         )
#         conn.commit()
#         logger.info(f"Analytics event added: {event_type} for user_id {actual_user_id or 'System'}")
#
#     except psycopg2.Error as e:
#         if conn:
#             conn.rollback()
#         # Log still refers to event_type as it's the input parameter name
#         logger.error(f"DB error adding analytics event (user_id: {actual_user_id}, event: {event_type}): {e}", exc_info=True)
#     except Exception as e:
#         if conn:
#             conn.rollback()
#         logger.error(f"Non-DB error adding analytics event (user_id: {actual_user_id}, event: {event_type}): {e}", exc_info=True)
#     finally:
#         if cur:
#             cur.close()
#         if conn:
#             conn.close()

def update_user_balance(user_id, new_balance):
    """
    Aktualisiert die Balance eines Benutzers in der Datenbank.
    
    Args:
        user_id (int): Die ID des Benutzers
        new_balance (float): Der neue Kontostand
        
    Returns:
        bool: True, wenn Update erfolgreich, False sonst
    """
    # add_analytics(user_id=user_id, event_type="update_user_balance", details={"user_id": user_id, "new_balance": new_balance, "source": "postgres_db_handler:update_user_balance"})
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        logger.info(f"Updating balance for user {user_id} to {new_balance}")
        cur.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user_id))
        conn.commit()
        affected_rows = cur.rowcount
        logger.info(f"Balance update affected {affected_rows} rows")
        return affected_rows > 0
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Aktualisieren der Balance für Benutzer ID {user_id}: {e}", exc_info=True)
        # add_analytics(user_id=user_id, event_type="update_user_balance_error", details={"user_id": user_id, "error": str(e), "source": "postgres_db_handler:update_user_balance"})
        return False
    finally:
        cur.close()
        conn.close()

def get_all_analytics():
    """
    Gibt alle Analyse-Metriken zurück.
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM analytics ORDER BY timestamp DESC")
        analytics = [dict(row) for row in cur.fetchall()]
        return analytics
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen aller Analysen: {e}", exc_info=True)
        return []
    finally:
        cur.close()
        conn.close()