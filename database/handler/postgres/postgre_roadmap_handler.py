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


if __name__ == "__main__":
    #print(get_roadmap(1))
    print(get_roadmap_steps(1))
    #print(get_roadmap_quizes_stepid(1))
    #print(get_roadmap_quizes_roadmapid(1))