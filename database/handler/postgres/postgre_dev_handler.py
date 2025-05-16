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
    print('[bold blue]Connection to DB from DEV Handler[/bold blue]')
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

def get_total_user_count():
    """Gibt die Gesamtanzahl der Benutzer in der Datenbank zurück."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users")
                total_users = cur.fetchone()[0]
                print(f'[dark orange3]SQL: SELECT COUNT(*) FROM users -> {total_users}[/]')
                return total_users
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Gesamtanzahl der Benutzer: {e}", exc_info=True)
        raise

def get_all_tables():
    """Gibt eine Liste aller Tabellen in der Datenbank zurück."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                tables = [row[0] for row in cur.fetchall()]
                print(f'[dark orange3]SQL: SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\' -> {tables}[/]')
                return tables
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Tabellen: {e}", exc_info=True)
        raise


def get_table_data(table_name):
    """Gibt die Daten einer bestimmten Tabelle zurück."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(f"SELECT * FROM {table_name}")
                rows = cur.fetchall()
                print(f'[dark orange3]SQL: SELECT * FROM {table_name} -> {rows}[/]')
                return rows
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Daten aus der Tabelle {table_name}: {e}", exc_info=True)
        raise

def get_db_size():
    """Gibt die Größe der Datenbank und die Anzahl der Tabellen zurück."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Datenbankgröße abfragen
                cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                db_size = cur.fetchone()[0]
                print(f'[dark orange3]SQL: SELECT pg_size_pretty(pg_database_size(current_database())) -> {db_size}[/]')

                # Tabellenanzahl abfragen
                cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
                table_count = cur.fetchone()[0]
                print(f'[dark orange3]SQL: SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = \'public\' -> {table_count}[/]')

                return {
                    "db_size": db_size,
                    "table_count": table_count
                }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Datenbankgröße oder Tabellenanzahl: {e}", exc_info=True)
        raise

def get_api_calls():
    """Gibt die Anzahl der API-Aufrufe und den Minuten-Durchschnitt zurück."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Gesamtanzahl der API-Aufrufe
                cur.execute("SELECT COUNT(*) FROM api_requests")
                api_calls = cur.fetchone()[0]
                print(f'[dark orange3]SQL: SELECT COUNT(*) FROM api_requests -> {api_calls}[/]')

                # Prüfe, ob eine Zeitspalte existiert
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'api_requests'
                """)
                columns = [row[0] for row in cur.fetchall()]
                # Suche nach einer passenden Zeitspalte
                time_column = None
                for candidate in ['request_time', 'created_at', 'timestamp', 'time', 'date']:
                    if candidate in columns:
                        time_column = candidate
                        break

                if time_column:
                    # Durchschnittliche API-Aufrufe pro Minute berechnen
                    cur.execute(f"""
                        SELECT 
                            CASE 
                                WHEN COUNT(*) = 0 THEN 0
                                ELSE COUNT(*)::float / NULLIF(EXTRACT(EPOCH FROM (MAX({time_column}) - MIN({time_column}))) / 60, 0)
                            END as avg_per_minute
                        FROM api_requests
                    """)
                    avg_per_minute = cur.fetchone()[0]
                    print(f'[dark orange3]SQL: AVG per minute ({time_column}) -> {avg_per_minute}[/]')
                else:
                    logger.warning("Keine Zeitspalte in api_requests gefunden, avg_per_minute wird auf None gesetzt.")
                    avg_per_minute = None

                return {
                    "api_calls": api_calls,
                    "avg_per_minute": avg_per_minute
                }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der API-Aufrufe: {e}", exc_info=True)
        raise

def delete_user(user_id):
    """Löscht einen Benutzer aus der Datenbank."""
    print(f'[bold red]Lösche Benutzer mit ID: {user_id}[/]')
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
                conn.commit()
                print(f'[red]SQL: DELETE FROM users WHERE id = {user_id}[/]')
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Benutzers mit ID {user_id}: {e}", exc_info=True)
        raise