from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
import db_handler
import auth as auth_module # Alias to avoid conflict with blueprint name

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

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
