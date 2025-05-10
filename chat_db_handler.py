import sqlite3
import logging
from datetime import datetime

# Logger konfigurieren
logger = logging.getLogger(__name__)

def get_db_connection():
    """Verbindung zur SQLite-Datenbank herstellen"""
    conn = sqlite3.connect('/Users/julianstosse/Developer/BuyHigh.io/database/database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_user_chats(user_id):
    """Alle Chats abrufen, an denen ein Benutzer teilnimmt"""
    # Stellen sicher, dass der Benutzer dem Standard-Chat beigetreten ist
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
        
        cursor.execute(query, (user_id,))
        chat_list = [dict(row) for row in cursor.fetchall()]
        
        # Zeit-Formatierung für die Anzeige
        for chat in chat_list:
            if chat['last_activity']:
                activity_time = datetime.strptime(chat['last_activity'], '%Y-%m-%d %H:%M:%S')
                now = datetime.now()
                delta = now - activity_time
                
                if delta.days > 0:
                    chat['last_activity'] = f"vor {delta.days} Tag{'en' if delta.days > 1 else ''}"
                elif delta.seconds > 3600:
                    hours = delta.seconds // 3600
                    chat['last_activity'] = f"vor {hours} Std"
                elif delta.seconds > 60:
                    minutes = delta.seconds // 60
                    chat['last_activity'] = f"vor {minutes} Min"
                else:
                    chat['last_activity'] = "gerade eben"
        
        logger.debug(f"Found {len(chat_list)} chats for user {user_id}")
        return chat_list
    except sqlite3.Error as e:
        logger.error(f"Datenbankfehler beim Abrufen der Chats: {e}")
        return []
    finally:
        conn.close()

def ensure_user_in_default_chat(user_id):
    """Stellt sicher, dass ein Benutzer am Standard-Chat (General) teilnimmt"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Prüfen, ob der Standard-Chat existiert
        cursor.execute("SELECT id FROM chat_rooms WHERE name = 'General' LIMIT 1")
        default_chat = cursor.fetchone()
        
        if not default_chat:
            # Standard-Chat erstellen, falls er nicht existiert
            cursor.execute("INSERT INTO chat_rooms (name) VALUES ('General')")
            default_chat_id = cursor.lastrowid
        else:
            default_chat_id = default_chat['id']
        
        # Prüfen, ob der Benutzer bereits am Chat teilnimmt
        cursor.execute("SELECT 1 FROM chat_room_participants WHERE chat_room_id = ? AND user_id = ?", 
                      (default_chat_id, user_id))
        
        if not cursor.fetchone():
            # Benutzer zum Chat hinzufügen
            cursor.execute("INSERT INTO chat_room_participants (chat_room_id, user_id) VALUES (?, ?)", 
                          (default_chat_id, user_id))
            conn.commit()
            logger.debug(f"User {user_id} added to default chat {default_chat_id}")
            return True
        
        return False
    except sqlite3.Error as e:
        logger.error(f"Fehler beim Hinzufügen des Benutzers zum Standard-Chat: {e}")
        return False
    finally:
        conn.close()

def get_chat_by_id(chat_id):
    """Chatroom-Informationen anhand der ID abrufen"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM chat_rooms WHERE id = ?", (chat_id,))
        chat = cursor.fetchone()
        
        if chat:
            return dict(chat)
        return None
    except sqlite3.Error as e:
        logger.error(f"Datenbankfehler beim Abrufen des Chats: {e}")
        return None
    finally:
        conn.close()

def is_chat_participant(chat_id, user_id):
    """Prüft, ob ein Benutzer an einem Chat teilnimmt"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT 1 FROM chat_room_participants WHERE chat_room_id = ? AND user_id = ?", 
                      (chat_id, user_id))
        return cursor.fetchone() is not None
    except sqlite3.Error as e:
        logger.error(f"Datenbankfehler bei der Teilnahmeprüfung: {e}")
        return False
    finally:
        conn.close()

def join_chat(chat_id, user_id):
    """Benutzer zu einem Chat hinzufügen"""
    if is_chat_participant(chat_id, user_id):
        return True  # Benutzer nimmt bereits teil
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO chat_room_participants (chat_room_id, user_id) VALUES (?, ?)", 
                      (chat_id, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Datenbankfehler beim Beitreten zum Chat: {e}")
        return False
    finally:
        conn.close()

def create_chat(chat_name, user_id):
    """Einen neuen Chat erstellen"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # Neuen Chat erstellen
        cursor.execute(
            "INSERT INTO chat_rooms (name, created_by) VALUES (?, ?)", 
            (chat_name, user_id)
        )
        chat_id = cursor.lastrowid
        
        # Ersteller als Teilnehmer hinzufügen
        cursor.execute(
            "INSERT INTO chat_room_participants (chat_room_id, user_id, chat_name) VALUES (?, ?, ?)",
            (chat_id, user_id, chat_name)
        )
        
        conn.commit()
        return chat_id
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Datenbankfehler beim Erstellen des Chats: {e}")
        return None
    finally:
        conn.close()

def add_message_and_get_details(chat_id, user_id, message_text):
    """Nachricht zu einem Chat hinzufügen und die Details der Nachricht abrufen."""
    logger.debug(f"[DB] add_message_and_get_details called: chat_id={chat_id}, user_id={user_id}, message_text={message_text}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Aktuelle UTC-Zeit für den Zeitstempel
        sent_at_dt = datetime.utcnow()
        sent_at_iso = sent_at_dt.isoformat() + "Z" # ISO 8601 Format mit Z für UTC

        cursor.execute(
            "INSERT INTO messages (chat_room_id, user_id, message_text, sent_at) VALUES (?, ?, ?, ?)",
            (chat_id, user_id, message_text, sent_at_dt.strftime('%Y-%m-%d %H:%M:%S')) # SQLite speichert als TEXT
        )
        message_id = cursor.lastrowid
        conn.commit()
        logger.debug(f"[DB] Message inserted with id: {message_id}")

        # Benutzername abrufen
        user_cursor = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user_row = user_cursor.fetchone()
        sender_name = user_row['username'] if user_row else "Unbekannt"
        
        # Rückgabe der Nachrichtendetails
        return {
            'id': message_id,
            'chat_room_id': chat_id,
            'user_id': user_id,
            'username': sender_name,
            'message_text': message_text,
            'sent_at': sent_at_iso
        }
    except sqlite3.Error as e:
        logger.error(f"[DB] Fehler beim Hinzufügen und Abrufen einer Nachricht: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_chat_messages(chat_id, limit=50, offset=0):
    """Nachrichten eines Chats abrufen"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT m.id, m.message_text, m.sent_at, m.user_id,
                  u.username -- Geändert von sender_name zu username
            FROM messages m
            JOIN users u ON m.user_id = u.id
            WHERE m.chat_room_id = ?
            ORDER BY m.sent_at DESC
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(query, (chat_id, limit, offset))
        messages = [dict(row) for row in cursor.fetchall()]
        
        # Konvertiere sent_at zu ISO-Format für JavaScript-Konsistenz
        for msg in messages:
            if msg.get('sent_at'):
                try:
                    # Zeitstempel aus DB ist wahrscheinlich ein String
                    dt_obj = datetime.strptime(msg['sent_at'], '%Y-%m-%d %H:%M:%S')
                    # In UTC umwandeln, wenn es als lokale Zeit gespeichert wurde (Annahme: DB speichert UTC oder naive Zeit)
                    # Wenn DB bereits UTC speichert, ist dies idempotent oder kann angepasst werden.
                    # Für dieses Beispiel nehmen wir an, dass es naiv ist und als UTC interpretiert werden soll.
                    msg['sent_at'] = dt_obj.isoformat() + "Z"
                except ValueError:
                    # Fallback, falls das Format anders ist oder bereits ISO
                    pass # Behalte den ursprünglichen Wert oder logge einen Fehler
                    
        messages.reverse()  # Chronologische Reihenfolge (älteste zuerst)
        
        return messages
    except sqlite3.Error as e:
        logger.error(f"Datenbankfehler beim Abrufen der Nachrichten: {e}")
        return []
    finally:
        conn.close()

def delete_chat(chat_id):
    """Löscht einen Chat und alle zugehörigen Nachrichten und Teilnehmer."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.execute("BEGIN TRANSACTION")
        cursor.execute("DELETE FROM messages WHERE chat_room_id = ?", (chat_id,))
        cursor.execute("DELETE FROM chat_room_participants WHERE chat_room_id = ?", (chat_id,))
        cursor.execute("DELETE FROM chat_rooms WHERE id = ?", (chat_id,))
        conn.commit()
        logger.debug(f"Chat {chat_id} und alle zugehörigen Daten wurden gelöscht.")
        return True
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Löschen des Chats {chat_id}: {e}")
        return False
    finally:
        conn.close()