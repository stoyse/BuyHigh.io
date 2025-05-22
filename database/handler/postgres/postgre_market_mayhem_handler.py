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
    print('[bold blue]Connection to DB from Market Mayhem Handler[/bold blue]')
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

def get_all_mayhem():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM market_mayhem")
                mayhem_data = cur.fetchall()
                # Convert to list of dicts
                colnames = [desc[0] for desc in cur.description]
                mayhem_data = [dict(zip(colnames, row)) for row in mayhem_data]
                return mayhem_data
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Marktdaten: {e}", exc_info=True)
        raise

def get_all_mayhem_scenarios():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM market_mayhem_scenarios")
                mayhem_data = cur.fetchall()
                # Convert to list of dicts
                colnames = [desc[0] for desc in cur.description]
                mayhem_data = [dict(zip(colnames, row)) for row in mayhem_data]
                return mayhem_data
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Marktdaten: {e}", exc_info=True)
        raise

def get_mayhem_data(scenario_id):
    data = {}
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM market_mayhem_scenarios WHERE id = %s", (scenario_id,))
                mayhem_data = cur.fetchone()
                if mayhem_data:
                    colnames = [desc[0] for desc in cur.description]
                    data = dict(zip(colnames, mayhem_data))
                else:
                    print(f"No data found for scenario ID {scenario_id}.")
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Marktdaten für Szenario {scenario_id}: {e}", exc_info=True)
        raise
    return data    

def check_if_mayhem():
    data = get_all_mayhem()
    today = datetime.now().strftime('%Y-%m-%d')  # Get today's date as a string
    events = {}
    for row in data:
        # Extract the date part from start_time
        start_date = row['start_time'].strftime('%Y-%m-%d') if isinstance(row['start_time'], datetime.datetime) else row['start_time'][:10]
        if start_date == today:
            events[row['id']] = row
            mayhem_scenarios = get_mayhem_data(scenario_id=events[row['id']]['scenario_id'])
            if mayhem_scenarios:
                events[row['id']]['mayhem_scenarios'] = mayhem_scenarios
            else:
                print(f"No scenarios found for event ID {row['id']}.")
    return events

def schedule_mayhem(scenario_id, start_time=None, end_time=None, result=None):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                now = datetime.datetime.now()
                
                # Use provided parameters or defaults
                start_time = datetime.datetime.fromisoformat(start_time) if start_time else now
                end_time = datetime.datetime.fromisoformat(end_time) if end_time else now
                
                cur.execute("""
                    INSERT INTO market_mayhem (scenario_id, start_time, end_time, result, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (scenario_id, start_time, end_time, result, now))
                new_id = cur.fetchone()[0]
                conn.commit()
                return new_id
    except Exception as e:
        logger.error(f"Error in market mayhem handler: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the connection and query
    print(check_if_mayhem())