import os  # Dieser Import fehlte
import psycopg2
import psycopg2.extras
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# PostgreSQL-Verbindungsdetails aus .env
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = os.getenv('POSTGRES_PORT', '5432')
PG_DB = os.getenv('POSTGRES_DB', 'buyhigh')
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')

def get_db_connection():
    """Stellt eine Verbindung zur PostgreSQL-Datenbank her."""
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
    conn = get_db_connection()
    try:
        # Keine Tabellen-Erstellung notwendig, da alle Tabellen bereits existieren
        logger.info("PostgreSQL: Verbindung erfolgreich hergestellt.")
    except psycopg2.Error as e:
        logger.error(f"Fehler während der DB-Initialisierung: {e}", exc_info=True)
    finally:
        conn.close()

def add_user(username, email, firebase_uid, provider='password'):
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
        return True
    except psycopg2.IntegrityError as e:
        conn.rollback()
        logger.error(f"Fehler beim Hinzufügen des Benutzers '{username}': {e}", exc_info=True)
        return False
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"DB-Fehler beim Hinzufügen des Benutzers '{username}': {e}", exc_info=True)
        return False
    finally:
        cur.close()
        conn.close()

def get_user_by_firebase_uid(firebase_uid):
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
        return None
    finally:
        cur.close()
        conn.close()

def get_user_by_id(user_id):
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
        return None
    finally:
        cur.close()
        conn.close()

def get_user_by_username(username):
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
        return None
    finally:
        cur.close()
        conn.close()

def get_user_by_email(email):
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
        return None
    finally:
        cur.close()
        conn.close()

def update_last_login(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (user_id,))
        conn.commit()
        return cur.rowcount > 0
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Aktualisieren der letzten Login-Zeit für Benutzer ID {user_id}: {e}", exc_info=True)
        return False
    finally:
        cur.close()
        conn.close()

def update_firebase_uid(user_id, firebase_uid):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET firebase_uid = %s WHERE id = %s", (firebase_uid, user_id))
        conn.commit()
        return cur.rowcount > 0
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Aktualisieren der Firebase UID für Benutzer ID {user_id}: {e}", exc_info=True)
        return False
    finally:
        cur.close()
        conn.close()

def update_user_theme(user_id, theme):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET theme = %s WHERE id = %s", (theme, user_id))
        conn.commit()
        return cur.rowcount
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Aktualisieren des Themes für Benutzer ID {user_id}: {e}", exc_info=True)
        return 0
    finally:
        cur.close()
        conn.close()

def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        return cur.rowcount > 0
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Löschen des Benutzers mit ID {user_id}: {e}", exc_info=True)
        return False
    finally:
        cur.close()
        conn.close()

def get_all_users():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT id, username, email FROM users ORDER BY username")
        users = [dict(row) for row in cur.fetchall()]
        return users
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen aller Benutzer: {e}", exc_info=True)
        return []
    finally:
        cur.close()
        conn.close()

def create_asset(symbol, name, asset_type, exchange=None, currency="USD", 
                sector=None, industry=None, logo_url=None, description=None, default_price=None):
    """
    Erstellt ein neues Asset in der Datenbank.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO assets 
                    (symbol, name, asset_type, exchange, currency, sector, industry, logo_url, description, default_price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (symbol, name, asset_type, exchange, currency, sector, industry, logo_url, description, default_price))
                conn.commit()
                return True
    except Exception as e:
        logger.error(f"Fehler beim Erstellen eines Assets: {e}")
        return False

if __name__ == "__main__":
    print("Starte einfachen Test für postgres_db_handler.py ...")
    try:
        init_db()
        print("init_db erfolgreich ausgeführt.")
        users = get_all_users()
        print(f"get_all_users: {users}")
        print("Test abgeschlossen.")
    except Exception as e:
        print(f"Fehler beim Testen von postgres_db_handler.py: {e}")
