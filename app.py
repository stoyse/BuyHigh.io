from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import os
from datetime import datetime
import functools # Import functools

import db_handler
import auth

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
@login_required # Add the decorator here
def index():
    return render_template('index.html')

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

    return render_template('register.html')

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

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # db_handler.py now ensures the 'database' directory exists
    app.run(debug=True)
