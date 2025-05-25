import os  # Dieser Import fehlte
import psycopg2
import psycopg2.extras
from psycopg2 import pool
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

connection_pool = psycopg2.pool.SimpleConnectionPool(1, 20,
    host=PG_HOST,
    port=PG_PORT,
    dbname=PG_DB,
    user=PG_USER,
    password=PG_PASSWORD
)

def get_db_connection(request):
    print('[bold blue]Connection to DB from Education Handler[/bold blue]')
    """Stellt eine Verbindung zur PostgreSQL-Datenbank her."""
    try:
        connection = connection_pool.getconn()
        return connection
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


def get_daily_quiz(date):
    """Lädt das tägliche Quiz für ein bestimmtes Datum aus der PostgreSQL-Datenbank."""
    try:
        conn = get_db_connection(None)
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM daily_quiz WHERE date = %s", (date,))
            quiz_data = cursor.fetchone()
            return dict(quiz_data) if quiz_data else None
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen des täglichen Quiz für das Datum {date}: {e}", exc_info=True)
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)

def insert_daily_quiz_attempt(user_id, quiz_id, selected_answer, is_correct):
    """
    Fügt einen neuen Eintrag in die Tabelle daily_quiz_attempts ein.
    """
    try:
        conn = get_db_connection(None)
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO daily_quiz_attempts (user_id, quiz_id, selected_answer, is_correct)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, quiz_id) DO NOTHING
            """, (user_id, quiz_id, selected_answer, is_correct))
            conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Einfügen eines Quiz-Versuchs: {e}", exc_info=True)
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)

def get_daily_quiz_attempts(user_id):
    """
    Lädt alle täglichen Quizversuche eines Benutzers aus der PostgreSQL-Datenbank.
    """
    try:
        conn = get_db_connection(None)
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM daily_quiz_attempts WHERE user_id = %s
            """, (user_id,))
            attempts = cursor.fetchall()
            return [dict(attempt) for attempt in attempts]
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen der täglichen Quizversuche für Benutzer {user_id}: {e}", exc_info=True)
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)


def create_daily_quiz(date, question, possible_answer_1, possible_answer_2, possible_answer_3, correct_answer):
    """
    Erstellt ein neues tägliches Quiz in der PostgreSQL-Datenbank.
    """
    try:
        conn = get_db_connection(None)
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO daily_quiz (date, question, possible_answer_1, possible_answer_2, possible_answer_3, correct_answer)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (date, question, possible_answer_1, possible_answer_2, possible_answer_3, correct_answer))
            conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Erstellen des täglichen Quiz: {e}", exc_info=True)
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)

def get_all_daily_quizzes():
    """
    Lädt alle täglichen Quiz aus der PostgreSQL-Datenbank.
    """
    try:
        conn = get_db_connection(None)
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM daily_quiz")
            quizzes = cursor.fetchall()
            return [dict(quiz) for quiz in quizzes]
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen aller täglichen Quiz: {e}", exc_info=True)
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)

def delete_daily_quiz(quiz_id):
    """
    Löscht ein tägliches Quiz aus der PostgreSQL-Datenbank.
    """
    try:
        conn = get_db_connection(None)
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM daily_quiz WHERE id = %s", (quiz_id,))
            conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Löschen des täglichen Quiz mit ID {quiz_id}: {e}", exc_info=True)
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)

def get_dayly_quiz_attempt_day(user_id, date):
    """
    Lädt den täglichen Quizversuch eines Benutzers für ein bestimmtes Datum aus der PostgreSQL-Datenbank.
    """
    try:
        conn = get_db_connection(None)
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # Assuming 'attempted_at' is a timestamp or date column in daily_quiz_attempts
            # and 'quiz_id' in daily_quiz_attempts refers to 'id' in daily_quiz
            # Removed dq.possible_answers from the SELECT statement
            cursor.execute("""
                SELECT dqa.*, dq.question, dq.correct_answer, dq.explanation, dq.category
                FROM daily_quiz_attempts dqa
                JOIN daily_quiz dq ON dqa.quiz_id = dq.id
                WHERE dqa.user_id = %s AND DATE(dq.date) = %s
                ORDER BY dqa.attempted_at DESC
                LIMIT 1
            """, (user_id, date))
            attempt = cursor.fetchone()
            return dict(attempt) if attempt else None
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen des täglichen Quizversuchs für Benutzer {user_id} am Datum {date}: {e}", exc_info=True)
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)
