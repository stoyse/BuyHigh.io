from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify
import os
from datetime import datetime, timedelta
import functools
import json

import db_handler
import auth
import stock_data

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24) # Replace with a strong, static secret key in production

# Initialize database
db_handler.init_db()

# Decorator for routes that require login
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("You need to be logged in to view this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return view(**kwargs)
    return wrapped_view

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db_handler.get_user_by_id(user_id)

@app.route('/')
@login_required
def index():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    return render_template('index.html', darkmode=dark_mode_active)

@app.route('/dashboard')
@login_required
def dashboard():
    # Determine if dark mode should be active based on user's theme preference
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    return render_template('dashboard.html', user=g.user, darkmode=dark_mode_active)

@app.route('/trade')
@login_required
def trade():
    # Determine if dark mode should be active based on user's theme preference
    dark_mode_active = g.user and g.user.get('theme') == 'dark'
    return render_template('trade.html', user=g.user, darkmode=dark_mode_active)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    dark_mode_active = g.user and g.user.get('theme') == 'dark'

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'theme_settings':
            new_theme = request.form.get('theme')
            if new_theme in ['light', 'dark']:
                if db_handler.update_user_theme(g.user['id'], new_theme):
                    flash('Theme erfolgreich aktualisiert.', 'success')
                    # Update g.user for the current request so the theme change is reflected immediately
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
            elif not auth.check_password(g.user['password_hash'], current_password):
                flash('Aktuelles Passwort ist nicht korrekt.', 'danger')
            elif new_password != confirm_new_password:
                flash('Die neuen Passwörter stimmen nicht überein.', 'danger')
            elif len(new_password) < 6: # Beispiel für eine Mindestlänge
                flash('Das neue Passwort muss mindestens 6 Zeichen lang sein.', 'danger')
            else:
                new_password_hash = auth.hash_password(new_password)
                if db_handler.update_user_password(g.user['id'], new_password_hash):
                    flash('Passwort erfolgreich geändert.', 'success')
                else:
                    flash('Fehler beim Ändern des Passworts.', 'danger')
        
        # Redirect to refresh the page and clear POST data, or to show updated g.user theme
        return redirect(url_for('settings'))

    return render_template('settings.html', user=g.user, darkmode=dark_mode_active)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('index'))
        
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
            hashed_password = auth.hash_password(password)
            if db_handler.add_user(username, email, hashed_password):
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                error = "Registration failed due to a database error."
        
        if error:
            flash(error, 'danger')

    dark_mode_active = request.args.get('darkmode', 'False').lower() == 'true' # Or from a global setting
    return render_template('register.html', darkmode=dark_mode_active)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        user = db_handler.get_user_by_username(username)

        if user is None:
            error = 'Incorrect username.'
        elif not auth.check_password(user['password_hash'], password):
            error = 'Incorrect password.'

        if error is None and user:
            session.clear()
            session['user_id'] = user['id']
            db_handler.update_last_login(user['id'])
            flash('Login successful!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        
        if error:
            flash(error, 'danger')

    dark_mode_active = request.args.get('darkmode', 'False').lower() == 'true' # Or from a global setting
    return render_template('login.html', darkmode=dark_mode_active)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/api/stock-data')
@login_required
def api_stock_data():
    symbol = request.args.get('symbol', 'AAPL')
    timeframe = request.args.get('timeframe', '3M')
    
    # Calculate date range based on timeframe
    end_date = datetime.now().strftime('%Y-%m-%d')
    days = 90  # Default to 3 months
    
    if timeframe == '1W':
        days = 7
    elif timeframe == '1M':
        days = 30
    elif timeframe == '3M':
        days = 90
    elif timeframe == '6M':
        days = 180
    elif timeframe == '1Y':
        days = 365
    elif timeframe == 'ALL':
        days = 1825  # 5 years
    
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    try:
        # Get real stock data
        df = stock_data.get_stock_data(symbol, start_date, end_date)
        
        # If no data found, try demo data
        if df.empty:
            df = stock_data.get_demo_stock_data(symbol, days)
        
        # Convert to list of dictionaries for JSON response
        data = []
        for index, row in df.iterrows():
            data.append({
                'date': index.strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # db_handler.py now ensures the 'database' directory exists
    app.run(debug=True)
