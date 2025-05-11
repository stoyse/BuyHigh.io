import sqlite3
import logging
from datetime import datetime
import os

# Logger konfigurieren
logger = logging.getLogger(__name__)

# --- BEGIN: Use DATABASE_FILE_PATH from environment or fallback ---
DATABASE_ENV_PATH = os.getenv('DATABASE_FILE_PATH', 'database/database.db')
if not os.path.isabs(DATABASE_ENV_PATH):
    APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    DB_PATH = os.path.abspath(os.path.join(APP_ROOT, DATABASE_ENV_PATH))
else:
    DB_PATH = DATABASE_ENV_PATH
# --- END: Use DATABASE_FILE_PATH from environment or fallback ---

# Check if we should use Firebase
USE_FIREBASE_ENV = os.getenv('USE_FIREBASE', 'true').lower() == 'true' # Umbenannt zur Klarheit
logger.info(f"Chat DB Handler: USE_FIREBASE aus Umgebungsvariable: {USE_FIREBASE_ENV}")

def get_db_connection():
    """Verbindung zur SQLite-Datenbank herstellen"""
    logger.debug(f"Versuche SQLite-Verbindung zu öffnen: {DB_PATH}")
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        logger.debug(f"SQLite-Verbindung erfolgreich geöffnet: {DB_PATH}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Fehler beim Öffnen der SQLite-Verbindung zu {DB_PATH}: {e}", exc_info=True)
        raise # Fehler weiterleiten, damit er behandelt werden kann

# Try to import Firebase handler, but don't fail if not available
_firebase_handler_available = False
if USE_FIREBASE_ENV:
    try:
        import database.handler.firebase_db_handler as firebase_db_handler
        if firebase_db_handler.can_use_firebase():
            _firebase_handler_available = True
            logger.info("Firebase DB Handler ist verfügbar und nutzbar.")
        else:
            logger.warning("Firebase DB Handler importiert, aber Firebase ist nicht nutzbar (can_use_firebase() gab False zurück). Fallback auf SQLite.")
    except ImportError:
        logger.warning("Firebase DB Handler (firebase_db_handler.py) nicht gefunden. Verwende nur SQLite für Chat-Operationen.")
    except Exception as e_fb_init:
        logger.error(f"Fehler beim Initialisieren/Prüfen des Firebase DB Handlers: {e_fb_init}. Verwende nur SQLite.", exc_info=True)
else:
    logger.info("USE_FIREBASE ist auf False gesetzt. Verwende nur SQLite für Chat-Operationen.")

# Function to determine which database system to use
def use_firebase_for_request():
    """Check if we should use Firebase for this request"""
    if USE_FIREBASE_ENV and _firebase_handler_available:
        logger.debug("Entscheidung: Verwende Firebase für diese Anfrage.")
        return True
    logger.debug("Entscheidung: Verwende SQLite für diese Anfrage.")
    return False

def get_user_chats(user_id):
    logger.info(f"get_user_chats aufgerufen für Benutzer ID: {user_id}")
    if use_firebase_for_request():
        try:
            logger.debug(f"Versuche Chats für Benutzer {user_id} von Firebase abzurufen.")
            return firebase_db_handler.get_user_chats(user_id)
        except Exception as e:
            logger.error(f"Firebase-Fehler in get_user_chats für Benutzer {user_id}: {e}. Fallback auf SQLite.", exc_info=True)
    
    logger.debug(f"Verwende SQLite für get_user_chats für Benutzer {user_id}.")
    ensure_user_in_default_chat(user_id)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT cr.id, cr.name, 
                   (SELECT message_text FROM messages 
                    WHERE chat_room_id = cr.id 
                    ORDER BY sent_at DESC LIMIT 1) as last_message,
                   (SELECT sent_at FROM messages 
                    WHERE chat_room_id = cr.id 
                    ORDER BY sent_at DESC LIMIT 1) as last_activity
            FROM chat_rooms cr
            JOIN chat_room_participants crp ON cr.id = crp.chat_room_id
            WHERE crp.user_id = ?
            ORDER BY last_activity DESC NULLS LAST, cr.created_at DESC
        """
        logger.debug(f"Führe SQLite-Query für get_user_chats aus (Benutzer {user_id}).")
        cursor.execute(query, (user_id,))
        chat_list_raw = cursor.fetchall()
        chat_list = [dict(row) for row in chat_list_raw]
        logger.info(f"{len(chat_list)} Chats in SQLite für Benutzer {user_id} gefunden.")
        
        for chat in chat_list:
            if chat.get('last_activity'):
                try:
                    activity_time = datetime.strptime(chat['last_activity'], '%Y-%m-%d %H:%M:%S')
                    now = datetime.now()
                    delta = now - activity_time
                    
                    if delta.days > 0:
                        chat['last_activity_formatted'] = f"vor {delta.days} Tag{'en' if delta.days > 1 else ''}"
                    elif delta.seconds > 3600:
                        hours = delta.seconds // 3600
                        chat['last_activity_formatted'] = f"vor {hours} Std"
                    elif delta.seconds > 60:
                        minutes = delta.seconds // 60
                        chat['last_activity_formatted'] = f"vor {minutes} Min"
                    else:
                        chat['last_activity_formatted'] = "gerade eben"
                except ValueError as ve_format:
                    logger.warning(f"Fehler beim Formatieren von last_activity '{chat['last_activity']}' für Chat {chat['id']}: {ve_format}")
                    chat['last_activity_formatted'] = chat['last_activity']
            else:
                chat['last_activity_formatted'] = "Keine Aktivität"
        
        return chat_list
    except sqlite3.Error as e:
        logger.error(f"SQLite-Datenbankfehler beim Abrufen der Chats für Benutzer {user_id}: {e}", exc_info=True)
        return []
    finally:
        if conn: conn.close()
        logger.debug(f"SQLite-Verbindung für get_user_chats (Benutzer {user_id}) geschlossen.")

def ensure_user_in_default_chat(user_id):
    logger.info(f"ensure_user_in_default_chat aufgerufen für Benutzer ID: {user_id}")
    if use_firebase_for_request():
        try:
            logger.debug(f"Versuche sicherzustellen, dass Benutzer {user_id} im Firebase Standard-Chat ist.")
            return firebase_db_handler.ensure_user_in_default_chat(user_id)
        except Exception as e:
            logger.error(f"Firebase-Fehler in ensure_user_in_default_chat für Benutzer {user_id}: {e}. Fallback auf SQLite.", exc_info=True)

    logger.debug(f"Verwende SQLite für ensure_user_in_default_chat für Benutzer {user_id}.")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM chat_rooms WHERE name = 'General' LIMIT 1")
        default_chat_row = cursor.fetchone()
        
        default_chat_id = None
        if not default_chat_row:
            logger.info("SQLite Standard-Chat 'General' nicht gefunden. Erstelle ihn.")
            cursor.execute("INSERT INTO chat_rooms (name) VALUES ('General')")
            default_chat_id = cursor.lastrowid
            conn.commit()
            logger.info(f"SQLite Standard-Chat 'General' mit ID {default_chat_id} erstellt.")
        else:
            default_chat_id = default_chat_row['id']
            logger.debug(f"SQLite Standard-Chat 'General' gefunden mit ID {default_chat_id}.")
        
        cursor.execute("SELECT 1 FROM chat_room_participants WHERE chat_room_id = ? AND user_id = ?", 
                      (default_chat_id, user_id))
        
        if not cursor.fetchone():
            logger.info(f"Benutzer {user_id} ist nicht im SQLite Standard-Chat {default_chat_id}. Füge hinzu.")
            cursor.execute("INSERT INTO chat_room_participants (chat_room_id, user_id) VALUES (?, ?)", 
                          (default_chat_id, user_id))
            conn.commit()
            logger.info(f"Benutzer {user_id} erfolgreich zum SQLite Standard-Chat {default_chat_id} hinzugefügt.")
            return True
        
        logger.debug(f"Benutzer {user_id} ist bereits im SQLite Standard-Chat {default_chat_id}.")
        return False
    except sqlite3.Error as e:
        logger.error(f"SQLite-Fehler beim Hinzufügen/Prüfen des Benutzers {user_id} zum Standard-Chat: {e}", exc_info=True)
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()
        logger.debug(f"SQLite-Verbindung für ensure_user_in_default_chat (Benutzer {user_id}) geschlossen.")

def get_default_chat_id():
    logger.info("get_default_chat_id aufgerufen.")
    logger.debug("Verwende SQLite für get_default_chat_id.")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM chat_rooms WHERE name = 'General' LIMIT 1")
        default_chat_row = cursor.fetchone()
        
        if default_chat_row:
            chat_id = default_chat_row['id']
            logger.info(f"SQLite Standard-Chat 'General' ID gefunden: {chat_id}")
            return chat_id
        logger.warning("SQLite Standard-Chat 'General' nicht gefunden.")
        return None
    except sqlite3.Error as e:
        logger.error(f"SQLite-Datenbankfehler beim Abrufen des Standard-Chats: {e}", exc_info=True)
        return None
    finally:
        if conn: conn.close()
        logger.debug("SQLite-Verbindung für get_default_chat_id geschlossen.")

def get_chat_by_id(chat_id):
    logger.info(f"get_chat_by_id aufgerufen für Chat ID: {chat_id}")
    if use_firebase_for_request():
        try:
            logger.debug(f"Versuche Chat {chat_id} von Firebase abzurufen.")
            return firebase_db_handler.get_chat_by_id(chat_id)
        except Exception as e:
            logger.error(f"Firebase-Fehler in get_chat_by_id für Chat {chat_id}: {e}. Fallback auf SQLite.", exc_info=True)

    logger.debug(f"Verwende SQLite für get_chat_by_id für Chat {chat_id}.")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM chat_rooms WHERE id = ?", (chat_id,))
        chat_row = cursor.fetchone()
        
        if chat_row:
            logger.info(f"SQLite Chat {chat_id} gefunden.")
            return dict(chat_row)
        logger.warning(f"SQLite Chat {chat_id} nicht gefunden.")
        return None
    except sqlite3.Error as e:
        logger.error(f"SQLite-Datenbankfehler beim Abrufen des Chats {chat_id}: {e}", exc_info=True)
        return None
    finally:
        if conn: conn.close()
        logger.debug(f"SQLite-Verbindung für get_chat_by_id (Chat {chat_id}) geschlossen.")

def is_chat_participant(chat_id, user_id):
    logger.info(f"is_chat_participant aufgerufen für Chat ID: {chat_id}, Benutzer ID: {user_id}")
    if use_firebase_for_request():
        try:
            logger.debug(f"Prüfe Teilnahme von Benutzer {user_id} in Chat {chat_id} (Firebase).")
            return firebase_db_handler.is_chat_participant(chat_id, user_id)
        except Exception as e:
            logger.error(f"Firebase-Fehler in is_chat_participant (Chat {chat_id}, Benutzer {user_id}): {e}. Fallback auf SQLite.", exc_info=True)

    logger.debug(f"Verwende SQLite für is_chat_participant (Chat {chat_id}, Benutzer {user_id}).")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT 1 FROM chat_room_participants WHERE chat_room_id = ? AND user_id = ?", 
                      (chat_id, user_id))
        is_participant_sqlite = cursor.fetchone() is not None
        logger.info(f"Benutzer {user_id} ist Teilnehmer in SQLite Chat {chat_id}: {is_participant_sqlite}")
        return is_participant_sqlite
    except sqlite3.Error as e:
        logger.error(f"SQLite-Datenbankfehler bei Teilnahmeprüfung (Chat {chat_id}, Benutzer {user_id}): {e}", exc_info=True)
        return False
    finally:
        if conn: conn.close()
        logger.debug(f"SQLite-Verbindung für is_chat_participant (Chat {chat_id}, Benutzer {user_id}) geschlossen.")

def join_chat(chat_id, user_id):
    logger.info(f"join_chat aufgerufen für Chat ID: {chat_id}, Benutzer ID: {user_id}")
    if use_firebase_for_request():
        try:
            logger.debug(f"Versuche Benutzer {user_id} zu Firebase Chat {chat_id} hinzuzufügen.")
            return firebase_db_handler.join_chat(chat_id, user_id)
        except Exception as e:
            logger.error(f"Firebase-Fehler in join_chat (Chat {chat_id}, Benutzer {user_id}): {e}. Fallback auf SQLite.", exc_info=True)

    logger.debug(f"Verwende SQLite für join_chat (Chat {chat_id}, Benutzer {user_id}).")
    if is_chat_participant(chat_id, user_id):
        logger.info(f"Benutzer {user_id} ist bereits Teilnehmer in SQLite Chat {chat_id}.")
        return True
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO chat_room_participants (chat_room_id, user_id) VALUES (?, ?)", 
                      (chat_id, user_id))
        conn.commit()
        logger.info(f"Benutzer {user_id} erfolgreich zu SQLite Chat {chat_id} hinzugefügt.")
        return True
    except sqlite3.Error as e:
        logger.error(f"SQLite-Datenbankfehler beim Beitreten zum Chat {chat_id} für Benutzer {user_id}: {e}", exc_info=True)
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()
        logger.debug(f"SQLite-Verbindung für join_chat (Chat {chat_id}, Benutzer {user_id}) geschlossen.")

def create_chat(chat_name, user_id):
    logger.info(f"create_chat aufgerufen: Name='{chat_name}', Ersteller-ID={user_id}")
    if use_firebase_for_request():
        try:
            logger.debug(f"Versuche Firebase Chat '{chat_name}' für Benutzer {user_id} zu erstellen.")
            return firebase_db_handler.create_chat(chat_name, user_id)
        except Exception as e:
            logger.error(f"Firebase-Fehler in create_chat (Name '{chat_name}', Benutzer {user_id}): {e}. Fallback auf SQLite.", exc_info=True)
    
    logger.debug(f"Verwende SQLite für create_chat (Name '{chat_name}', Benutzer {user_id}).")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        logger.debug(f"Füge Chat '{chat_name}' (Ersteller {user_id}) in SQLite Tabelle chat_rooms ein.")
        cursor.execute(
            "INSERT INTO chat_rooms (name, created_by) VALUES (?, ?)", 
            (chat_name, user_id)
        )
        new_chat_id = cursor.lastrowid
        logger.info(f"SQLite Chat '{chat_name}' mit ID {new_chat_id} erstellt.")
        
        cursor.execute(
            "INSERT INTO chat_room_participants (chat_room_id, user_id) VALUES (?, ?)",
            (new_chat_id, user_id)
        )
        
        conn.commit()
        logger.info(f"SQLite Chat '{chat_name}' (ID {new_chat_id}) und Ersteller-Teilnahme erfolgreich committet.")
        return new_chat_id
    except sqlite3.Error as e:
        if conn: conn.rollback()
        logger.error(f"SQLite-Datenbankfehler beim Erstellen des Chats '{chat_name}' für Benutzer {user_id}: {e}", exc_info=True)
        return None
    finally:
        if conn: conn.close()
        logger.debug(f"SQLite-Verbindung für create_chat (Name '{chat_name}', Benutzer {user_id}) geschlossen.")

def add_message_and_get_details(chat_id, user_id, message_text):
    logger.info(f"add_message_and_get_details: ChatID={chat_id}, UserID={user_id}, Nachricht (gekürzt)='{message_text[:50]}'")
    if use_firebase_for_request():
        try:
            logger.debug(f"Versuche Nachricht zu Firebase Chat {chat_id} von Benutzer {user_id} hinzuzufügen.")
            return firebase_db_handler.add_message_and_get_details(chat_id, user_id, message_text)
        except Exception as e:
            logger.error(f"Firebase-Fehler in add_message_and_get_details (Chat {chat_id}, Benutzer {user_id}): {e}. Fallback auf SQLite.", exc_info=True)
    
    logger.debug(f"[SQLite] add_message_and_get_details: ChatID={chat_id}, UserID={user_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sent_at_dt = datetime.utcnow()
        sent_at_iso = sent_at_dt.isoformat() + "Z"
        sent_at_sqlite = sent_at_dt.strftime('%Y-%m-%d %H:%M:%S')

        logger.debug(f"Füge Nachricht zu SQLite Chat {chat_id} ein. Zeitstempel (SQLite): {sent_at_sqlite}")
        cursor.execute(
            "INSERT INTO messages (chat_room_id, user_id, message_text, sent_at) VALUES (?, ?, ?, ?)",
            (chat_id, user_id, message_text, sent_at_sqlite)
        )
        message_id = cursor.lastrowid
        conn.commit()
        logger.info(f"[SQLite] Nachricht mit ID {message_id} in Chat {chat_id} eingefügt.")

        user_cursor = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user_row = user_cursor.fetchone()
        sender_name = user_row['username'] if user_row else "Unbekannt"
        logger.debug(f"Absendername für Benutzer {user_id} ist '{sender_name}'.")
        
        message_details = {
            'id': message_id,
            'chat_room_id': str(chat_id),
            'user_id': str(user_id),
            'username': sender_name,
            'message_text': message_text,
            'sent_at': sent_at_iso
        }
        logger.debug(f"[SQLite] Zurückgegebene Nachrichtendetails: {message_details}")
        return message_details
    except sqlite3.Error as e:
        logger.error(f"[SQLite] Fehler beim Hinzufügen und Abrufen einer Nachricht für Chat {chat_id}: {e}", exc_info=True)
        if conn: conn.rollback()
        return None
    finally:
        if conn: conn.close()
        logger.debug(f"[SQLite] Verbindung für add_message_and_get_details (Chat {chat_id}) geschlossen.")

def get_chat_messages(chat_id, limit=50, offset=0):
    logger.info(f"get_chat_messages: ChatID={chat_id}, Limit={limit}, Offset={offset}")
    if use_firebase_for_request():
        try:
            logger.debug(f"Versuche Nachrichten für Firebase Chat {chat_id} abzurufen.")
            return firebase_db_handler.get_chat_messages(chat_id, limit, offset)
        except Exception as e:
            logger.error(f"Firebase-Fehler in get_chat_messages (Chat {chat_id}): {e}. Fallback auf SQLite.", exc_info=True)
    
    logger.debug(f"Verwende SQLite für get_chat_messages (Chat {chat_id}).")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT m.id, m.message_text, m.sent_at, m.user_id,
                  u.username
            FROM messages m
            JOIN users u ON m.user_id = u.id
            WHERE m.chat_room_id = ?
            ORDER BY m.sent_at DESC
            LIMIT ? OFFSET ?
        """
        logger.debug(f"Führe SQLite-Query für get_chat_messages (Chat {chat_id}) aus.")
        cursor.execute(query, (chat_id, limit, offset))
        messages_raw = cursor.fetchall()
        messages = [dict(row) for row in messages_raw]
        logger.info(f"{len(messages)} Nachrichten in SQLite für Chat {chat_id} (Limit {limit}, Offset {offset}) gefunden.")
        
        for msg in messages:
            if msg.get('sent_at') and isinstance(msg['sent_at'], str):
                try:
                    dt_obj = datetime.strptime(msg['sent_at'], '%Y-%m-%d %H:%M:%S')
                    msg['sent_at'] = dt_obj.isoformat() + "Z"
                except ValueError:
                    logger.warning(f"Konnte sent_at '{msg['sent_at']}' nicht in ISO-Format umwandeln für Nachricht ID {msg.get('id')}.")
                    pass 
            msg['id'] = str(msg.get('id'))
            msg['user_id'] = str(msg.get('user_id'))
            msg['chat_room_id'] = str(chat_id)

        messages.reverse()
        
        logger.debug(f"Zurückgegebene Nachrichten für Chat {chat_id}: {messages}")
        return messages
    except sqlite3.Error as e:
        logger.error(f"SQLite-Datenbankfehler beim Abrufen der Nachrichten für Chat {chat_id}: {e}", exc_info=True)
        return []
    finally:
        if conn: conn.close()
        logger.debug(f"SQLite-Verbindung für get_chat_messages (Chat {chat_id}) geschlossen.")

def delete_chat(chat_id):
    logger.info(f"delete_chat aufgerufen für Chat ID: {chat_id}")
    if use_firebase_for_request():
        try:
            logger.debug(f"Versuche Firebase Chat {chat_id} zu löschen.")
            return firebase_db_handler.delete_chat(chat_id)
        except Exception as e:
            logger.error(f"Firebase-Fehler in delete_chat (Chat {chat_id}): {e}. Fallback auf SQLite.", exc_info=True)
    
    logger.debug(f"Verwende SQLite für delete_chat (Chat {chat_id}).")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.execute("BEGIN TRANSACTION")
        logger.debug(f"Lösche Nachrichten für SQLite Chat {chat_id}.")
        cursor.execute("DELETE FROM messages WHERE chat_room_id = ?", (chat_id,))
        logger.debug(f"Lösche Teilnehmer für SQLite Chat {chat_id}.")
        cursor.execute("DELETE FROM chat_room_participants WHERE chat_room_id = ?", (chat_id,))
        logger.debug(f"Lösche SQLite Chatraum {chat_id}.")
        cursor.execute("DELETE FROM chat_rooms WHERE id = ?", (chat_id,))
        conn.commit()
        logger.info(f"SQLite Chat {chat_id} und zugehörige Daten erfolgreich gelöscht.")
        return True
    except sqlite3.Error as e:
        if conn: conn.rollback()
        logger.error(f"SQLite-Fehler beim Löschen des Chats {chat_id}: {e}", exc_info=True)
        return False
    finally:
        if conn: conn.close()
        logger.debug(f"SQLite-Verbindung für delete_chat (Chat {chat_id}) geschlossen.")

def migrate_data_to_firebase():
    logger.info("migrate_data_to_firebase aufgerufen.")
    if not USE_FIREBASE_ENV:
        logger.warning("Firebase ist in der Umgebung deaktiviert. Migration wird nicht durchgeführt.")
        return False
    
    if not _firebase_handler_available:
        logger.error("Firebase DB Handler ist nicht verfügbar. Migration kann nicht durchgeführt werden.")
        return False
        
    try:
        import database.handler.firebase_db_handler as firebase_db_handler 
        logger.info("Starte Migration von SQLite Chat-Daten zu Firebase.")
        result = firebase_db_handler.migrate_chat_data_from_sqlite_to_firebase()
        if result:
            logger.info("Migration von SQLite zu Firebase erfolgreich abgeschlossen.")
        else:
            logger.error("Migration von SQLite zu Firebase fehlgeschlagen.")
        return result
    except ImportError:
        logger.error("Firebase DB Handler konnte nicht importiert werden. Migration abgebrochen.")
        return False
    except Exception as e:
        logger.error(f"Fehler während der Migration von SQLite zu Firebase: {e}", exc_info=True)
        return False