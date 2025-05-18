import os
import psycopg2
import psycopg2.extras
import logging
from datetime import datetime
from rich import print

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
    add_analytics(None, "get_db_connection", "postgres_db_handler:get_db_connection")
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
        add_analytics(None, "get_db_connection_error", f"postgres_db_handler:get_db_connection:error={e}")
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
    add_analytics(None, "init_db", "postgres_db_handler:init_db")
    conn = get_db_connection()
    try:
        logger.info("PostgreSQL: Verbindung erfolgreich hergestellt.")
    except psycopg2.Error as e:
        logger.error(f"Fehler während der DB-Initialisierung: {e}", exc_info=True)
        add_analytics(None, "init_db_error", f"postgres_db_handler:init_db:error={e}")
    finally:
        conn.close()

def add_user(username, email, firebase_uid, provider='password'):
    add_analytics(None, "add_user_attempt", f"postgres_db_handler:add_user:email={email},uid={firebase_uid}")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, email, firebase_uid, firebase_provider) VALUES (%s, %s, %s, %s) RETURNING id",
            (username, email, firebase_uid, provider)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"Benutzer '{username}' erfolgreich mit ID {user_id} hinzugefügt.")
        add_analytics(user_id, "add_user_success", f"postgres_db_handler:add_user:email={email},uid={firebase_uid}")
        return True
    except psycopg2.IntegrityError as e:
        conn.rollback()
        logger.error(f"Fehler beim Hinzufügen des Benutzers '{username}': {e}", exc_info=True)
        add_analytics(None, "add_user_integrity_error", f"postgres_db_handler:add_user:email={email},error={e}")
        return False
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"DB-Fehler beim Hinzufügen des Benutzers '{username}': {e}", exc_info=True)
        add_analytics(None, "add_user_db_error", f"postgres_db_handler:add_user:email={email},error={e}")
        return False
    finally:
        cur.close()
        conn.close()

def get_user_by_firebase_uid(firebase_uid):
    add_analytics(None, "get_user_by_firebase_uid", f"postgres_db_handler:get_user_by_firebase_uid:uid={firebase_uid}")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM users WHERE firebase_uid = %s", (firebase_uid,))
        user = cur.fetchone()
        if user:
            return _parse_user_timestamps(user)
        return None
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Suchen nach Firebase UID '{firebase_uid}': {e}", exc_info=True)
        add_analytics(None, "get_user_by_firebase_uid_error", f"postgres_db_handler:get_user_by_firebase_uid:uid={firebase_uid},error={e}")
        return None
    finally:
        cur.close()
        conn.close()

def get_user_by_id(user_id):
    add_analytics(user_id, "get_user_by_id", f"postgres_db_handler:get_user_by_id:user_id={user_id}")
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
        add_analytics(user_id, "get_user_by_id_error", f"postgres_db_handler:get_user_by_id:user_id={user_id},error={e}")
        return None
    finally:
        cur.close()
        conn.close()

def get_user_by_username(username):
    add_analytics(None, "get_user_by_username", f"postgres_db_handler:get_user_by_username:username={username}")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if user:
            return _parse_user_timestamps(user)
        return None
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Suchen nach Benutzername '{username}': {e}", exc_info=True)
        add_analytics(None, "get_user_by_username_error", f"postgres_db_handler:get_user_by_username:username={username},error={e}")
        return None
    finally:
        cur.close()
        conn.close()

def get_user_by_email(email):
    add_analytics(None, "get_user_by_email", f"postgres_db_handler:get_user_by_email:email={email}")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if user:
            return _parse_user_timestamps(user)
        return None
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Suchen nach E-Mail '{email}': {e}", exc_info=True)
        add_analytics(None, "get_user_by_email_error", f"postgres_db_handler:get_user_by_email:email={email},error={e}")
        return None
    finally:
        cur.close()
        conn.close()

def update_last_login(user_id):
    add_analytics(user_id, "update_last_login", f"postgres_db_handler:update_last_login:user_id={user_id}")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (user_id,))
        conn.commit()
        return cur.rowcount > 0
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Aktualisieren der letzten Login-Zeit für Benutzer ID {user_id}: {e}", exc_info=True)
        add_analytics(user_id, "update_last_login_error", f"postgres_db_handler:update_last_login:user_id={user_id},error={e}")
        return False
    finally:
        cur.close()
        conn.close()

def update_firebase_uid(user_id, firebase_uid):
    add_analytics(user_id, "update_firebase_uid", f"postgres_db_handler:update_firebase_uid:user_id={user_id},uid={firebase_uid}")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET firebase_uid = %s WHERE id = %s", (firebase_uid, user_id))
        conn.commit()
        return cur.rowcount > 0
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Aktualisieren der Firebase UID für Benutzer ID {user_id}: {e}", exc_info=True)
        add_analytics(user_id, "update_firebase_uid_error", f"postgres_db_handler:update_firebase_uid:user_id={user_id},error={e}")
        return False
    finally:
        cur.close()
        conn.close()

def update_user_theme(user_id, theme):
    add_analytics(user_id, "update_user_theme", f"postgres_db_handler:update_user_theme:user_id={user_id},theme={theme}")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET theme = %s WHERE id = %s", (theme, user_id))
        conn.commit()
        return cur.rowcount
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Aktualisieren des Themes für Benutzer ID {user_id}: {e}", exc_info=True)
        add_analytics(user_id, "update_user_theme_error", f"postgres_db_handler:update_user_theme:user_id={user_id},error={e}")
        return 0
    finally:
        cur.close()
        conn.close()

def delete_user(user_id):
    add_analytics(user_id, "delete_user_request", f"postgres_db_handler:delete_user:user_id_to_delete={user_id}")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        add_analytics(user_id, "delete_user_success", f"postgres_db_handler:delete_user:user_id_deleted={user_id}")
        return cur.rowcount > 0
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Löschen des Benutzers mit ID {user_id}: {e}", exc_info=True)
        add_analytics(user_id, "delete_user_error", f"postgres_db_handler:delete_user:user_id_to_delete={user_id},error={e}")
        return False
    finally:
        cur.close()
        conn.close()

def get_all_users():
    add_analytics(None, "get_all_users", "postgres_db_handler:get_all_users")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT id, username, email FROM users ORDER BY username")
        users = [dict(row) for row in cur.fetchall()]
        return users
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen aller Benutzer: {e}", exc_info=True)
        add_analytics(None, "get_all_users_error", f"postgres_db_handler:get_all_users:error={e}")
        return []
    finally:
        cur.close()
        conn.close()

def get_all_profiles():
    add_analytics(None, "get_all_profiles", "postgres_db_handler:get_all_profiles")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM users ORDER BY id")
        profiles = [dict(row) for row in cur.fetchall()]
        return profiles
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen aller Profile: {e}", exc_info=True)
        add_analytics(None, "get_all_profiles_error", f"postgres_db_handler:get_all_profiles:error={e}")
        return []
    finally:
        cur.close()
        conn.close()

def create_asset(symbol, name, asset_type, exchange=None, currency="USD", 
                sector=None, industry=None, logo_url=None, description=None, default_price=None):
    """
    Erstellt ein neues Asset in der Datenbank.
    """
    add_analytics(None, "create_asset_attempt", f"postgres_db_handler:create_asset:symbol={symbol},type={asset_type}")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO assets 
                    (symbol, name, asset_type, exchange, currency, sector, industry, logo_url, description, default_price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (symbol, name, asset_type, exchange, currency, sector, industry, logo_url, description, default_price))
                conn.commit()
                add_analytics(None, "create_asset_success", f"postgres_db_handler:create_asset:symbol={symbol}")
                return True
    except Exception as e:
        logger.error(f"Fehler beim Erstellen eines Assets: {e}")
        add_analytics(None, "create_asset_error", f"postgres_db_handler:create_asset:symbol={symbol},error={e}")
        return False

def get_user_level(user_id):
    """
    Gibt den Level eines Benutzers zurück.
    """
    add_analytics(user_id, "get_user_level", f"postgres_db_handler:get_user_level:user_id={user_id}")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT level FROM users WHERE id = %s", (user_id,))
        level = cur.fetchone()
        if level:
            return level[0]
        return None
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen des Levels für Benutzer ID {user_id}: {e}", exc_info=True)
        add_analytics(user_id, "get_user_level_error", f"postgres_db_handler:get_user_level:user_id={user_id},error={e}")
        return None
    finally:
        cur.close()
        conn.close()

def get_xp_levels():
    """
    Gibt die XP-Level zurück.
    """
    add_analytics(None, "get_xp_levels", "postgres_db_handler:get_xp_levels")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM xp_levels ORDER BY level")
        levels = cur.fetchall()
        return levels
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen der XP-Levels: {e}", exc_info=True)
        add_analytics(None, "get_xp_levels_error", f"postgres_db_handler:get_xp_levels:error={e}")
        return []
    finally:
        cur.close()
        conn.close()

def get_xp_gains(action):
    """
    Gibt die XP-Gewinne für eine bestimmte Aktion zurück.
    """
    add_analytics(None, "get_xp_gains", f"postgres_db_handler:get_xp_gains:action={action}")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT xp_amount FROM xp_gains WHERE action = %s", (action,))
        xp_gain = cur.fetchone()
        if xp_gain:
            return xp_gain[0]
        return None
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen von XP-Gewinnen für Aktion '{action}': {e}", exc_info=True)
        add_analytics(None, "get_xp_gains_error", f"postgres_db_handler:get_xp_gains:action={action},error={e}")
        return None
    finally:
        cur.close()
        conn.close()

def manage_user_xp(action, user_id, quantity):
    """
    Verwalte die XP eines Benutzers basierend auf der Aktion.
    """
    add_analytics(user_id, "manage_user_xp_start", f"postgres_db_handler:manage_user_xp:action={action},user={user_id},qty={quantity}")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        xp_to_add = get_xp_gains(action)
        if xp_to_add is None:
            logger.warning(f"Keine XP-Definition für Aktion '{action}' gefunden.")
            add_analytics(user_id, "manage_user_xp_no_xp_def", f"postgres_db_handler:manage_user_xp:action={action}")
            return False

        cur.execute("UPDATE users SET xp = xp + %s WHERE id = %s", (xp_to_add, user_id))
        conn.commit()
        logger.info(f"{xp_to_add} XP für Aktion '{action}' zu Benutzer {user_id} hinzugefügt.")
        add_analytics(user_id, "manage_user_xp_success", f"postgres_db_handler:manage_user_xp:action={action},xp_added={xp_to_add}")
        
        check_user_level(user_id, get_user_xp(user_id))
        return True
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Verwalten von XP für Benutzer {user_id}, Aktion '{action}': {e}", exc_info=True)
        add_analytics(user_id, "manage_user_xp_error", f"postgres_db_handler:manage_user_xp:action={action},error={e}")
        return False
    finally:
        cur.close()
        conn.close()

def get_user_xp(user_id):
    add_analytics(user_id, "get_user_xp", f"postgres_db_handler:get_user_xp:user_id={user_id}")
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
        add_analytics(user_id, "get_user_xp_error", f"postgres_db_handler:get_user_xp:user_id={user_id},error={e}")
        return 0
    finally:
        cur.close()
        conn.close()

def check_user_level(user_id, current_xp):
    add_analytics(user_id, "check_user_level_start", f"postgres_db_handler:check_user_level:user_id={user_id},current_xp={current_xp}")
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
            add_analytics(user_id, "user_level_up", f"postgres_db_handler:check_user_level:old={user_current_level},new={new_level}")
        else:
            add_analytics(user_id, "user_level_no_change", f"postgres_db_handler:check_user_level:level={user_current_level}")

    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Überprüfen/Aktualisieren des Benutzerlevels für ID {user_id}: {e}", exc_info=True)
        add_analytics(user_id, "check_user_level_error", f"postgres_db_handler:check_user_level:error={e}")
    finally:
        cur.close()
        conn.close()

def add_analytics(user_id, action, source_details):
    """
    Protokolliert eine Analyse-Metrik in der Datenbank.
    """
    if action == "get_db_connection" and "add_analytics" in source_details:
         print(f"Analytics (skipped to prevent recursion): user_id={user_id}, action='{action}', source='{source_details}'")
         return

    conn = None
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO analytics (user_id, action, source_details) VALUES (%s, %s, %s)",
                (user_id, action, source_details)
            )
    except psycopg2.Error as e:
        print(f"DB-Fehler in add_analytics: {e}")
    except Exception as e:
        print(f"Allgemeiner Fehler in add_analytics: {e}")
    finally:
        if conn:
            conn.close()

def update_user_balance(user_id, new_balance):
    """
    Aktualisiert die Balance eines Benutzers in der Datenbank.
    
    Args:
        user_id (int): Die ID des Benutzers
        new_balance (float): Der neue Kontostand
        
    Returns:
        bool: True, wenn Update erfolgreich, False sonst
    """
    add_analytics(user_id, "update_user_balance", f"postgres_db_handler:update_user_balance:user_id={user_id},new_balance={new_balance}")
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
        add_analytics(user_id, "update_user_balance_error", f"postgres_db_handler:update_user_balance:user_id={user_id},error={e}")
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