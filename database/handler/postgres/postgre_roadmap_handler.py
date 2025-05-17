import os  # Dieser Import fehlte
import psycopg2
import psycopg2.extras
from datetime import datetime
import logging
from rich import print

logger = logging.getLogger(__name__)

# PostgreSQL-Verbindungsdetails aus .env
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = os.getenv('POSTGRES_PORT', '5432')
PG_DB = os.getenv('POSTGRES_DB', 'buyhigh')
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')

def get_db_connection():
    print('[bold blue]Connection to DB from Education Handler[/bold blue]')
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

def get_roadmap(id):
    """Lädt die Roadmap mit der angegebenen ID aus der Datenbank."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM roadmap WHERE id = %s", (id,))
            roadmap = cursor.fetchone()
            if roadmap:
                return dict(roadmap)
            else:
                logger.warning(f"Roadmap mit ID {id} nicht gefunden.")
                return None
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen der Roadmap: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_roadmap_steps(roadmap_id):
    """Lädt die Schritte der Roadmap mit der angegebenen ID aus der Datenbank."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM roadmap_steps WHERE roadmap_id = %s", (roadmap_id,))
            steps = cursor.fetchall()
            return [dict(step) for step in steps]
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen der Roadmap-Schritte: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_roadmap_quizes_roadmapid(roadmap_id):
    """Lädt die Quizze für eine bestimmte Roadmap-ID."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM roadmap_quizzes WHERE roadmap_id = %s", (roadmap_id,))
            quizzes = cursor.fetchall()
            return [dict(quiz) for quiz in quizzes]
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen der Roadmap-Quizze: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_roadmap_quizes_stepid(roadmap_step):
    """Lädt die Quizze für einen bestimmten Roadmap-Schritt."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM roadmap_quizzes WHERE step_id = %s", (roadmap_step,))
            quizzes = cursor.fetchall()
            return [dict(quiz) for quiz in quizzes]
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen der Roadmap-Quizze: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_user_progress_for_quizzes(user_id, quiz_ids):
    """
    Lädt den Fortschritt eines Benutzers für eine gegebene Liste von Quiz-IDs.
    Gibt ein Dictionary zurück, das quiz_id auf {'attempted': bool, 'is_correct': bool} abbildet.
    """
    if not quiz_ids:
        return {}
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # Erstelle eine Platzhalter-Zeichenkette für die IN-Klausel: (%s, %s, ...)
            placeholders = ', '.join(['%s'] * len(quiz_ids))
            sql_query = f"""
            SELECT 
                quiz_id,
                is_correct,
                attempted_at IS NOT NULL as attempted
            FROM user_roadmap_quiz_progress
            WHERE user_id = %s AND quiz_id IN ({placeholders});
            """
            # Die Parameterliste muss user_id zuerst enthalten, dann die quiz_ids
            params = [user_id] + quiz_ids
            cursor.execute(sql_query, tuple(params))
            progress_data = cursor.fetchall()
            
            user_progress = {}
            for row in progress_data:
                user_progress[row['quiz_id']] = {
                    'attempted': row['attempted'],
                    'is_correct': row['is_correct']
                }
            return user_progress
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen des Benutzerfortschritts für Quizze: {e}", exc_info=True)
        return {} # Im Fehlerfall leeres Dictionary zurückgeben, um den Rest der Logik nicht zu blockieren
    finally:
        conn.close()

def get_quiz_by_id(quiz_id):
    """Lädt ein einzelnes Quiz anhand seiner ID."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM roadmap_quizzes WHERE id = %s", (quiz_id,))
            quiz = cursor.fetchone()
            if quiz:
                return dict(quiz)
            return None
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen des Quiz mit ID {quiz_id}: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def record_user_quiz_attempt(user_id, quiz_id, is_correct):
    """Speichert den Quiz-Versuch eines Benutzers oder aktualisiert ihn."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Versuche, einen vorhandenen Eintrag zu aktualisieren oder einen neuen einzufügen
            sql_query = """
            INSERT INTO user_roadmap_quiz_progress (user_id, quiz_id, is_correct, attempted_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, quiz_id) DO UPDATE SET
                is_correct = EXCLUDED.is_correct,
                attempted_at = CURRENT_TIMESTAMP;
            """
            cursor.execute(sql_query, (user_id, quiz_id, is_correct))
            conn.commit()
            logger.info(f"Quiz-Versuch für Benutzer {user_id}, Quiz {quiz_id} gespeichert. Korrekt: {is_correct}")
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Speichern des Quiz-Versuchs für Benutzer {user_id}, Quiz {quiz_id}: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_xp_for_action(action_name):
    """Ruft den XP-Betrag für eine bestimmte Aktion ab."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT xp_amount FROM xp_gains WHERE action = %s", (action_name,))
            result = cursor.fetchone()
            if result:
                return result['xp_amount']
            logger.warning(f"Kein XP-Betrag für Aktion '{action_name}' in xp_gains gefunden.")
            return 0  # Standardwert, falls Aktion nicht gefunden wird
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen von XP für Aktion {action_name}: {e}", exc_info=True)
        return 0 # Im Fehlerfall 0 zurückgeben
    finally:
        conn.close()

def add_xp_to_user(user_id, xp_to_add):
    """Fügt einem Benutzer XP hinzu und aktualisiert sein Level, falls erforderlich."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # Aktuelle XP und Level des Benutzers abrufen
            cursor.execute("SELECT xp, level FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            if not user_data:
                logger.error(f"Benutzer mit ID {user_id} nicht gefunden für XP-Update.")
                return

            current_xp = user_data['xp']
            current_level = user_data['level']
            new_xp = current_xp + xp_to_add

            # Alle XP-Level abrufen, um das neue Level zu bestimmen
            cursor.execute("SELECT level, xp_required FROM xp_levels ORDER BY level DESC")
            levels = cursor.fetchall()
            
            new_level = current_level
            for level_info in levels:
                if new_xp >= level_info['xp_required']:
                    new_level = level_info['level']
                    break 
            
            # Benutzer-XP und Level aktualisieren
            cursor.execute("UPDATE users SET xp = %s, level = %s WHERE id = %s", (new_xp, new_level, user_id))
            conn.commit()
            logger.info(f"Benutzer {user_id}: {xp_to_add} XP hinzugefügt. Neues XP: {new_xp}, Neues Level: {new_level}")
            
            xp_info = {"added_xp": xp_to_add, "total_xp": new_xp, "old_level": current_level, "new_level": new_level}
            if new_level > current_level:
                xp_info["level_up"] = True
            return xp_info

    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Hinzufügen von XP zu Benutzer {user_id}: {e}", exc_info=True)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    #print(get_roadmap(1))
    print(get_roadmap_steps(1))
    #print(get_roadmap_quizes_stepid(1))
    #print(get_roadmap_quizes_roadmapid(1))