from flask import Blueprint, render_template, g, request, flash, redirect, url_for, jsonify, current_app, render_template_string
from utils import login_required
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
@login_required
def roadmap():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    return render_template('roadmap/roadmap.html',
                           user=g.user, 
                           darkmode=dark_mode_active,
                           roadmap=roadmap_handler.get_roadmap(1),
                           roadmap_steps=roadmap_handler.get_roadmap_steps(1),
                           roadmap_quiz=roadmap_handler.get_roadmap_quizes_roadmapid(1))
                           

@roadmap_bp.route('/step/<int:roadmap_id>/<step_id>')
@login_required
def roadmap_step(roadmap_id, step_id):
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    data = roadmap_handler.get_roadmap_steps(roadmap_id)
    current_step = next((s for s in data if str(s['id']) == str(step_id)), None)

    if not current_step:
        flash("Schritt nicht gefunden.", "error")
        return redirect(url_for('roadmap.roadmap'))

    raw_page_layout = current_step.get('page_layout', [])
    print(f'[red]Current Step: {current_step}[/red]')
    print(f'[blue]Initial Page Layout from DB: {raw_page_layout}[/blue]')

    page_layout = []
    for layout_item_identifier in raw_page_layout:
        page_layout.append({
            "layout_number": layout_item_identifier, # Dies wird jetzt immer eine Zahl oder ein String sein, der zu einer .html-Datei führt
            "card_html": None,
        })
    
    print(f'[green]Transformed Page Layout for processing: {page_layout}[/green]')

    # Lade alle Quizze für den aktuellen Schritt einmal.
    # Diese werden jeder Karte im Kontext zur Verfügung gestellt.
    
    # 1. Lade alle Quizze für den Schritt (ohne Benutzerfortschritt)
    quizzes_for_step_raw = roadmap_handler.get_roadmap_quizes_stepid(step_id)
    
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
                    quiz_raw['is_correct'] = progress.get('is_correct', None) # Behält None bei, wenn nicht versucht oder kein is_correct Wert
                else:
                    quiz_raw['attempted'] = False
                    quiz_raw['is_correct'] = None
                all_quizzes_for_step.append(quiz_raw)
        else:
            # Kein Benutzer angemeldet, Quizze ohne Fortschrittsinformationen hinzufügen
            for quiz_raw in quizzes_for_step_raw:
                quiz_raw['attempted'] = False
                quiz_raw['is_correct'] = None
                all_quizzes_for_step.append(quiz_raw)
            print(f'[yellow]Warnung: Keine Benutzer-ID für Quiz-Fortschritt verfügbar. Quizze werden ohne Fortschritt geladen.[/yellow]')
    
    if all_quizzes_for_step:
        print(f'[magenta]Quizzes found for step {step_id}: {len(all_quizzes_for_step)} quizzes. Will be available to card templates.[/magenta]')
    else:
        print(f'[yellow]No quizzes found for step {step_id}.[/yellow]')


    for item in page_layout:
        layout_number_str = str(item.get('layout_number'))
        print(f'[cyan]Processing layout identifier (expected to be a card number): {layout_number_str}[/cyan]')

        # Jedes Element im page_layout wird als reguläre Karte behandelt,
        # die Karte selbst kann entscheiden, ob sie Quizdaten verwendet.
        card_filename = f"{roadmap_id}_{step_id}_{layout_number_str}.html"
        card_path = os.path.join(current_app.root_path, "templates", "roadmap", "step_cards", card_filename)
        print(f'[blue]Card Path: {card_path}[/blue]')
        try:
            with open(card_path, "r") as card_file:
                raw_html = card_file.read()
                # Kontext für das Rendern der einzelnen Karte vorbereiten
                card_context = {
                    "user": g.user,
                    "current_step": current_step,
                    "layout_number": layout_number_str,
                    "all_quizzes_for_step": all_quizzes_for_step # Stelle alle Quizze der Karte zur Verfügung
                    # Fügen Sie hier weitere Variablen hinzu, die Kartenvorlagen benötigen könnten
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

    return render_template('roadmap/step.html',
                           user=g.user,
                           darkmode=dark_mode_active,
                           roadmap=roadmap_handler.get_roadmap(roadmap_id),
                           roadmap_steps=data,
                           page_layout=page_layout,
                           current_step=current_step,
                           # roadmap_quiz_overall_for_step kann beibehalten werden, falls es global auf der step.html Seite genutzt wird
                           roadmap_quiz_overall_for_step=all_quizzes_for_step 
                           )

@roadmap_bp.route('/submit_quiz', methods=['POST'])
@login_required
def submit_roadmap_quiz():
    if request.method == 'POST':
        quiz_id_str = request.form.get('quiz_id')
        step_id_str = request.form.get('step_id')
        roadmap_id_str = request.form.get('roadmap_id')
        submitted_answer = request.form.get('quiz_answer')
        user_id = g.user.get('id')

        if not all([quiz_id_str, step_id_str, roadmap_id_str, submitted_answer, user_id]):
            flash("Fehler: Unvollständige Quizdaten übermittelt.", "error")
            return redirect(request.referrer or url_for('roadmap.roadmap'))

        try:
            quiz_id = int(quiz_id_str)
            step_id = int(step_id_str)
            roadmap_id = int(roadmap_id_str)
        except ValueError:
            flash("Fehler: Ungültige Quiz-Identifikatoren.", "error")
            return redirect(request.referrer or url_for('roadmap.roadmap'))

        quiz = roadmap_handler.get_quiz_by_id(quiz_id)

        if not quiz:
            flash(f"Quiz mit ID {quiz_id} nicht gefunden.", "error")
            return redirect(url_for('roadmap.roadmap_step', roadmap_id=roadmap_id, step_id=step_id))

        is_correct = (quiz['correct_answer'] == submitted_answer)

        try:
            roadmap_handler.record_user_quiz_attempt(user_id, quiz_id, is_correct)
            
            if is_correct:
                # XP für korrektes Roadmap-Quiz vergeben
                # Annahme: Die Aktion in xp_gains heißt 'roadmap_quiz_correct'
                xp_action_name = 'roadmap_quiz_correct' 
                # Überprüfen, ob 'roadmap_quiz_correct' in xp_gains existiert, ansonsten Fallback
                # Für dieses Beispiel nehmen wir an, es gibt einen Eintrag oder wir verwenden einen Standardwert.
                # Sie sollten sicherstellen, dass 'roadmap_quiz_correct' in Ihrer xp_gains Tabelle existiert.
                # INSERT INTO xp_gains (action, xp_amount, description) VALUES ('roadmap_quiz_correct', 75, 'Awarded for correctly answering a roadmap quiz') ON CONFLICT (action) DO NOTHING;
                xp_to_award = roadmap_handler.get_xp_for_action(xp_action_name)
                if xp_to_award == 0: # Fallback, falls 'roadmap_quiz_correct' nicht existiert, aber 'daily_quiz'
                    xp_to_award = roadmap_handler.get_xp_for_action('daily_quiz') # Beispiel-Fallback
                    if xp_to_award == 0: # Hardcoded Fallback
                        xp_to_award = 50 
                
                if xp_to_award > 0:
                    xp_update_info = roadmap_handler.add_xp_to_user(user_id, xp_to_award)
                    flash_message = f"Richtig! 🎉 Du hast {xp_to_award} XP erhalten."
                    if xp_update_info and xp_update_info.get("level_up"):
                        flash_message += f" Level Up! Du bist jetzt Level {xp_update_info['new_level']}! 🚀"
                    flash(flash_message, "success")
                else:
                    flash("Richtig! 🎉", "success")
            else:
                flash(f"Leider falsch. Die richtige Antwort war: {quiz['correct_answer']}", "warning")

        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung der Quiz-Antwort: {e}", exc_info=True)
            flash("Ein interner Fehler ist aufgetreten. Bitte versuche es später erneut.", "error")

        return redirect(url_for('roadmap.roadmap_step', roadmap_id=roadmap_id, step_id=step_id))
    
    # GET-Anfragen zu dieser Route sind nicht vorgesehen
    return redirect(url_for('roadmap.roadmap'))


