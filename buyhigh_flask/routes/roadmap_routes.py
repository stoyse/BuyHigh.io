from flask import Blueprint, render_template, g, request, flash, redirect, url_for, jsonify, current_app, render_template_string
from utils.utils import login_required
import database.handler.postgres.postgres_db_handler as db_handler
import logging
from rich import print
import database.handler.postgres.postgre_roadmap_handler as roadmap_handler
import os

# Configure basic logging
# logging.basicConfig(level=logging.DEBUG) # Wird jetzt in app.py global konfiguriert
logger = logging.getLogger(__name__)

roadmap_bp = Blueprint('roadmap', __name__)

@roadmap_bp.route('/')
@roadmap_bp.route('/<int:roadmap_id>')
@login_required
def roadmap(roadmap_id=1):  # Default to roadmap ID 1 if none provided
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    user_id = g.user.get('id')

    roadmap_data = roadmap_handler.get_roadmap(roadmap_id)
    if not roadmap_data:
        flash("Roadmap nicht gefunden.", "error")
        return redirect(url_for('roadmap.roadmap_collection'))
        
    roadmap_steps_data = roadmap_handler.get_roadmap_steps(roadmap_id)
    
    user_step_progress_db = {}
    if user_id:
        user_step_progress_db = roadmap_handler.get_user_roadmap_progress_all_steps(user_id, roadmap_id)

    total_steps = len(roadmap_steps_data)
    completed_steps_count = 0 # Counts steps where all quizzes are attempted

    if total_steps > 0:
        for step in roadmap_steps_data:
            progress_info = user_step_progress_db.get(step['id'])
            step['is_attempted_all_quizzes'] = False # Renaming for clarity, true if all quizzes in step are attempted
            step['completion_status'] = 'incomplete' # Default: 'incomplete', 'perfect', 'imperfect'

            if progress_info and progress_info.get('is_completed'): # 'is_completed' from DB means all quizzes attempted
                step['is_attempted_all_quizzes'] = True
                completed_steps_count += 1

                # Use get_roadmap_quizes_specific for accuracy
                quizzes_in_step = roadmap_handler.get_roadmap_quizes_specific(step_id=step['id'], roadmap_id=roadmap_id)
                if not quizzes_in_step:
                    step['completion_status'] = 'perfect' # Step completed, no quizzes to be imperfect on
                else:
                    all_correct = True
                    quiz_ids_for_this_step = [q['id'] for q in quizzes_in_step]
                    # Fetch attempts for these specific quizzes
                    user_attempts_for_quizzes = roadmap_handler.get_user_progress_for_quizzes(user_id, quiz_ids_for_this_step)

                    if len(user_attempts_for_quizzes) < len(quizzes_in_step):
                        # This implies an inconsistency if step.is_attempted_all_quizzes is True.
                        # e.g. quiz added after completion, or error fetching progress.
                        all_correct = False
                        logger.warning(f"Data inconsistency for step {step['id']} user {user_id}: marked completed but quiz progress count mismatch.")
                    
                    for q_id in quiz_ids_for_this_step:
                        attempt = user_attempts_for_quizzes.get(q_id)
                        # If step is marked as all quizzes attempted, each quiz should have an attempt.
                        if not attempt or not attempt.get('attempted'):
                            all_correct = False # Should not happen if is_attempted_all_quizzes is true and data is consistent
                            logger.warning(f"Data inconsistency for step {step['id']} user {user_id}: quiz {q_id} not marked attempted despite step completion.")
                            break 
                        if not attempt.get('is_correct'):
                            all_correct = False
                            break
                    
                    if all_correct:
                        step['completion_status'] = 'perfect'
                    else:
                        step['completion_status'] = 'imperfect'
            # else: step remains 'incomplete' and step['is_attempted_all_quizzes'] is False
        
        overall_roadmap_progress_percentage = (completed_steps_count / total_steps) * 100 if total_steps > 0 else 0
    else:
        overall_roadmap_progress_percentage = 0

    return render_template('roadmap/roadmap.html',
                           user=g.user, 
                           darkmode=dark_mode_active,
                           roadmap=roadmap_data,
                           roadmap_steps=roadmap_steps_data, # Now contains 'is_attempted_all_quizzes' and 'completion_status'
                           overall_roadmap_progress_percentage=overall_roadmap_progress_percentage
                           )
                           

@roadmap_bp.route('/step/<int:roadmap_id>/<step_id>')
@login_required
def roadmap_step(roadmap_id, step_id): # step_id is a string from URL
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    
    all_steps_for_roadmap = roadmap_handler.get_roadmap_steps(roadmap_id)
    current_step = next((s for s in all_steps_for_roadmap if str(s['id']) == str(step_id)), None)

    if not current_step:
        flash("Schritt nicht gefunden.", "error")
        return redirect(url_for('roadmap.roadmap', roadmap_id=roadmap_id))

    raw_page_layout = current_step.get('page_layout', [])
    print(f'[red]Current Step (ID: {current_step["id"]}, Roadmap ID: {roadmap_id}): {current_step}[/red]')
    print(f'[blue]Initial Page Layout from DB: {raw_page_layout}[/blue]')

    page_layout = []
    for layout_item_identifier in raw_page_layout:
        page_layout.append({
            "layout_number": layout_item_identifier,
            "card_html": None,
        })
    
    print(f'[green]Transformed Page Layout for processing: {page_layout}[/green]')

    quizzes_for_step_raw = roadmap_handler.get_roadmap_quizes_specific(step_id=current_step['id'], roadmap_id=roadmap_id)
    
    all_quizzes_for_step = []
    user_id_for_quiz = g.user.get('id') if g.user else None

    if quizzes_for_step_raw:
        if user_id_for_quiz:
            quiz_ids = [q['id'] for q in quizzes_for_step_raw]
            user_progress = roadmap_handler.get_user_progress_for_quizzes(user_id_for_quiz, quiz_ids)
            
            for quiz_raw in quizzes_for_step_raw:
                progress = user_progress.get(quiz_raw['id'])
                if progress:
                    quiz_raw['attempted'] = progress.get('attempted', False)
                    quiz_raw['is_correct'] = progress.get('is_correct', None)
                else:
                    quiz_raw['attempted'] = False
                    quiz_raw['is_correct'] = None
                all_quizzes_for_step.append(quiz_raw)
        else:
            for quiz_raw in quizzes_for_step_raw:
                quiz_raw['attempted'] = False
                quiz_raw['is_correct'] = None
                all_quizzes_for_step.append(quiz_raw)
            print(f'[yellow]Warnung: Keine Benutzer-ID für Quiz-Fortschritt verfügbar. Quizze werden ohne Fortschritt geladen.[/yellow]')
    
    if all_quizzes_for_step:
        print(f'[magenta]Quizzes found for step {current_step["id"]} (Roadmap {roadmap_id}): {len(all_quizzes_for_step)} quizzes. Will be available to card templates.[/magenta]')
    else:
        print(f'[yellow]No quizzes found for step {current_step["id"]} (Roadmap {roadmap_id}) using get_roadmap_quizes_specific.[/yellow]')

    for item in page_layout:
        layout_number_str = str(item.get('layout_number'))
        print(f'[cyan]Processing layout identifier (expected to be a card number): {layout_number_str}[/cyan]')

        if layout_number_str == '1':
            explain_text = current_step.get('explain')
            if explain_text:
                item['card_html'] = f"<div class='explanation-card p-4 rounded-lg bg-white/5 dark:bg-black/10 border border-gray-200/10 dark:border-gray-700/20 shadow-sm'><h3 class='text-lg font-semibold mb-2 text-gray-800 dark:text-gray-100'>Concept Explanation</h3><p>{explain_text}</p></div>"
                print(f'[green]Rendered HTML for card 1 from current_step.explain[/green]')
            else:
                item['card_html'] = "<div class='explanation-card p-4 rounded-lg bg-white/5 dark:bg-black/10 border border-gray-200/10 dark:border-gray-700/20 shadow-sm'><p><em>No explanation available for this step.</em></p></div>"
                print(f'[yellow]No explanation text found for card 1 in current_step.[/yellow]')
        else:
            card_filename = f"{roadmap_id}_{step_id}_{layout_number_str}.html"
            card_path = os.path.join(current_app.root_path, "templates", "roadmap", "step_cards", card_filename)
            print(f'[blue]Card Path: {card_path}[/blue]')
            try:
                with open(card_path, "r") as card_file:
                    raw_html = card_file.read()
                    card_context = {
                        "user": g.user,
                        "current_step": current_step,
                        "layout_number": layout_number_str,
                        "all_quizzes_for_step": all_quizzes_for_step
                    }
                    item['card_html'] = render_template_string(raw_html, **card_context)
                    print(f'[green]Rendered HTML for {card_filename} with context (including quizzes if any)[/green]')
            except FileNotFoundError:
                item['card_html'] = f"<!-- Card file {card_filename} not found -->"
                print(f'[red]Card file {card_filename} not found[/red]')
            except Exception as e:
                item['card_html'] = f"<!-- Error rendering card {card_filename}: {e} -->"
                print(f'[red]Error rendering card {card_filename}: {e}[/red]')
                logger.error(f"Error rendering card {card_filename}: {e}", exc_info=True)

    # HINWEIS: Die folgende Dummy-Funktion dient nur dazu, den UndefinedError zu beheben.
    # Sie bietet KEINE echte CSRF-Sicherheit. Eine korrekte CSRF-Einrichtung
    # erfordert die Initialisierung von CSRFProtect in Ihrer Hauptanwendung (app.py).
    def dummy_csrf_token_for_template():
        return "dummy_token_to_prevent_undefined_error"

    return render_template('roadmap/step.html',
                           user=g.user,
                           darkmode=dark_mode_active,
                           roadmap=roadmap_handler.get_roadmap(roadmap_id),
                           roadmap_steps=all_steps_for_roadmap,
                           page_layout=page_layout,
                           current_step=current_step,
                           quizzes=all_quizzes_for_step,
                           csrf_token=dummy_csrf_token_for_template # csrf_token() im Template wird dies aufrufen
                           )

@roadmap_bp.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    logger.debug(f"submit_quiz called. Form data: {request.form.to_dict()}")

    if request.method == 'POST':
        quiz_id_str = request.form.get('quiz_id')
        step_id_str = request.form.get('step_id')
        roadmap_id_str = request.form.get('roadmap_id')
        submitted_answer_value = request.form.get('quiz_answer') # Dies ist 'possible_answer_1', etc.
        user_id = g.user.get('id')

        redirect_url = url_for('roadmap.roadmap') # Fallback, falls IDs fehlen
        if roadmap_id_str and step_id_str:
            try:
                redirect_url = url_for('roadmap.roadmap_step', roadmap_id=int(roadmap_id_str), step_id=int(step_id_str))
            except ValueError:
                logger.warning(f"Konnte roadmap_id '{roadmap_id_str}' oder step_id '{step_id_str}' nicht für Redirect-URL konvertieren.")
                redirect_url = url_for('roadmap.roadmap_collection')


        if not all([quiz_id_str, step_id_str, roadmap_id_str, submitted_answer_value, user_id]):
            message = "Error: Incomplete quiz data submitted."
            logger.error(f"Incomplete data in submit_quiz: quiz_id={quiz_id_str}, step_id={step_id_str}, roadmap_id={roadmap_id_str}, answer_value={submitted_answer_value}, user_id={user_id}")
            flash(message, "error")
            return redirect(request.referrer or redirect_url)

        try:
            quiz_id = int(quiz_id_str)
            actual_step_id = int(step_id_str) # Dies ist die ID des roadmap_steps
            current_roadmap_id = int(roadmap_id_str) # Dies ist die ID der roadmap
        except ValueError:
            message = "Error: Invalid quiz identifiers."
            logger.error(f"Invalid identifiers in submit_quiz: quiz_id_str={quiz_id_str}, step_id_str={step_id_str}, roadmap_id_str={roadmap_id_str}")
            flash(message, "error")
            return redirect(redirect_url) # Nutze die zuvor bestimmte redirect_url

        target_step_redirect_url = url_for('roadmap.roadmap_step', roadmap_id=current_roadmap_id, step_id=actual_step_id)

        quiz = roadmap_handler.get_quiz_by_id(quiz_id)

        if not quiz:
            message = f"Quiz with ID {quiz_id} not found."
            logger.error(message)
            flash(message, "error")
            return redirect(target_step_redirect_url)
        
        if quiz.get('step_id') != actual_step_id or quiz.get('roadmap_id') != current_roadmap_id:
            message = f"Data mismatch: Quiz {quiz_id} (step: {quiz.get('step_id')}, roadmap: {quiz.get('roadmap_id')}) does not align with submitted step {actual_step_id} or roadmap {current_roadmap_id}."
            logger.error(message)
            flash("An error occurred with the quiz data. Please try again.", "error")
            return redirect(target_step_redirect_url)

        submitted_answer_text = ""
        if submitted_answer_value == 'possible_answer_1':
            submitted_answer_text = quiz.get('possible_answer_1')
        elif submitted_answer_value == 'possible_answer_2':
            submitted_answer_text = quiz.get('possible_answer_2')
        elif submitted_answer_value == 'possible_answer_3':
            submitted_answer_text = quiz.get('possible_answer_3')

        is_correct = (str(quiz.get('correct_answer','')).strip().lower() == str(submitted_answer_text).strip().lower())
        logger.info(f"Quiz {quiz_id} attempt by user {user_id}. Submitted key: '{submitted_answer_value}', Submitted text: '{submitted_answer_text}', Correct text: '{quiz.get('correct_answer')}'. Result: {is_correct}")

        try:
            logger.info(f"Attempting to record quiz attempt for user {user_id}, quiz {quiz_id}, correct: {is_correct}")
            roadmap_handler.record_user_quiz_attempt(user_id, quiz_id, is_correct)
            logger.info(f"Successfully recorded quiz attempt for user {user_id}, quiz {quiz_id}.")
            
            all_quizzes_for_this_step = roadmap_handler.get_roadmap_quizes_specific(step_id=actual_step_id, roadmap_id=current_roadmap_id)
            logger.debug(f"Quizzes for step {actual_step_id} (Roadmap {current_roadmap_id}) after attempt: {len(all_quizzes_for_this_step) if all_quizzes_for_this_step else 'None or 0'}")
            
            if all_quizzes_for_this_step:
                quiz_ids_in_step = [q['id'] for q in all_quizzes_for_this_step]
                user_attempts_for_step_quizzes = roadmap_handler.get_user_progress_for_quizzes(user_id, quiz_ids_in_step)
                
                all_quizzes_in_step_attempted = True
                if len(user_attempts_for_step_quizzes) < len(all_quizzes_for_this_step):
                    all_quizzes_in_step_attempted = False
                else:
                    for q_id_in_step in quiz_ids_in_step:
                        attempt_info = user_attempts_for_step_quizzes.get(q_id_in_step)
                        if not attempt_info or not attempt_info.get('attempted'):
                            all_quizzes_in_step_attempted = False
                            break
                
                if all_quizzes_in_step_attempted:
                    logger.info(f"All quizzes for step {actual_step_id} (Roadmap {current_roadmap_id}) attempted by user {user_id}. Attempting to update step progress.")
                    roadmap_handler.update_user_roadmap_step_progress(user_id, current_roadmap_id, actual_step_id, is_completed=True, progress_percentage=100.0)
                    logger.info(f"Successfully updated step progress for user {user_id}, roadmap {current_roadmap_id}, step {actual_step_id}.")
            
            response_message_text = "" # Renamed to avoid conflict with jsonify's message
            if is_correct:
                xp_action_name = 'roadmap_quiz_correct' 
                xp_to_award = roadmap_handler.get_xp_for_action(xp_action_name)
                if xp_to_award == 0: 
                    xp_to_award = roadmap_handler.get_xp_for_action('daily_quiz') 
                    if xp_to_award == 0: 
                        xp_to_award = 25 
                
                if xp_to_award > 0:
                    xp_update_info = roadmap_handler.add_xp_to_user(user_id, xp_to_award)
                    response_message_text = f"Correct! You earned {xp_to_award} XP."
                    if xp_update_info and xp_update_info.get("level_up"):
                        response_message_text += f" Level Up! You are now Level {xp_update_info['new_level']}!"
                else:
                    response_message_text = "Correct!"
                flash(response_message_text, "success")
            else:
                response_message_text = f"Incorrect. The correct answer was: {quiz.get('correct_answer')}"
                flash(response_message_text, "warning")

        except Exception as e:
            logger.error(f"Exception during DB operations or subsequent logic in submit_quiz for quiz {quiz_id}: {e}", exc_info=True)
            flash("An internal error occurred while processing your answer.", "error")

        return redirect(target_step_redirect_url)
    
    flash("Invalid request method.", "error")
    return redirect(url_for('roadmap.roadmap'))

@roadmap_bp.route('/roadmap-collection')
@login_required
def roadmap_collection():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    user_id = g.user.get('id')
    
    all_roadmaps_raw = roadmap_handler.get_roadmap_collection()
    processed_roadmaps = []

    if user_id:
        for r_map in all_roadmaps_raw:
            roadmap_id = r_map['id']
            steps_for_this_roadmap = roadmap_handler.get_roadmap_steps(roadmap_id)
            total_steps = len(steps_for_this_roadmap)
            completed_steps_count = 0

            if total_steps > 0:
                user_step_progress_db = roadmap_handler.get_user_roadmap_progress_all_steps(user_id, roadmap_id)
                for step in steps_for_this_roadmap:
                    progress_info = user_step_progress_db.get(step['id'])
                    if progress_info and progress_info.get('is_completed'):
                        completed_steps_count += 1
                
                r_map['progress_percentage'] = (completed_steps_count / total_steps) * 100
                r_map['is_completed'] = (completed_steps_count == total_steps)
            else:
                r_map['progress_percentage'] = 0
                r_map['is_completed'] = False # Eine Roadmap ohne Schritte kann nicht abgeschlossen sein im Sinne von Schritten
            
            processed_roadmaps.append(r_map)
    else:
        for r_map in all_roadmaps_raw:
            r_map['progress_percentage'] = 0
            r_map['is_completed'] = False
            processed_roadmaps.append(r_map)

    return render_template('roadmap/roadmap_collection.html',
                           user = g.user,
                           darkmode = dark_mode_active,
                           roadmap_collection = processed_roadmaps)

@roadmap_bp.route('/create_roadmap', methods=['GET', 'POST'])
@login_required
def create_roadmap():
    user_id_for_analytics = g.user.get('id') if hasattr(g, 'user') and g.user else None
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        roadmap_title = request.form.get('roadmap_title')
        roadmap_description = request.form.get('roadmap_description')
        
        if not roadmap_title:
            if is_ajax:
                return jsonify({'success': False, 'message': 'Roadmap title is required'})
            flash('Roadmap title is required', 'danger')
            return redirect(url_for('roadmap.create_roadmap'))
        
        conn = None
        try:
            conn = roadmap_handler.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO roadmap (title, description) VALUES (%s, %s) RETURNING id",
                (roadmap_title, roadmap_description)
            )
            roadmap_id = cursor.fetchone()[0]
            
            step_titles = request.form.getlist('step_title[]')
            step_descriptions = request.form.getlist('step_description[]')
            step_numbers = request.form.getlist('step_number[]')
            step_explains = request.form.getlist('step_explain[]')
            
            layout_fields = {}
            for key in request.form:
                if key.startswith('step_layout_'):
                    index = int(key.replace('step_layout_', ''))
                    layout_fields[index] = request.form[key]
            
            step_ids = []
            for i in range(len(step_titles)):
                step_number = int(step_numbers[i]) if i < len(step_numbers) else i + 1
                step_title = step_titles[i]
                step_description = step_descriptions[i] if i < len(step_descriptions) else ""
                step_explain = step_explains[i] if i < len(step_explains) else None
                
                layout_json = layout_fields.get(i, '[]')
                try:
                    import json
                    layout_array = json.loads(layout_json)
                    if not layout_array and step_explain:
                        layout_array = [1]
                except:
                    layout_array = [1] if step_explain else []
                
                cursor.execute(
                    """
                    INSERT INTO roadmap_steps 
                    (roadmap_id, step_number, title, description, page_layout, explain) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (roadmap_id, step_number, step_title, step_description, layout_array, step_explain)
                )
                step_id = cursor.fetchone()[0]
                step_ids.append(step_id)
            
            for key in request.form:
                if key.startswith('quiz_step_') and '_question_' in key:
                    parts = key.split('_')
                    step_index = int(parts[2])
                    quiz_index = int(parts[4])
                    
                    question = request.form[key]
                    answer1 = request.form.get(f'quiz_step_{step_index}_answer1_{quiz_index}', '')
                    answer2 = request.form.get(f'quiz_step_{step_index}_answer2_{quiz_index}', '')
                    answer3 = request.form.get(f'quiz_step_{step_index}_answer3_{quiz_index}', '')
                    correct_answer = request.form.get(f'quiz_step_{step_index}_correct_{quiz_index}', '')
                    
                    if question and answer1 and answer2 and answer3 and correct_answer and step_index < len(step_ids):
                        step_id = step_ids[step_index]
                        
                        cursor.execute(
                            """
                            INSERT INTO roadmap_quizzes
                            (roadmap_id, step_id, question, possible_answer_1, possible_answer_2, possible_answer_3, correct_answer)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (roadmap_id, step_id, question, answer1, answer2, answer3, correct_answer)
                        )
            
            conn.commit()
            
            if is_ajax:
                return jsonify({
                    'success': True, 
                    'message': 'Roadmap created successfully',
                    'redirect_url': url_for('roadmap.roadmap', roadmap_id=roadmap_id) if step_ids else url_for('roadmap.roadmap_collection')
                })
            
            flash('Roadmap created successfully!', 'success')
            if step_ids:
                return redirect(url_for('roadmap.roadmap', roadmap_id=roadmap_id))
            return redirect(url_for('roadmap.roadmap_collection'))
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error creating roadmap: {e}", exc_info=True)
            
            if is_ajax:
                return jsonify({'success': False, 'message': f'Error: {str(e)}'})
            
            flash(f'Error creating roadmap: {str(e)}', 'danger')
            return redirect(url_for('roadmap.create_roadmap'))
            
        finally:
            if conn:
                conn.close()
    
    return render_template('roadmap/create_roadmap.html',
                          user = g.user,
                          darkmode = g.user.get('theme') == 'dark',
                          roadmap_collection = roadmap_handler.get_roadmap_collection())

@roadmap_bp.route('/moonwalking-bull')
@login_required
def moonwalking_bull_page():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    return render_template('roadmap/moonwalking_bull.html',
                           user=g.user,
                           darkmode=dark_mode_active)

@roadmap_bp.route('/toggle_meme_mode', methods=['POST'])
@login_required
def toggle_meme_mode():
    user_id = g.user.get('id')
    
    if not user_id:
        flash("Du musst angemeldet sein, um den Meme-Modus umzuschalten.", "error")
        return redirect(url_for('roadmap.roadmap'))
    
    conn = None
    try:
        conn = roadmap_handler.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_meme_mode FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        
        if result is None:
            flash("Benutzer nicht gefunden.", "error")
            return redirect(url_for('roadmap.roadmap'))
        
        current_meme_mode = result[0]
        new_meme_mode = not current_meme_mode
        
        cursor.execute("UPDATE users SET is_meme_mode = %s WHERE id = %s", (new_meme_mode, user_id))
        conn.commit()
        
        if 'user' in g and g.user:
            g.user['is_meme_mode'] = new_meme_mode
        
        status_text = "aktiviert" if new_meme_mode else "deaktiviert"
        flash(f"Meme-Modus wurde {status_text}.", "success")
        return redirect(request.referrer or url_for('roadmap.roadmap'))
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Fehler beim Umschalten des Meme-Modus: {e}", exc_info=True)
        flash(f"Fehler beim Umschalten des Meme-Modus: {str(e)}", "danger")
        return redirect(request.referrer or url_for('roadmap.roadmap'))
        
    finally:
        if conn:
            conn.close()
