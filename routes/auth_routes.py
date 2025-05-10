from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
import db_handler
import auth as auth_module # Alias to avoid conflict with blueprint name
from utils import login_required # Import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        error = None
        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif db_handler.get_user_by_username(username):
            error = f"User {username} is already registered."
        elif db_handler.get_user_by_email(email):
            error = f"Email {email} is already registered."

        if error is None:
            hashed_password = auth_module.hash_password(password)
            if db_handler.add_user(username, email, hashed_password):
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            else:
                error = "Registration failed due to a database error."
        
        if error:
            flash(error, 'danger')

    dark_mode_active = request.args.get('darkmode', 'False').lower() == 'true'
    return render_template('register.html', darkmode=dark_mode_active)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        user = db_handler.get_user_by_username(username)

        if user is None:
            error = 'Incorrect username.'
        elif not auth_module.check_password(user['password_hash'], password):
            error = 'Incorrect password.'

        if error is None and user:
            session.clear()
            session['user_id'] = user['id']
            db_handler.update_last_login(user['id'])
            flash('Login successful!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.index'))
        
        if error:
            flash(error, 'danger')

    dark_mode_active = request.args.get('darkmode', 'False').lower() == 'true'
    return render_template('login.html', darkmode=dark_mode_active)

@auth_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        current_password = request.form.get('current_password_for_delete')

        if not current_password:
            flash('Passwort zur Bestätigung erforderlich.', 'danger')
            return redirect(url_for('main.settings'))

        if not g.user: # Should be caught by @login_required, but as a safeguard
            flash('Benutzer nicht gefunden.', 'danger')
            return redirect(url_for('auth.login'))

        if not auth_module.check_password(g.user['password_hash'], current_password):
            flash('Aktuelles Passwort ist nicht korrekt.', 'danger')
            return redirect(url_for('main.settings'))

        # Proceed with deletion
        if db_handler.delete_user(g.user['id']):
            session.clear() # Log out the user
            flash('Ihr Konto wurde erfolgreich gelöscht.', 'success')
            return redirect(url_for('main.index')) # Redirect to home or login page
        else:
            flash('Fehler beim Löschen des Kontos. Bitte versuchen Sie es später erneut.', 'danger')
            return redirect(url_for('main.settings'))
    
    # GET request not allowed for this route directly, redirect to settings
    return redirect(url_for('main.settings'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
