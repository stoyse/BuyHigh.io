import sqlite3
import os
from datetime import datetime
import logging

# Configure logger
logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s') # Wird global in app.py konfiguriert

DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'database.db')

if not os.path.exists(DATABASE_DIR):
    try:
        os.makedirs(DATABASE_DIR)
        logger.info(f"Datenbankverzeichnis erstellt: {DATABASE_DIR}")
    except OSError as e:
        logger.error(f"Fehler beim Erstellen des Datenbankverzeichnisses {DATABASE_DIR}: {e}")

def get_db_connection():
    logger.debug(f"Versuche SQLite-Datenbankverbindung zu öffnen: {DATABASE_PATH}")
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row
        logger.debug(f"SQLite-Datenbankverbindung erfolgreich geöffnet: {DATABASE_PATH}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Fehler beim Öffnen der SQLite-Datenbankverbindung zu {DATABASE_PATH}: {e}", exc_info=True)
        raise

def _parse_user_timestamps(user_row):
    if user_row is None:
        return None
    
    user_data = dict(user_row)
    logger.debug(f"Parse Zeitstempel für Benutzerdaten: {list(user_data.keys())}")

    for key in ['created_at', 'last_login']:
        timestamp_str = user_data.get(key)
        if timestamp_str and isinstance(timestamp_str, str):
            try:
                user_data[key] = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                logger.debug(f"Zeitstempel '{key}' erfolgreich geparst (mit Mikrosekunden): {user_data[key]}")
            except ValueError:
                try:
                    user_data[key] = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    logger.debug(f"Zeitstempel '{key}' erfolgreich geparst (ohne Mikrosekunden): {user_data[key]}")
                except ValueError:
                    logger.warning(f"Konnte Zeitstempel-String '{timestamp_str}' für Schlüssel '{key}' nicht parsen.")
                    pass 
    return user_data

def init_db():
    logger.info(f"Initialisiere Datenbank unter: {DATABASE_PATH}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        logger.debug("Erstelle Tabelle 'users', falls nicht vorhanden.")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT, 
            firebase_uid TEXT UNIQUE, 
            firebase_provider TEXT DEFAULT 'password', 
            balance REAL DEFAULT 10000.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            mood_pet TEXT DEFAULT 'bull',
            pet_energy INTEGER DEFAULT 100,
            is_meme_mode BOOLEAN DEFAULT 0,
            email_verified BOOLEAN DEFAULT 0,
            theme TEXT DEFAULT 'light',
            total_trades INTEGER DEFAULT 0,
            profit_loss REAL DEFAULT 0.0
        )
        """)
        logger.info("Tabelle 'users' erfolgreich erstellt/überprüft.")
        
        logger.debug("Überprüfe, ob Spalte 'firebase_provider' in 'users' existiert.")
        try:
            cursor.execute("SELECT firebase_provider FROM users LIMIT 1")
            logger.debug("Spalte 'firebase_provider' existiert bereits.")
        except sqlite3.OperationalError:
            logger.info("Spalte 'firebase_provider' existiert nicht, füge sie hinzu.")
            cursor.execute("ALTER TABLE users ADD COLUMN firebase_provider TEXT DEFAULT 'password'")
            logger.info("Spalte 'firebase_provider' erfolgreich zur Tabelle 'users' hinzugefügt.")
        
        conn.commit()
        logger.info("Datenbankinitialisierung abgeschlossen und Änderungen committet.")
    except sqlite3.Error as e:
        logger.error(f"Fehler während der Datenbankinitialisierung: {e}", exc_info=True)
        conn.rollback() # Änderungen zurückrollen im Fehlerfall
    finally:
        conn.close()
        logger.debug("Datenbankverbindung nach init_db geschlossen.")
    # print("Database initialized with users, asset_types, transactions, and chat_room_participants tables.") # Ersetzt durch Logging

def add_user(username, email, firebase_uid, provider='password'):
    logger.info(f"Füge Benutzer hinzu: Benutzername='{username}', E-Mail='{email}', Firebase UID='{firebase_uid}', Provider='{provider}'")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, firebase_uid, firebase_provider) VALUES (?, ?, ?, ?)",
            (username, email, firebase_uid, provider)
        )
        conn.commit()
        user_id = cursor.lastrowid
        logger.info(f"Benutzer '{username}' erfolgreich mit ID {user_id} zur Datenbank hinzugefügt.")
        return True
    except sqlite3.IntegrityError as e: # Spezifischer Fehler für UNIQUE constraints
        logger.error(f"Fehler beim Hinzufügen des Benutzers '{username}': Eindeutigkeitsverletzung (Benutzername oder E-Mail bereits vorhanden). Details: {e}", exc_info=True)
        return False
    except sqlite3.Error as e:
        logger.error(f"Datenbankfehler beim Hinzufügen des Benutzers '{username}': {e}", exc_info=True)
        return False
    finally:
        conn.close()
        logger.debug(f"Datenbankverbindung nach add_user für '{username}' geschlossen.")

def get_user_by_firebase_uid(firebase_uid):
    logger.debug(f"Suche Benutzer anhand Firebase UID: {firebase_uid}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE firebase_uid = ?", (firebase_uid,))
        user = cursor.fetchone()
        if user:
            logger.info(f"Benutzer mit Firebase UID '{firebase_uid}' gefunden: ID={user['id']}, Benutzername='{user['username']}'")
            return _parse_user_timestamps(user)
        else:
            logger.info(f"Kein Benutzer mit Firebase UID '{firebase_uid}' gefunden.")
            return None
    except sqlite3.Error as e:
        logger.error(f"Datenbankfehler beim Suchen nach Firebase UID '{firebase_uid}': {e}", exc_info=True)
        return None
    finally:
        conn.close()
        logger.debug(f"Datenbankverbindung nach get_user_by_firebase_uid für '{firebase_uid}' geschlossen.")

def get_user_by_id(user_id):
    logger.debug(f"Suche Benutzer anhand lokaler ID: {user_id}")
    if not user_id:
        logger.warning("get_user_by_id aufgerufen mit ungültiger user_id (None oder leer).")
        return None
        
    db = get_db_connection()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            logger.info(f"Benutzer mit lokaler ID '{user_id}' gefunden: Benutzername='{user['username']}'")
            user_dict = dict(user) if hasattr(user, "keys") else dict(zip([col[0] for col in cursor.description], user))
            return _parse_user_timestamps(user_dict) # Parse Timestamps hier auch
        else:
            logger.info(f"Kein Benutzer mit lokaler ID '{user_id}' gefunden.")
            return None
    except sqlite3.Error as e: # Geändert von Exception zu sqlite3.Error
        logger.error(f"Datenbankfehler beim Suchen nach Benutzer mit ID '{user_id}': {e}", exc_info=True)
        return None
    finally:
        db.close()
        logger.debug(f"Datenbankverbindung nach get_user_by_id für '{user_id}' geschlossen.")

def get_user_by_username(username):
    logger.debug(f"Suche Benutzer anhand Benutzername: {username}")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user:
            logger.info(f"Benutzer mit Benutzername '{username}' gefunden: ID={user['id']}")
            return _parse_user_timestamps(dict(user))
        else:
            logger.info(f"Kein Benutzer mit Benutzername '{username}' gefunden.")
            return None
    except sqlite3.Error as e:
        logger.error(f"Datenbankfehler beim Suchen nach Benutzername '{username}': {e}", exc_info=True)
        return None
    finally:
        conn.close()
        logger.debug(f"Datenbankverbindung nach get_user_by_username für '{username}' geschlossen.")

def get_user_by_email(email):
    logger.debug(f"Suche Benutzer anhand E-Mail: {email}")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if user:
            logger.info(f"Benutzer mit E-Mail '{email}' gefunden: ID={user['id']}, Benutzername='{user['username']}'")
            return _parse_user_timestamps(dict(user))
        else:
            logger.info(f"Kein Benutzer mit E-Mail '{email}' gefunden.")
            return None
    except sqlite3.Error as e:
        logger.error(f"Datenbankfehler beim Suchen nach E-Mail '{email}': {e}", exc_info=True)
        return None
    finally:
        conn.close()
        logger.debug(f"Datenbankverbindung nach get_user_by_email für '{email}' geschlossen.")

def update_last_login(user_id):
    logger.info(f"Aktualisiere letzte Login-Zeit für Benutzer ID: {user_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Letzte Login-Zeit für Benutzer ID {user_id} erfolgreich aktualisiert.")
            return True
        else:
            logger.warning(f"Konnte letzte Login-Zeit für Benutzer ID {user_id} nicht aktualisieren (Benutzer nicht gefunden oder Zeitstempel bereits aktuell).")
            return False # Oder True, je nachdem, ob "nicht gefunden" als Fehler gilt
    except sqlite3.Error as e:
        logger.error(f"Datenbankfehler beim Aktualisieren der letzten Login-Zeit für Benutzer ID {user_id}: {e}", exc_info=True)
        return False
    finally:
        conn.close()
        logger.debug(f"Datenbankverbindung nach update_last_login für Benutzer ID {user_id} geschlossen.")

def update_firebase_uid(user_id, firebase_uid):
    logger.info(f"Aktualisiere Firebase UID auf '{firebase_uid}' für lokalen Benutzer ID: {user_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE users SET firebase_uid = ? WHERE id = ?", 
            (firebase_uid, user_id)
        )
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Firebase UID für Benutzer ID {user_id} erfolgreich auf '{firebase_uid}' aktualisiert.")
            return True
        else:
            logger.warning(f"Konnte Firebase UID für Benutzer ID {user_id} nicht aktualisieren (Benutzer nicht gefunden).")
            return False
    except sqlite3.Error as e:
        logger.error(f"Datenbankfehler beim Aktualisieren der Firebase UID für Benutzer ID {user_id}: {e}", exc_info=True)
        return False
    finally:
        conn.close()
        logger.debug(f"Datenbankverbindung nach update_firebase_uid für Benutzer ID {user_id} geschlossen.")

def update_user_theme(user_id, theme):
    logger.info(f"Aktualisiere Theme auf '{theme}' für Benutzer ID: {user_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET theme = ? WHERE id = ?", (theme, user_id))
        conn.commit()
        updated_rows = cursor.rowcount
        if updated_rows > 0:
            logger.info(f"Theme für Benutzer ID {user_id} erfolgreich auf '{theme}' aktualisiert.")
        else:
            logger.warning(f"Konnte Theme für Benutzer ID {user_id} nicht aktualisieren (Benutzer nicht gefunden oder Theme bereits '{theme}').")
        return updated_rows # Gibt Anzahl der aktualisierten Zeilen zurück
    except sqlite3.Error as e:
        logger.error(f"Datenbankfehler beim Aktualisieren des Themes für Benutzer ID {user_id}: {e}", exc_info=True)
        return 0
    finally:
        conn.close()
        logger.debug(f"Datenbankverbindung nach update_user_theme für Benutzer ID {user_id} geschlossen.")

def delete_user(user_id):
    """Löscht einen Benutzer aus der lokalen Datenbank anhand seiner ID."""
    logger.info(f"Versuche Benutzer mit lokaler ID {user_id} zu löschen.")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Zuerst abhängige Daten löschen oder Verknüpfungen aufheben (Beispiel: Transaktionen, Chat-Teilnahmen)
        # Dies hängt von Ihrem Datenbankschema und den Fremdschlüsselbeziehungen ab.
        # Beispiel:
        # logger.debug(f"Lösche Transaktionen für Benutzer ID {user_id}.")
        # cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        # logger.debug(f"Lösche Chat-Teilnahmen für Benutzer ID {user_id}.")
        # cursor.execute("DELETE FROM chat_room_participants WHERE user_id = ?", (user_id,))
        # ... weitere Abhängigkeiten ...

        logger.debug(f"Lösche Benutzerdatensatz für ID {user_id} aus Tabelle 'users'.")
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Benutzer mit lokaler ID {user_id} erfolgreich aus der Datenbank gelöscht.")
            return True
        else:
            logger.warning(f"Konnte Benutzer mit lokaler ID {user_id} nicht löschen (nicht gefunden).")
            return False
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Datenbankfehler beim Löschen des Benutzers mit ID {user_id}: {e}", exc_info=True)
        return False
    finally:
        conn.close()
        logger.debug(f"Datenbankverbindung nach delete_user für ID {user_id} geschlossen.")

def update_user_password(user_id, new_password_hash):
    """Aktualisiert den Passwort-Hash eines Benutzers. (Veraltet, wenn Firebase verwendet wird)"""
    logger.warning(f"Aufruf von veralteter Funktion update_user_password für Benutzer ID {user_id}. Passwörter sollten in Firebase verwaltet werden.")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Lokaler Passwort-Hash für Benutzer ID {user_id} aktualisiert (veraltete Funktion).")
            return True
        else:
            logger.warning(f"Konnte lokalen Passwort-Hash für Benutzer ID {user_id} nicht aktualisieren (Benutzer nicht gefunden).")
            return False
    except sqlite3.Error as e:
        logger.error(f"Datenbankfehler beim Aktualisieren des lokalen Passwort-Hashes für Benutzer ID {user_id}: {e}", exc_info=True)
        return False
    finally:
        conn.close()
        logger.debug(f"Datenbankverbindung nach update_user_password für ID {user_id} geschlossen.")

def get_all_users():
    """Ruft alle Benutzer aus der Datenbank ab (für Admin-Zwecke, z.B. Chat-Mitglieder hinzufügen)."""
    logger.debug("Rufe alle Benutzer aus der Datenbank ab.")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, email FROM users ORDER BY username")
        users = [dict(row) for row in cursor.fetchall()]
        logger.info(f"{len(users)} Benutzer erfolgreich abgerufen.")
        return users
    except sqlite3.Error as e:
        logger.error(f"Datenbankfehler beim Abrufen aller Benutzer: {e}", exc_info=True)
        return []
    finally:
        conn.close()
        logger.debug("Datenbankverbindung nach get_all_users geschlossen.")

# Chat-spezifische Funktionen, die möglicherweise hier waren, sollten in chat_db_handler.py sein.
# Beispiel: get_chat_room, get_chat_members, add_chat_member, remove_chat_member, set_members_can_invite
# Diese müssen ggf. angepasst werden, um Firebase zu berücksichtigen oder bleiben reine SQLite-Implementierungen,
# wenn chat_db_handler.py die Logik für die Datenbankauswahl übernimmt.

# Beispiel für eine Chat-Funktion, die hier bleiben könnte, wenn sie nur SQLite betrifft
# und nicht von der Firebase/SQLite-Auswahl in chat_db_handler betroffen ist.
# Dies ist jedoch unwahrscheinlich für die meisten Chat-Funktionen.
def get_chat_room(chat_id):
    """Ruft einen Chatraum anhand seiner ID ab (Beispiel für eine Funktion, die hier sein könnte)."""
    # Diese Funktion ist wahrscheinlich besser in chat_db_handler.py aufgehoben,
    # da sie von der Firebase/SQLite-Entscheidung betroffen sein sollte.
    # Wenn sie hier bleibt, ist sie rein SQLite.
    logger.debug(f"db_handler.get_chat_room (SQLite) aufgerufen für Chat-ID: {chat_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Annahme: Es gibt eine Tabelle chat_rooms in der SQLite-DB
        cursor.execute("SELECT * FROM chat_rooms WHERE id = ?", (chat_id,))
        chat_room = cursor.fetchone()
        if chat_room:
            logger.info(f"Chatraum mit ID {chat_id} in SQLite gefunden.")
            return dict(chat_room)
        else:
            logger.info(f"Kein Chatraum mit ID {chat_id} in SQLite gefunden.")
            return None
    except sqlite3.Error as e:
        logger.error(f"SQLite-Fehler beim Abrufen von Chatraum {chat_id}: {e}", exc_info=True)
        return None
    finally:
        conn.close()
