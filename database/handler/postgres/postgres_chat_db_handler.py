import psycopg2
import psycopg2.extras
import logging
from datetime import datetime
import os
from rich import print
from .postgres_db_handler import add_analytics

logger = logging.getLogger(__name__)

def is_int(val):
    # Internal helper, analytics not typically added.
    try:
        int(val)
        return True
    except (TypeError, ValueError):
        return False

def get_db_connection():
    """Verbindung zur PostgreSQL-Datenbank herstellen"""
    print('[bold blue]Connection to DB from Chat Handler[/bold blue]')
    add_analytics(None, "get_db_connection_chat_handler", "postgres_chat_db_handler:get_db_connection")
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            dbname=os.getenv('POSTGRES_DB')
        )
        return conn
    except Exception as e:
        logger.error(f"Fehler beim Öffnen der PostgreSQL-Verbindung: {e}", exc_info=True)
        add_analytics(None, "get_db_connection_chat_handler_error", f"postgres_chat_db_handler:get_db_connection:error={e}")
        raise

def get_user_chats(user_id):
    logger.info(f"get_user_chats (Postgres) aufgerufen für Benutzer ID: {user_id}")
    add_analytics(user_id, "get_user_chats", "postgres_chat_db_handler")
    ensure_user_in_default_chat(user_id)
    conn = get_db_connection()
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
        if conn: conn.close()

def ensure_user_in_default_chat(user_id):
    logger.info(f"ensure_user_in_default_chat (Postgres) aufgerufen für Benutzer ID: {user_id}")
    add_analytics(user_id, "ensure_user_in_default_chat", "postgres_chat_db_handler")
    conn = get_db_connection()
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
        if conn: conn.close()

def get_default_chat_id():
    logger.info("get_default_chat_id (Postgres) aufgerufen.")
    add_analytics(None, "get_default_chat_id", "postgres_chat_db_handler")
    conn = get_db_connection()
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
        if conn: conn.close()

def get_chat_by_id(chat_id):
    logger.info(f"get_chat_by_id (Postgres) aufgerufen für Chat ID: {chat_id}")
    add_analytics(None, "get_chat_by_id", f"postgres_chat_db_handler:chat_id={chat_id}")
    if not is_int(chat_id):
        logger.warning(f"get_chat_by_id: Chat-ID '{chat_id}' ist kein Integer. Breche ab.")
        return None
    conn = get_db_connection()
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
        if conn: conn.close()

def is_chat_participant(chat_id, user_id):
    logger.info(f"is_chat_participant (Postgres) aufgerufen für Chat ID: {chat_id}, Benutzer ID: {user_id}")
    add_analytics(user_id, "is_chat_participant", f"postgres_chat_db_handler:chat_id={chat_id}")
    if not is_int(chat_id) or not is_int(user_id):
        logger.warning(f"is_chat_participant: Chat-ID '{chat_id}' oder User-ID '{user_id}' ist kein Integer. Breche ab.")
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM chat_room_participants WHERE chat_room_id = %s AND user_id = %s", (int(chat_id), int(user_id)))
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Postgres-Fehler bei Teilnahmeprüfung (Chat {chat_id}, Benutzer {user_id}): {e}", exc_info=True)
        return False
    finally:
        if conn: conn.close()

def join_chat(chat_id, user_id):
    logger.info(f"join_chat (Postgres) aufgerufen für Chat ID: {chat_id}, Benutzer ID: {user_id}")
    add_analytics(user_id, "join_chat", f"postgres_chat_db_handler:chat_id={chat_id}")
    if not is_int(chat_id) or not is_int(user_id):
        logger.warning(f"join_chat: Chat-ID '{chat_id}' oder User-ID '{user_id}' ist kein Integer. Breche ab.")
        return False
    if is_chat_participant(chat_id, user_id):
        logger.info(f"Benutzer {user_id} ist bereits Teilnehmer in Postgres Chat {chat_id}.")
        return True
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO chat_room_participants (chat_room_id, user_id) VALUES (%s, %s)", (int(chat_id), int(user_id)))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Postgres-Fehler beim Beitreten zum Chat {chat_id} für Benutzer {user_id}: {e}", exc_info=True)
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

def create_chat(chat_name, user_id):
    logger.info(f"create_chat (Postgres) aufgerufen: Name='{chat_name}', Ersteller-ID={user_id}")
    add_analytics(user_id, "create_chat", f"postgres_chat_db_handler:chat_name={chat_name}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN")
        cursor.execute("INSERT INTO chat_rooms (name, created_by) VALUES (%s, %s) RETURNING id", (chat_name, user_id))
        new_chat_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO chat_room_participants (chat_room_id, user_id) VALUES (%s, %s)", (new_chat_id, user_id))
        conn.commit()
        return new_chat_id
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Postgres-Fehler beim Erstellen des Chats '{chat_name}' für Benutzer {user_id}: {e}", exc_info=True)
        return None
    finally:
        if conn: conn.close()

def add_message_and_get_details(chat_id, user_id, message_text):
    logger.info(f"add_message_and_get_details (Postgres): ChatID={chat_id}, UserID={user_id}, Nachricht (gekürzt)='{message_text[:50]}'")
    add_analytics(user_id, "add_message_and_get_details", f"postgres_chat_db_handler:chat_id={chat_id}")
    if not is_int(chat_id) or not is_int(user_id):
        logger.warning(f"add_message_and_get_details: Chat-ID '{chat_id}' oder User-ID '{user_id}' ist kein Integer. Breche ab.")
        return None
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        sent_at_dt = datetime.utcnow()
        sent_at_pg = sent_at_dt.strftime('%Y-%m-%d %H:%M:%S')
        sent_at_iso = sent_at_dt.isoformat() + "Z"
        cursor.execute(
            "INSERT INTO messages (chat_room_id, user_id, message_text, sent_at) VALUES (%s, %s, %s, %s) RETURNING id",
            (int(chat_id), int(user_id), message_text, sent_at_pg)
        )
        message_id = cursor.fetchone()['id']
        conn.commit()
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user_row = cursor.fetchone()
        sender_name = user_row['username'] if user_row else "Unbekannt"
        message_details = {
            'id': message_id,
            'chat_room_id': str(chat_id),
            'user_id': str(user_id),
            'username': sender_name,
            'message_text': message_text,
            'sent_at': sent_at_iso
        }
        return message_details
    except Exception as e:
        logger.error(f"Postgres-Fehler beim Hinzufügen und Abrufen einer Nachricht für Chat {chat_id}: {e}", exc_info=True)
        if conn: conn.rollback()
        return None
    finally:
        if conn: conn.close()

def get_chat_messages(chat_id, limit=50, offset=0):
    logger.info(f"get_chat_messages (Postgres): ChatID={chat_id}, Limit={limit}, Offset={offset}")
    add_analytics(None, "get_chat_messages", f"postgres_chat_db_handler:chat_id={chat_id}")
    if not is_int(chat_id):
        logger.warning(f"get_chat_messages: Chat-ID '{chat_id}' ist kein Integer. Breche ab.")
        return []
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = """
            SELECT m.id, m.message_text, m.sent_at, m.user_id,
                   u.username
            FROM messages m
            JOIN users u ON m.user_id = u.id
            WHERE m.chat_room_id = %s
            ORDER BY m.sent_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (int(chat_id), limit, offset))
        messages = cursor.fetchall()
        for msg in messages:
            if msg.get('sent_at'):
                if isinstance(msg['sent_at'], datetime):
                    msg['sent_at'] = msg['sent_at'].isoformat() + "Z"
                elif isinstance(msg['sent_at'], str):
                    try:
                        dt_obj = datetime.strptime(msg['sent_at'], '%Y-%m-%d %H:%M:%S')
                        msg['sent_at'] = dt_obj.isoformat() + "Z"
                    except Exception:
                        pass
            msg['id'] = str(msg.get('id'))
            msg['user_id'] = str(msg.get('user_id'))
            msg['chat_room_id'] = str(chat_id)
        messages.reverse()
        return messages
    except Exception as e:
        logger.error(f"Postgres-Fehler beim Abrufen der Nachrichten für Chat {chat_id}: {e}", exc_info=True)
        return []
    finally:
        if conn: conn.close()

def delete_chat(chat_id):
    logger.info(f"delete_chat (Postgres) aufgerufen für Chat ID: {chat_id}")
    add_analytics(None, "delete_chat", f"postgres_chat_db_handler:chat_id={chat_id}")
    if not is_int(chat_id):
        logger.warning(f"delete_chat: Chat-ID '{chat_id}' ist kein Integer. Breche ab.")
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN")
        cursor.execute("DELETE FROM messages WHERE chat_room_id = %s", (int(chat_id),))
        cursor.execute("DELETE FROM chat_room_participants WHERE chat_room_id = %s", (int(chat_id),))
        cursor.execute("DELETE FROM chat_rooms WHERE id = %s", (int(chat_id),))
        conn.commit()
        return True
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Postgres-Fehler beim Löschen des Chats {chat_id}: {e}", exc_info=True)
        return False
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    import random
    import string

    print("Starte Unittests für postgres_chat_db_handler.py ...")
    try:
        # Optional: Sequenz für chat_rooms.id reparieren (nur für Testzwecke)
        def fix_chat_rooms_sequence():
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute("SELECT MAX(id) FROM chat_rooms")
                max_id = cur.fetchone()[0] or 0
                cur.execute("SELECT pg_get_serial_sequence('chat_rooms', 'id')")
                seq_name = cur.fetchone()[0]
                if seq_name:
                    cur.execute(f"SELECT setval(%s, %s, true)", (seq_name, max_id))
                    conn.commit()
                    print(f"Sequenz {seq_name} auf {max_id} gesetzt.")
            except Exception as e:
                print(f"Fehler beim Reparieren der chat_rooms-Sequenz: {e}")
            finally:
                cur.close()
                conn.close()

        fix_chat_rooms_sequence()
        # Testdaten generieren
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        test_user_id = 1  # Passe ggf. an, falls User mit ID 1 nicht existiert
        chat_name = f"TestChat_{rand_str}"

        # Chat anlegen
        print(f"Lege Testchat an: {chat_name}")
        chat_id = create_chat(chat_name, test_user_id)
        assert chat_id, "create_chat fehlgeschlagen"
        print(f"Chat erstellt mit ID: {chat_id}")

        # Chat beitreten (nochmal, sollte True zurückgeben)
        joined = join_chat(chat_id, test_user_id)
        assert joined, "join_chat fehlgeschlagen"
        print(f"User {test_user_id} ist Chat {chat_id} beigetreten.")

        # Nachricht senden
        msg_text = f"Testnachricht {rand_str}"
        msg = add_message_and_get_details(chat_id, test_user_id, msg_text)
        assert msg, "add_message_and_get_details fehlgeschlagen"
        print(f"Nachricht gesendet: {msg}")

        # Nachrichten abrufen
        messages = get_chat_messages(chat_id)
        assert isinstance(messages, list) and len(messages) > 0, "get_chat_messages fehlgeschlagen"
        print(f"Nachrichten im Chat {chat_id}: {messages}")

        # Chat löschen
        deleted = delete_chat(chat_id)
        assert deleted, "delete_chat fehlgeschlagen"
        print(f"Chat {chat_id} gelöscht.")

        print("Alle Chat-Tests erfolgreich abgeschlossen.")
    except Exception as e:
        print(f"Fehler beim Testen von postgres_chat_db_handler.py: {e}")
