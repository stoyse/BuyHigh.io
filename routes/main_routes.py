from flask import Blueprint, render_template, g, request, flash, redirect, url_for
from utils import login_required
import db_handler

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    return render_template('index.html', darkmode=dark_mode_active)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    
    # Import transactions_handler locally to avoid potential circular imports at top level
    # if transactions_handler itself might import something from app or routes in a complex setup.
    # For now, direct import should be fine if transactions_handler is self-contained.
    import transactions_handler 
    portfolio_data = transactions_handler.show_user_portfolio(g.user['id'])
    recent_transactions_data = transactions_handler.get_recent_transactions(g.user['id'])
    
    return render_template('dashboard.html', 
                           user=g.user, 
                           darkmode=dark_mode_active,
                           portfolio_data=portfolio_data,
                           recent_transactions=recent_transactions_data.get('transactions', []))

@main_bp.route('/trade')
@login_required
def trade():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    return render_template('trade.html', user=g.user, darkmode=dark_mode_active)

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    # Import auth module locally for password checking if needed, or ensure it's imported at top
    import auth as auth_module


    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'theme_settings':
            new_theme = request.form.get('theme')
            if new_theme in ['light', 'dark']:
                if db_handler.update_user_theme(g.user['id'], new_theme):
                    flash('Theme erfolgreich aktualisiert.', 'success')
                    g.user = db_handler.get_user_by_id(g.user['id']) 
                    dark_mode_active = g.user and g.user.get('theme') == 'dark'
                else:
                    flash('Fehler beim Aktualisieren des Themes.', 'danger')
            else:
                flash('Ungültige Theme-Auswahl.', 'danger')

        elif form_type == 'password_settings':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')

            if not current_password or not new_password or not confirm_new_password:
                flash('Alle Passwortfelder müssen ausgefüllt sein.', 'danger')
            elif not auth_module.check_password(g.user['password_hash'], current_password):
                flash('Aktuelles Passwort ist nicht korrekt.', 'danger')
            elif new_password != confirm_new_password:
                flash('Die neuen Passwörter stimmen nicht überein.', 'danger')
            elif len(new_password) < 6:
                flash('Das neue Passwort muss mindestens 6 Zeichen lang sein.', 'danger')
            else:
                new_password_hash = auth_module.hash_password(new_password)
                if db_handler.update_user_password(g.user['id'], new_password_hash):
                    flash('Passwort erfolgreich geändert.', 'success')
                else:
                    flash('Fehler beim Ändern des Passworts.', 'danger')
        
        return redirect(url_for('main.settings'))

    return render_template('settings.html', user=g.user, darkmode=dark_mode_active)
