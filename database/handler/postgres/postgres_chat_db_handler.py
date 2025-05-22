import psycopg2
import psycopg2.extras
from psycopg2 import pool
import logging
from datetime import datetime
import os
from rich import print

logger = logging.getLogger(__name__)

def is_int(val):
    # Internal helper, analytics not typically added.
    try:
        int(val)
        return True
    except (TypeError, ValueError):
        return False

connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    dbname=os.getenv('POSTGRES_DB')
)

def get_db_connection(request):
    try:
        connection = connection_pool.getconn()
    except Exception as e:
        print(f"Error getting connection from pool: {e}")
        return None, str(e)  # Return None and the error message
    return connection, None # Return connection and no error

def get_user_chats(user_id):
    logger.info(f"get_user_chats (Postgres) aufgerufen für Benutzer ID: {user_id}")
    ensure_user_in_default_chat(user_id)
    conn, error = get_db_connection(None)
    if error:
        logger.error(f"Fehler beim Abrufen der Datenbankverbindung: {error}")
        return []
    if conn is None:
        logger.error("Datenbankverbindung fehlgeschlagen")
        return []
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
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
            WHERE crp.user_id = %s
            ORDER BY last_activity DESC NULLS LAST, cr.created_at DESC
        """
        cursor.execute(query, (user_id,))
        chat_list = cursor.fetchall()
        for chat in chat_list:
            if chat.get('last_activity'):
                try:
                    activity_time = chat['last_activity']
                    if isinstance(activity_time, str):
                        activity_time = datetime.strptime(activity_time, '%Y-%m-%d %H:%M:%S')
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
                except Exception as ve_format:
                    logger.warning(f"Fehler beim Formatieren von last_activity '{chat['last_activity']}' für Chat {chat['id']}: {ve_format}")
                    chat['last_activity_formatted'] = str(chat['last_activity'])
            else:
                chat['last_activity_formatted'] = "Keine Aktivität"
        return chat_list
    except Exception as e:
        logger.error(f"Postgres-Fehler beim Abrufen der Chats für Benutzer {user_id}: {e}", exc_info=True)
        return []
    finally:
        if conn: connection_pool.putconn(conn)

def ensure_user_in_default_chat(user_id):
    logger.info(f"ensure_user_in_default_chat (Postgres) aufgerufen für Benutzer ID: {user_id}")
    conn, error = get_db_connection(None)
    if error:
        logger.error(f"Fehler beim Abrufen der Datenbankverbindung: {error}")
        return False
    if conn is None:
        logger.error("Datenbankverbindung fehlgeschlagen")
        return False
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("SELECT id FROM chat_rooms WHERE name = 'General' LIMIT 1")
        default_chat_row = cursor.fetchone()
        default_chat_id = None
        if not default_chat_row:
            logger.info("Postgres Standard-Chat 'General' nicht gefunden. Erstelle ihn.")
            cursor.execute("INSERT INTO chat_rooms (name) VALUES ('General') RETURNING id")
            default_chat_id = cursor.fetchone()['id']
            conn.commit()
        else:
            default_chat_id = default_chat_row['id']
        cursor.execute("SELECT 1 FROM chat_room_participants WHERE chat_room_id = %s AND user_id = %s", (default_chat_id, user_id))
        if not cursor.fetchone():
            logger.info(f"Benutzer {user_id} ist nicht im Postgres Standard-Chat {default_chat_id}. Füge hinzu.")
            cursor.execute("INSERT INTO chat_room_participants (chat_room_id, user_id) VALUES (%s, %s)", (default_chat_id, user_id))
            conn.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Postgres-Fehler beim Hinzufügen/Prüfen des Benutzers {user_id} zum Standard-Chat: {e}", exc_info=True)
        if conn: conn.rollback()
        return False
    finally:
        if conn: connection_pool.putconn(conn)

def get_default_chat_id():
    logger.info("get_default_chat_id (Postgres) aufgerufen.")
    conn, error = get_db_connection(None)
    if error:
        logger.error(f"Fehler beim Abrufen der Datenbankverbindung: {error}")
        return None
    if conn is None:
        logger.error("Datenbankverbindung fehlgeschlagen")
        return None
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("SELECT id FROM chat_rooms WHERE name = 'General' LIMIT 1")
        row = cursor.fetchone()
        if row:
            return row['id']
        return None
    except Exception as e:
        logger.error(f"Postgres-Fehler beim Abrufen des Standard-Chats: {e}", exc_info=True)
        return None
    finally:
        if conn: connection_pool.putconn(conn)

def get_chat_by_id(chat_id):
    logger.info(f"get_chat_by_id (Postgres) aufgerufen für Chat ID: {chat_id}")
    if not is_int(chat_id):
        logger.warning(f"get_chat_by_id: Chat-ID '{chat_id}' ist kein Integer. Breche ab.")
        return None
    conn, error = get_db_connection(None)
    if error:
        logger.error(f"Fehler beim Abrufen der Datenbankverbindung: {error}")
        return None
    if conn is None:
        logger.error("Datenbankverbindung fehlgeschlagen")
        return None
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("SELECT * FROM chat_rooms WHERE id = %s", (int(chat_id),))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except Exception as e:
        logger.error(f"Postgres-Fehler beim Abrufen des Chats {chat_id}: {e}", exc_info=True)
        return None
    finally:
        if conn: connection_pool.putconn(conn)

def is_chat_participant(chat_id, user_id):
    logger.info(f"is_chat_participant (Postgres) aufgerufen für Chat ID: {chat_id}, Benutzer ID: {user_id}")
    if not is_int(chat_id) or not is_int(user_id):
        logger.warning(f"is_chat_participant: Chat-ID '{chat_id}' oder User-ID '{user_id}' ist kein Integer. Breche ab.")
        return False
    conn, error = get_db_connection(None)
    if error:
        logger.error(f"Fehler beim Abrufen der Datenbankverbindung: {error}")
        return False
    if conn is None:
        logger.error("Datenbankverbindung fehlgeschlagen")
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM chat_room_participants WHERE chat_room_id = %s AND user_id = %s", (int(chat_id), int(user_id)))
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Postgres-Fehler bei Teilnahmeprüfung (Chat {chat_id}, Benutzer {user_id}): {e}", exc_info=True)
        return False
    finally:
        if conn: connection_pool.putconn(conn)

def join_chat(chat_id, user_id):
    logger.info(f"join_chat (Postgres) aufgerufen für Chat ID: {chat_id}, Benutzer ID: {user_id}")
    if not is_int(chat_id) or not is_int(user_id):
        logger.warning(f"join_chat: Chat-ID '{chat_id}' oder User-ID '{user_id}' ist kein Integer. Breche ab.")
        return False
    if is_chat_participant(chat_id, user_id):
        logger.info(f"Benutzer {user_id} ist bereits Teilnehmer in Postgres Chat {chat_id}.")
        return True
    conn, error = get_db_connection(None)
    if error:
        logger.error(f"Fehler beim Abrufen der Datenbankverbindung: {error}")
        return False
    if conn is None:
        logger.error("Datenbankverbindung fehlgeschlagen")
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO chat_room_participants (chat_room_id, user_id) VALUES (%s, %s)", (int(chat_id), int(user_id)))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Postgres-Fehler beim Hinzufügen des Benutzers {user_id} zu Chat {chat_id}: {e}", exc_info=True)
        if conn: conn.rollback()
        return False
    finally:
        if conn: connection_pool.putconn(conn)

def save_chat_message(request, user_id, message, username, room_id="default_room"):
    conn, error = get_db_connection(request)
    if error:
        return False, error
    if conn is None:
        return False, "Database connection failed"
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO messages (user_id, message_text, username, chat_room_id) VALUES (%s, %s, %s, %s)",
            (user_id, message, username, room_id)
        )
        conn.commit()
        return True, None
    except Exception as e:
        logger.error(f"Postgres-Fehler beim Speichern der Nachricht: {e}", exc_info=True)
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: connection_pool.putconn(conn)

def get_chat_messages(request, room_id="default_room", limit=50):
    conn, error = get_db_connection(request)
    if error:
        return [], error
    if conn is None:
        return [], "Database connection failed"
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute(
            "SELECT * FROM messages WHERE chat_room_id = %s ORDER BY sent_at DESC LIMIT %s",
            (room_id, limit)
        )
        messages = cursor.fetchall()
        return messages, None
    except Exception as e:
        logger.error(f"Postgres-Fehler beim Abrufen der Nachrichten: {e}", exc_info=True)
        return [], str(e)
    finally:
        if conn: connection_pool.putconn(conn)
