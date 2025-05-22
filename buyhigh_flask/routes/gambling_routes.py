from flask import Blueprint, render_template, g, request, flash, redirect, url_for, jsonify, session, current_app
from utils.utils import login_required
import database.handler.postgres.postgres_db_handler as db_handler
import logging  # Add logging import
from rich import print
import database.handler.postgres.postgre_education_handler as edu_handler
import database.handler.postgres.postgre_market_mayhem_handler as market_mayhem_handler
import inspect
# from database.handler.postgres.postgres_db_handler import add_analytics # Entfernt
from database.handler.postgres.postgre_market_mayhem_handler import get_all_mayhem

# Configure basic logging
# logging.basicConfig(level=logging.DEBUG) # Wird jetzt in app.py global konfiguriert
logger = logging.getLogger(__name__)

gambling_bp = Blueprint('gambling', __name__)

@gambling_bp.route('/')
@login_required
def gambling_index():
    """
    Render the gambling index page.
    """
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    return render_template('gambling/index.html',
                           user=g.user, 
                           darkmode=dark_mode_active)

@gambling_bp.route('/market_mayhem')
def market_mayhem():
    # add_analytics(request,inspect.currentframe().f_code.co_name) # Entfernt
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401