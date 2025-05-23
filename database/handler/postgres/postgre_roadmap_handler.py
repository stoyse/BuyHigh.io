import os
import psycopg2
import psycopg2.extras
from datetime import datetime
import logging
from rich import print

logger = logging.getLogger(__name__)

# PostgreSQL connection details from .env
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = os.getenv('POSTGRES_PORT', '5432')
PG_DB = os.getenv('POSTGRES_DB', 'buyhigh')
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')

def get_db_connection():
    print('[bold blue]Connection to DB from Roadmap Handler[/bold blue]') # Corrected from Education Handler
    """Establishes a connection to the PostgreSQL database."""
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
        logger.error(f"Error opening PostgreSQL connection: {e}", exc_info=True)
        raise

def get_roadmap(id):
    """Loads the roadmap with the specified ID from the database."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM roadmap WHERE id = %s", (id,))
            roadmap = cursor.fetchone()
            if roadmap:
                return dict(roadmap)
            else:
                logger.warning(f"Roadmap with ID {id} not found.")
                return None
    except psycopg2.Error as e:
        logger.error(f"Error fetching roadmap: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_roadmap_steps(roadmap_id):
    """Loads the steps of the roadmap with the specified ID from the database."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM roadmap_steps WHERE roadmap_id = %s", (roadmap_id,))
            steps = cursor.fetchall()
            return [dict(step) for step in steps]
    except psycopg2.Error as e:
        logger.error(f"Error fetching roadmap steps: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_roadmap_quizes_roadmapid(roadmap_id):
    """Loads the quizzes for a specific roadmap ID."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM roadmap_quizzes WHERE roadmap_id = %s", (roadmap_id,))
            quizzes = cursor.fetchall()
            return [dict(quiz) for quiz in quizzes]
    except psycopg2.Error as e:
        logger.error(f"Error fetching roadmap quizzes: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_roadmap_quizes_stepid(roadmap_step, roadmap_id=None):
    """
    Loads the quizzes for a specific roadmap step.
    Optionally, a roadmap_id can be specified to further restrict the results.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            if roadmap_id is not None:
                # More precise query with roadmap_id and step_id
                cursor.execute("SELECT * FROM roadmap_quizzes WHERE step_id = %s AND roadmap_id = %s", 
                              (roadmap_step, roadmap_id))
            else:
                # Original query only with step_id
                cursor.execute("SELECT * FROM roadmap_quizzes WHERE step_id = %s", (roadmap_step,))
            
            quizzes = cursor.fetchall()
            logger.info(f"Found quizzes for step_id={roadmap_step}, roadmap_id={roadmap_id}: {len(quizzes)}")
            return [dict(quiz) for quiz in quizzes]
    except psycopg2.Error as e:
        logger.error(f"Error fetching roadmap quizzes: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_roadmap_quizes_specific(step_id, roadmap_id):
    """
    Loads the quizzes for a specific combination of roadmap ID and step ID.
    This is the most precise query and should be preferred.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM roadmap_quizzes 
                WHERE step_id = %s AND roadmap_id = %s
            """, (step_id, roadmap_id))
            
            quizzes = cursor.fetchall()
            logger.info(f"Found quizzes for step_id={step_id}, roadmap_id={roadmap_id}: {len(quizzes)}")
            
            if len(quizzes) == 0:
                # Diagnostic: Check if there are any quizzes for this step_id
                cursor.execute("SELECT COUNT(*) FROM roadmap_quizzes WHERE step_id = %s", (step_id,))
                count_by_step = cursor.fetchone()[0]
                
                # Check if there are quizzes for this roadmap_id
                cursor.execute("SELECT COUNT(*) FROM roadmap_quizzes WHERE roadmap_id = %s", (roadmap_id,))
                count_by_roadmap = cursor.fetchone()[0]
                
                logger.warning(f"No quizzes found for step_id={step_id}, roadmap_id={roadmap_id}. "
                              f"Individually found: {count_by_step} for step_id, {count_by_roadmap} for roadmap_id")
                
            return [dict(quiz) for quiz in quizzes]
    except psycopg2.Error as e:
        logger.error(f"Error fetching specific roadmap quizzes: {e}", exc_info=True)
        return [] # Return empty list in case of error
    finally:
        conn.close()

def check_and_fix_quiz_mappings():
    """Diagnostic function to check and fix inconsistent quiz mappings."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # Check for quiz entries where step_id does not match roadmap_id
            cursor.execute("""
                SELECT q.id, q.step_id, q.roadmap_id, s.roadmap_id AS expected_roadmap_id
                FROM roadmap_quizzes q
                LEFT JOIN roadmap_steps s ON q.step_id = s.id
                WHERE q.roadmap_id != s.roadmap_id OR s.id IS NULL
            """)
            
            inconsistent_quizzes = cursor.fetchall()
            
            if inconsistent_quizzes:
                logger.warning(f"Found {len(inconsistent_quizzes)} inconsistent quiz mappings:")
                for quiz in inconsistent_quizzes:
                    logger.warning(f"Quiz ID: {quiz['id']}, step_id: {quiz['step_id']}, "
                                 f"current roadmap_id: {quiz['roadmap_id']}, expected: {quiz['expected_roadmap_id']}")
                    
                    # Optional: Automatic correction if desired
                    if quiz['expected_roadmap_id'] is not None:
                        cursor.execute("""
                            UPDATE roadmap_quizzes
                            SET roadmap_id = %s
                            WHERE id = %s
                        """, (quiz['expected_roadmap_id'], quiz['id']))
                        
                conn.commit()
                logger.info("Inconsistent quiz mappings have been corrected.")
            else:
                logger.info("No inconsistent quiz mappings found.")
                
            return len(inconsistent_quizzes)
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Error checking/fixing quiz mappings: {e}", exc_info=True)
        return -1
    finally:
        conn.close()

def get_user_progress_for_quizzes(user_id, quiz_ids):
    """
    Loads the progress of a user for a given list of quiz IDs.
    Returns a dictionary mapping quiz_id to {'attempted': bool, 'is_correct': bool}.
    """
    if not quiz_ids:
        return {}
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # Create a placeholder string for the IN clause: (%s, %s, ...)
            placeholders = ', '.join(['%s'] * len(quiz_ids))
            sql_query = f"""
            SELECT 
                quiz_id,
                is_correct,
                attempted_at IS NOT NULL as attempted
            FROM user_roadmap_quiz_progress
            WHERE user_id = %s AND quiz_id IN ({placeholders});
            """
            # The parameter list must contain user_id first, then the quiz_ids
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
        logger.error(f"Error fetching user progress for quizzes: {e}", exc_info=True)
        return {} # Return empty dictionary in case of error
    finally:
        conn.close()

def get_quiz_by_id(quiz_id):
    """Loads a single quiz by its ID."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM roadmap_quizzes WHERE id = %s", (quiz_id,))
            quiz = cursor.fetchone()
            if quiz:
                return dict(quiz)
            return None
    except psycopg2.Error as e:
        logger.error(f"Error fetching quiz with ID {quiz_id}: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def record_user_quiz_attempt(user_id, quiz_id, is_correct):
    """Records or updates a user's quiz attempt."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Attempt to update an existing entry or insert a new one
            sql_query = """
            INSERT INTO user_roadmap_quiz_progress (user_id, quiz_id, is_correct, attempted_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, quiz_id) DO UPDATE SET
                is_correct = EXCLUDED.is_correct,
                attempted_at = CURRENT_TIMESTAMP;
            """
            cursor.execute(sql_query, (user_id, quiz_id, is_correct))
            conn.commit()
            logger.info(f"Quiz attempt for user {user_id}, quiz {quiz_id} recorded. Correct: {is_correct}")
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Error recording quiz attempt for user {user_id}, quiz {quiz_id}: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_xp_for_action(action_name):
    """Fetches the XP amount for a specific action."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT xp_amount FROM xp_gains WHERE action = %s", (action_name,))
            result = cursor.fetchone()
            if result:
                return result['xp_amount']
            logger.warning(f"No XP amount found for action '{action_name}' in xp_gains.")
            return 0  # Default value if action is not found
    except psycopg2.Error as e:
        logger.error(f"Error fetching XP for action {action_name}: {e}", exc_info=True)
        return 0 # Return 0 in case of error
    finally:
        conn.close()

def add_xp_to_user(user_id, xp_to_add):
    """Adds XP to a user and updates their level if necessary."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # Fetch current XP and level of the user
            cursor.execute("SELECT xp, level FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            if not user_data:
                logger.error(f"User with ID {user_id} not found for XP update.")
                return

            current_xp = user_data['xp']
            current_level = user_data['level']
            new_xp = current_xp + xp_to_add

            # Fetch all XP levels to determine the new level
            cursor.execute("SELECT level, xp_required FROM xp_levels ORDER BY level DESC")
            levels = cursor.fetchall()
            
            new_level = current_level
            for level_info in levels:
                if new_xp >= level_info['xp_required']:
                    new_level = level_info['level']
                    break 
            
            # Update user XP and level
            cursor.execute("UPDATE users SET xp = %s, level = %s WHERE id = %s", (new_xp, new_level, user_id))
            conn.commit()
            logger.info(f"User {user_id}: {xp_to_add} XP added. New XP: {new_xp}, New Level: {new_level}")
            
            xp_info = {"added_xp": xp_to_add, "total_xp": new_xp, "old_level": current_level, "new_level": new_level}
            if new_level > current_level:
                xp_info["level_up"] = True
            return xp_info

    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Error adding XP to user {user_id}: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def update_user_roadmap_step_progress(user_id, roadmap_id, step_id, is_completed, progress_percentage=None):
    """
    Updates the progress of a user for a specific roadmap step.
    Sets completed_at if is_completed is True.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            completed_at_val = datetime.now() if is_completed else None
            
            # If no specific progress percentage is provided and the step is completed, set to 100%
            if progress_percentage is None and is_completed:
                progress_percentage = 100.0
            elif progress_percentage is None and not is_completed: # If not completed and no value, set to 0%
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
            logger.info(f"Progress for user {user_id}, roadmap {roadmap_id}, step {step_id} updated. Completed: {is_completed}, Progress: {progress_percentage}%")
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Error updating roadmap step progress: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_user_roadmap_progress_all_steps(user_id, roadmap_id):
    """
    Fetches the progress of all steps of a roadmap for a specific user.
    Returns a dictionary mapping step_id to {'is_completed': bool, 'progress_percentage': float}.
    """
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
        logger.error(f"Error fetching full roadmap progress for user {user_id}, roadmap {roadmap_id}: {e}", exc_info=True)
        return {} # Return empty dictionary in case of error
    finally:
        conn.close()

def get_roadmap_collection():
    """Loads all roadmaps from the database."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM roadmap")
            roadmaps = cursor.fetchall()
            return [dict(roadmap) for roadmap in roadmaps]
    except psycopg2.Error as e:
        logger.error(f"Error fetching roadmap collection: {e}", exc_info=True)
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # Perform a check and correction of quiz mappings if necessary
    print("[bold yellow]Checking quiz mappings:[/bold yellow]")
    check_and_fix_quiz_mappings()
    print("-" * 50)

    # Example IDs for tests
    EXAMPLE_WORKING_ROADMAP_ID = 1
    EXAMPLE_WORKING_STEP_ID = 1 # This is roadmap_steps.id

    # Based on previous logs as an example for a problematic test:
    EXAMPLE_PROBLEM_ROADMAP_ID = 3
    EXAMPLE_PROBLEM_STEP_ID = 4 # This is roadmap_steps.id

    # --- Test for working example ---
    print(f"[bold green]Test for roadmap {EXAMPLE_WORKING_ROADMAP_ID} (working example):[/bold green]")
    roadmap_working = get_roadmap(EXAMPLE_WORKING_ROADMAP_ID)
    if roadmap_working:
        print(f"Roadmap {EXAMPLE_WORKING_ROADMAP_ID}: {roadmap_working}")
        steps_working_roadmap = get_roadmap_steps(EXAMPLE_WORKING_ROADMAP_ID)
        if steps_working_roadmap:
            # Find the actual ID of the first step, if available
            actual_first_step_id_working = steps_working_roadmap[0]['id'] if steps_working_roadmap else EXAMPLE_WORKING_STEP_ID
            print(f"Quizzes for roadmap {EXAMPLE_WORKING_ROADMAP_ID}, step ID {actual_first_step_id_working} (specific):")
            print(get_roadmap_quizes_specific(step_id=actual_first_step_id_working, roadmap_id=EXAMPLE_WORKING_ROADMAP_ID))
        else:
            print(f"No steps found for roadmap {EXAMPLE_WORKING_ROADMAP_ID}.")
    else:
        print(f"Roadmap {EXAMPLE_WORKING_ROADMAP_ID} not found.")
    print("-" * 30)

    # --- Test for problematic example ---
    print(f"[bold red]Test for roadmap {EXAMPLE_PROBLEM_ROADMAP_ID} (problematic example):[/bold red]")
    roadmap_problem = get_roadmap(EXAMPLE_PROBLEM_ROADMAP_ID)
    if roadmap_problem:
        print(f"Roadmap {EXAMPLE_PROBLEM_ROADMAP_ID}: {roadmap_problem}")
        steps_problem_roadmap = get_roadmap_steps(EXAMPLE_PROBLEM_ROADMAP_ID)
        problem_step_details = None # Initialize
        if steps_problem_roadmap:
            for step in steps_problem_roadmap:
                if step['id'] == EXAMPLE_PROBLEM_STEP_ID: # Compare with roadmap_steps.id
                    problem_step_details = step
                    break
            if problem_step_details:
                 print(f"Details for step ID {EXAMPLE_PROBLEM_STEP_ID} (roadmap {EXAMPLE_PROBLEM_ROADMAP_ID}): {problem_step_details}")
            else:
                print(f"Step with ID {EXAMPLE_PROBLEM_STEP_ID} not found in roadmap {EXAMPLE_PROBLEM_ROADMAP_ID}.")
        else:
            print(f"No steps found for roadmap {EXAMPLE_PROBLEM_ROADMAP_ID}.")

        print(f"Quizzes for roadmap {EXAMPLE_PROBLEM_ROADMAP_ID}, step ID {EXAMPLE_PROBLEM_STEP_ID} (specific):")
        quizzes_specific = get_roadmap_quizes_specific(step_id=EXAMPLE_PROBLEM_STEP_ID, roadmap_id=EXAMPLE_PROBLEM_ROADMAP_ID)
        print(quizzes_specific)
        if not quizzes_specific:
            print(f"[bold yellow]WARNING: get_roadmap_quizes_specific returned no quizzes for step ID {EXAMPLE_PROBLEM_STEP_ID} (roadmap_steps.id), roadmap ID {EXAMPLE_PROBLEM_ROADMAP_ID}.[/bold yellow]")

        print(f"All quizzes for roadmap {EXAMPLE_PROBLEM_ROADMAP_ID} (via get_roadmap_quizes_roadmapid):")
        all_quizzes_for_roadmap = get_roadmap_quizes_roadmapid(EXAMPLE_PROBLEM_ROADMAP_ID)
        print(all_quizzes_for_roadmap)
        # Check if a quiz with the searched step_id is in the list
        found_in_all = any(q['step_id'] == EXAMPLE_PROBLEM_STEP_ID for q in all_quizzes_for_roadmap)
        if not found_in_all and quizzes_specific: # If specific finds something but "all" does not, that's odd
             print(f"[bold yellow]WARNING: Quiz for step ID {EXAMPLE_PROBLEM_STEP_ID} was found specifically, but not in the full list of quizzes for roadmap {EXAMPLE_PROBLEM_ROADMAP_ID} via step_id attribute.[/bold yellow]")
        elif not found_in_all and not quizzes_specific:
             print(f"[bold yellow]INFO: Neither specifically nor in the full list was a quiz found for step ID {EXAMPLE_PROBLEM_STEP_ID} (roadmap_steps.id) in roadmap {EXAMPLE_PROBLEM_ROADMAP_ID}.[/bold yellow]")
    else:
        print(f"Roadmap {EXAMPLE_PROBLEM_ROADMAP_ID} not found.")
    print("-" * 50)
    print("[bold blue]Diagnostic script tests completed.[/bold blue]")