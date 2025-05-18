import os
import psycopg2
import psycopg2.extras
from datetime import datetime
import logging
from rich import print
from database.handler.postgres.postgres_db_handler import add_analytics

logger = logging.getLogger(__name__)

# PostgreSQL-Verbindungsdetails aus .env
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = os.getenv('POSTGRES_PORT', '5432')
PG_DB = os.getenv('POSTGRES_DB', 'buyhigh')
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')

def get_db_connection():
    print('[bold blue]Connection to DB from Roadmap Handler[/bold blue]') # Corrected from Education Handler
    """Stellt eine Verbindung zur PostgreSQL-Datenbank her."""
    add_analytics(None, "get_db_connection_roadmap_handler", "postgre_roadmap_handler:get_db_connection")
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
        add_analytics(None, "get_db_connection_roadmap_handler_error", f"postgre_roadmap_handler:get_db_connection:error={e}")
        raise

def get_roadmap(id):
    """Lädt die Roadmap mit der angegebenen ID aus der Datenbank."""
    add_analytics(None, "get_roadmap", f"postgre_roadmap_handler:id={id}")
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
    add_analytics(None, "get_roadmap_steps", f"postgre_roadmap_handler:roadmap_id={roadmap_id}")
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
    add_analytics(None, "get_roadmap_quizes_roadmapid", f"postgre_roadmap_handler:roadmap_id={roadmap_id}")
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

def get_roadmap_quizes_stepid(roadmap_step, roadmap_id=None):
    """
    Lädt die Quizze für einen bestimmten Roadmap-Schritt.
    Optional kann eine roadmap_id angegeben werden, um die Ergebnisse weiter einzuschränken.
    """
    add_analytics(None, "get_roadmap_quizes_stepid", f"postgre_roadmap_handler:step_id={roadmap_step},roadmap_id={roadmap_id}")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            if roadmap_id is not None:
                # Präzisere Abfrage mit roadmap_id und step_id
                cursor.execute("SELECT * FROM roadmap_quizzes WHERE step_id = %s AND roadmap_id = %s", 
                              (roadmap_step, roadmap_id))
            else:
                # Ursprüngliche Abfrage nur mit step_id
                cursor.execute("SELECT * FROM roadmap_quizzes WHERE step_id = %s", (roadmap_step,))
            
            quizzes = cursor.fetchall()
            logger.info(f"Gefundene Quizze für step_id={roadmap_step}, roadmap_id={roadmap_id}: {len(quizzes)}")
            return [dict(quiz) for quiz in quizzes]
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen der Roadmap-Quizze: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_roadmap_quizes_specific(step_id, roadmap_id):
    """
    Lädt die Quizze für eine spezifische Kombination aus Roadmap-ID und Step-ID.
    Dies ist die präziseste Abfrage und sollte bevorzugt verwendet werden.
    """
    add_analytics(None, "get_roadmap_quizes_specific", f"postgre_roadmap_handler:step_id={step_id},roadmap_id={roadmap_id}")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM roadmap_quizzes 
                WHERE step_id = %s AND roadmap_id = %s
            """, (step_id, roadmap_id))
            
            quizzes = cursor.fetchall()
            logger.info(f"Gefundene Quizze für step_id={step_id}, roadmap_id={roadmap_id}: {len(quizzes)}")
            
            if len(quizzes) == 0:
                # Zur Diagnose: Überprüfe, ob es überhaupt Quizze für diese step_id gibt
                cursor.execute("SELECT COUNT(*) FROM roadmap_quizzes WHERE step_id = %s", (step_id,))
                count_by_step = cursor.fetchone()[0]
                
                # Überprüfe, ob es Quizze für diese roadmap_id gibt
                cursor.execute("SELECT COUNT(*) FROM roadmap_quizzes WHERE roadmap_id = %s", (roadmap_id,))
                count_by_roadmap = cursor.fetchone()[0]
                
                logger.warning(f"Keine Quizze gefunden für step_id={step_id}, roadmap_id={roadmap_id}. "
                              f"Einzeln gefunden: {count_by_step} für step_id, {count_by_roadmap} für roadmap_id")
                
            return [dict(quiz) for quiz in quizzes]
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen spezifischer Roadmap-Quizze: {e}", exc_info=True)
        return [] # Leere Liste im Fehlerfall zurückgeben
    finally:
        conn.close()

def check_and_fix_quiz_mappings():
    """Diagnostische Funktion zur Überprüfung und Reparatur inkonsistenter Quiz-Mappings."""
    add_analytics(None, "check_and_fix_quiz_mappings", "postgre_roadmap_handler")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # Überprüfe auf Quiz-Einträge, bei denen step_id nicht zu roadmap_id passt
            cursor.execute("""
                SELECT q.id, q.step_id, q.roadmap_id, s.roadmap_id AS expected_roadmap_id
                FROM roadmap_quizzes q
                LEFT JOIN roadmap_steps s ON q.step_id = s.id
                WHERE q.roadmap_id != s.roadmap_id OR s.id IS NULL
            """)
            
            inconsistent_quizzes = cursor.fetchall()
            
            if inconsistent_quizzes:
                logger.warning(f"Gefunden {len(inconsistent_quizzes)} inkonsistente Quiz-Mappings:")
                for quiz in inconsistent_quizzes:
                    logger.warning(f"Quiz ID: {quiz['id']}, step_id: {quiz['step_id']}, "
                                 f"aktuell roadmap_id: {quiz['roadmap_id']}, erwartet: {quiz['expected_roadmap_id']}")
                    
                    # Optional: Automatische Korrektur, wenn gewünscht
                    if quiz['expected_roadmap_id'] is not None:
                        cursor.execute("""
                            UPDATE roadmap_quizzes
                            SET roadmap_id = %s
                            WHERE id = %s
                        """, (quiz['expected_roadmap_id'], quiz['id']))
                        
                conn.commit()
                logger.info("Inkonsistente Quiz-Mappings wurden korrigiert.")
            else:
                logger.info("Keine inkonsistenten Quiz-Mappings gefunden.")
                
            return len(inconsistent_quizzes)
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler bei der Überprüfung/Reparatur der Quiz-Mappings: {e}", exc_info=True)
        return -1
    finally:
        conn.close()

def get_user_progress_for_quizzes(user_id, quiz_ids):
    """
    Lädt den Fortschritt eines Benutzers für eine gegebene Liste von Quiz-IDs.
    Gibt ein Dictionary zurück, das quiz_id auf {'attempted': bool, 'is_correct': bool} abbildet.
    """
    add_analytics(user_id, "get_user_progress_for_quizzes", f"postgre_roadmap_handler:quiz_count={len(quiz_ids)}")
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
    add_analytics(None, "get_quiz_by_id", f"postgre_roadmap_handler:quiz_id={quiz_id}")
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
    add_analytics(user_id, "record_user_quiz_attempt", f"postgre_roadmap_handler:quiz_id={quiz_id},correct={is_correct}")
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
    add_analytics(None, "get_xp_for_action", f"postgre_roadmap_handler:action={action_name}")
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
    add_analytics(user_id, "add_xp_to_user", f"postgre_roadmap_handler:xp_added={xp_to_add}")
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

def update_user_roadmap_step_progress(user_id, roadmap_id, step_id, is_completed, progress_percentage=None):
    """
    Aktualisiert den Fortschritt eines Benutzers für einen bestimmten Roadmap-Schritt.
    Setzt completed_at, wenn is_completed True ist.
    """
    add_analytics(user_id, "update_user_roadmap_step_progress", f"postgre_roadmap_handler:roadmap_id={roadmap_id},step_id={step_id},completed={is_completed}")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            completed_at_val = datetime.now() if is_completed else None
            
            # Wenn kein spezifischer Fortschrittsprozentsatz angegeben ist und der Schritt abgeschlossen ist, auf 100% setzen
            if progress_percentage is None and is_completed:
                progress_percentage = 100.0
            elif progress_percentage is None and not is_completed: # Falls nicht abgeschlossen und kein Wert, 0%
                progress_percentage = 0.0

            sql_query = """
            INSERT INTO user_roadmap_progress (user_id, roadmap_id, step_id, is_completed, progress_percentage, completed_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, roadmap_id, step_id) DO UPDATE SET
                is_completed = EXCLUDED.is_completed,
                progress_percentage = EXCLUDED.progress_percentage,
                completed_at = EXCLUDED.completed_at;
            """
            cursor.execute(sql_query, (user_id, roadmap_id, step_id, is_completed, progress_percentage, completed_at_val))
            conn.commit()
            logger.info(f"Fortschritt für Benutzer {user_id}, Roadmap {roadmap_id}, Schritt {step_id} aktualisiert. Abgeschlossen: {is_completed}, Fortschritt: {progress_percentage}%")
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Fehler beim Aktualisieren des Roadmap-Schritt-Fortschritts: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_user_roadmap_progress_all_steps(user_id, roadmap_id):
    """
    Ruft den Fortschritt aller Schritte einer Roadmap für einen bestimmten Benutzer ab.
    Gibt ein Dictionary zurück, das step_id auf {'is_completed': bool, 'progress_percentage': float} abbildet.
    """
    add_analytics(user_id, "get_user_roadmap_progress_all_steps", f"postgre_roadmap_handler:roadmap_id={roadmap_id}")
    conn = get_db_connection()
    progress_map = {}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT step_id, is_completed, progress_percentage 
                FROM user_roadmap_progress 
                WHERE user_id = %s AND roadmap_id = %s
            """, (user_id, roadmap_id))
            rows = cursor.fetchall()
            for row in rows:
                progress_map[row['step_id']] = {
                    'is_completed': row['is_completed'],
                    'progress_percentage': row['progress_percentage']
                }
        return progress_map
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen des gesamten Roadmap-Fortschritts für Benutzer {user_id}, Roadmap {roadmap_id}: {e}", exc_info=True)
        return {} # Leeres Dictionary im Fehlerfall
    finally:
        conn.close()

def get_roadmap_collection():
    """Lädt alle Roadmaps aus der Datenbank."""
    add_analytics(None, "get_roadmap_collection", "postgre_roadmap_handler")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM roadmap")
            roadmaps = cursor.fetchall()
            return [dict(roadmap) for roadmap in roadmaps]
    except psycopg2.Error as e:
        logger.error(f"Fehler beim Abrufen der Roadmap-Sammlung: {e}", exc_info=True)
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # Führen Sie eine Überprüfung und ggf. Korrektur der Quiz-Mappings durch
    print("[bold yellow]Überprüfung der Quiz-Mappings:[/bold yellow]")
    check_and_fix_quiz_mappings()
    print("-" * 50)

    # Beispiel-IDs für Tests
    EXAMPLE_WORKING_ROADMAP_ID = 1
    EXAMPLE_WORKING_STEP_ID = 1 # Dies ist roadmap_steps.id

    # Basierend auf vorherigen Logs als Beispiel für eine problematische Prüfung:
    EXAMPLE_PROBLEM_ROADMAP_ID = 3
    EXAMPLE_PROBLEM_STEP_ID = 4 # Dies ist roadmap_steps.id

    # --- Test für funktionierendes Beispiel ---
    print(f"[bold green]Test für Roadmap {EXAMPLE_WORKING_ROADMAP_ID} (funktionierendes Beispiel):[/bold green]")
    roadmap_working = get_roadmap(EXAMPLE_WORKING_ROADMAP_ID)
    if roadmap_working:
        print(f"Roadmap {EXAMPLE_WORKING_ROADMAP_ID}: {roadmap_working}")
        steps_working_roadmap = get_roadmap_steps(EXAMPLE_WORKING_ROADMAP_ID)
        if steps_working_roadmap:
            # Finde die tatsächliche ID des ersten Schritts, falls vorhanden
            actual_first_step_id_working = steps_working_roadmap[0]['id'] if steps_working_roadmap else EXAMPLE_WORKING_STEP_ID
            print(f"Quizze für Roadmap {EXAMPLE_WORKING_ROADMAP_ID}, Step ID {actual_first_step_id_working} (spezifisch):")
            print(get_roadmap_quizes_specific(step_id=actual_first_step_id_working, roadmap_id=EXAMPLE_WORKING_ROADMAP_ID))
        else:
            print(f"Keine Schritte für Roadmap {EXAMPLE_WORKING_ROADMAP_ID} gefunden.")
    else:
        print(f"Roadmap {EXAMPLE_WORKING_ROADMAP_ID} nicht gefunden.")
    print("-" * 30)

    # --- Test für problematisches Beispiel ---
    print(f"[bold red]Test für Roadmap {EXAMPLE_PROBLEM_ROADMAP_ID} (problematisches Beispiel):[/bold red]")
    roadmap_problem = get_roadmap(EXAMPLE_PROBLEM_ROADMAP_ID)
    if roadmap_problem:
        print(f"Roadmap {EXAMPLE_PROBLEM_ROADMAP_ID}: {roadmap_problem}")
        steps_problem_roadmap = get_roadmap_steps(EXAMPLE_PROBLEM_ROADMAP_ID)
        problem_step_details = None # Initialisieren
        if steps_problem_roadmap:
            for step in steps_problem_roadmap:
                if step['id'] == EXAMPLE_PROBLEM_STEP_ID: # Vergleiche mit roadmap_steps.id
                    problem_step_details = step
                    break
            if problem_step_details:
                 print(f"Details für Step ID {EXAMPLE_PROBLEM_STEP_ID} (Roadmap {EXAMPLE_PROBLEM_ROADMAP_ID}): {problem_step_details}")
            else:
                print(f"Step mit ID {EXAMPLE_PROBLEM_STEP_ID} nicht in Roadmap {EXAMPLE_PROBLEM_ROADMAP_ID} gefunden.")
        else:
            print(f"Keine Schritte für Roadmap {EXAMPLE_PROBLEM_ROADMAP_ID} gefunden.")

        print(f"Quizze für Roadmap {EXAMPLE_PROBLEM_ROADMAP_ID}, Step ID {EXAMPLE_PROBLEM_STEP_ID} (spezifisch):")
        quizzes_specific = get_roadmap_quizes_specific(step_id=EXAMPLE_PROBLEM_STEP_ID, roadmap_id=EXAMPLE_PROBLEM_ROADMAP_ID)
        print(quizzes_specific)
        if not quizzes_specific:
            print(f"[bold yellow]WARNUNG: get_roadmap_quizes_specific hat keine Quizze für Step ID {EXAMPLE_PROBLEM_STEP_ID} (roadmap_steps.id), Roadmap ID {EXAMPLE_PROBLEM_ROADMAP_ID} zurückgegeben.[/bold yellow]")

        print(f"Alle Quizze für Roadmap {EXAMPLE_PROBLEM_ROADMAP_ID} (via get_roadmap_quizes_roadmapid):")
        all_quizzes_for_roadmap = get_roadmap_quizes_roadmapid(EXAMPLE_PROBLEM_ROADMAP_ID)
        print(all_quizzes_for_roadmap)
        # Überprüfen, ob ein Quiz mit der gesuchten step_id in der Liste ist
        found_in_all = any(q['step_id'] == EXAMPLE_PROBLEM_STEP_ID for q in all_quizzes_for_roadmap)
        if not found_in_all and quizzes_specific: # Wenn spezifisch was findet, aber "alle" nicht, ist das seltsam
             print(f"[bold yellow]WARNUNG: Quiz für Step ID {EXAMPLE_PROBLEM_STEP_ID} wurde spezifisch gefunden, aber nicht in der Gesamtliste der Quizze für Roadmap {EXAMPLE_PROBLEM_ROADMAP_ID} über step_id-Attribut.[/bold yellow]")
        elif not found_in_all and not quizzes_specific:
             print(f"[bold yellow]INFO: Weder spezifisch noch in der Gesamtliste wurde ein Quiz für Step ID {EXAMPLE_PROBLEM_STEP_ID} (roadmap_steps.id) in Roadmap {EXAMPLE_PROBLEM_ROADMAP_ID} gefunden.[/bold yellow]")
    else:
        print(f"Roadmap {EXAMPLE_PROBLEM_ROADMAP_ID} nicht gefunden.")
    print("-" * 50)
    print("[bold blue]Diagnose-Skript-Tests abgeschlossen.[/bold blue]")