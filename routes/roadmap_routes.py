from flask import Blueprint, render_template, g, request, flash, redirect, url_for, jsonify, current_app
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
    # Find the current step by step_id
    current_step = next((item for item in data if str(item['id']) == str(step_id)), None)
    page_layout = current_step.get('page_layout', []) if current_step else []
    print(f'[red]Current Step: {current_step}[/red]')
    print(f'[blue]Page Layout: {page_layout}[/blue]')

    # Dynamisches Laden der Karten-Daten, falls page_layout nur IDs enthält
    if all(isinstance(item, int) for item in page_layout):
        page_layout = [
            {"layout_number": layout_id, "card_html": None} for layout_id in page_layout
        ]
        print(f'[green]Transformed Page Layout: {page_layout}[/green]')

    for item in page_layout:
        print(f'[yellow]Processing item: {item}[/yellow]')
        if isinstance(item, dict):  # Sicherstellen, dass item ein Dictionary ist
            layout_number = item.get('layout_number')
            print(f'[cyan]Layout Number: {layout_number}[/cyan]')
            if layout_number is not None:
                # Allgemeiner Pfad zu den Karten-Dateien
                card_filename = f"{roadmap_id}_{step_id}_{layout_number}.html"
                card_path = os.path.join(current_app.root_path, "templates", "roadmap", "step_cards", card_filename)
                print(f'[blue]Card Path: {card_path}[/blue]')
                try:
                    with open(card_path, "r") as card_file:
                        item['card_html'] = card_file.read()
                        print(f'[green]Loaded HTML for {card_filename}[/green]')
                except FileNotFoundError:
                    item['card_html'] = f"<!-- Card file {card_filename} not found -->"
                    print(f'[red]Card file {card_filename} not found[/red]')
        else:
            logger.error(f"Unexpected item type in page_layout: {type(item)}")
            print(f'[red]Unexpected item type in page_layout: {type(item)}[/red]')
    # Now, each item in page_layout has a 'card_html' key with the HTML content.
    # Pass page_layout to the template and render the HTML using the |safe filter in Jinja2.
    return render_template('roadmap/step.html',
                           user=g.user,
                           darkmode=dark_mode_active,
                           roadmap=roadmap_handler.get_roadmap(roadmap_id),
                           roadmap_steps=data,
                           roadmap_quiz=roadmap_handler.get_roadmap_quizes_stepid(step_id),
                           page_layout=page_layout,
                           current_step=current_step)


