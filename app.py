from flask import Flask, request, session, flash, g, redirect, url_for
import os
import datetime
from flask_socketio import SocketIO
import logging  # Import logging

import db_handler
import transactions_handler

# Import Blueprints
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.api_routes import api_bp
from routes.chat_routes import chat_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # Replace with a strong, static secret key in production
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure basic logging if not already configured
# This ensures logger.debug messages will be shown if the root logger level is DEBUG
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)  # Get a logger for this module

# Initialize database
db_handler.init_db()
transactions_handler.init_asset_types()  # Ensure asset types are initialized

@app.before_request
def load_logged_in_user():
    # Log details for every request to understand session and g.user behavior
    logger.debug(f"--- Request to {request.path} ---")
    logger.debug(f"Session contents: {dict(session)}")
    user_id = session.get('user_id')
    
    if user_id is None:
        g.user = None
        logger.debug(f"No 'user_id' in session. g.user is None.")
    else:
        logger.debug(f"Found 'user_id': {user_id} in session. Attempting to load user.")
        g.user = db_handler.get_user_by_id(user_id)
        if g.user:
            logger.debug(f"Successfully loaded user (ID: {g.user.get('id')}, Username: {g.user.get('username')}) into g.user.")
        else:
            logger.warning(f"'user_id' {user_id} was in session, but no user found in DB. g.user is None.")
            # Consider clearing the invalid user_id from session:
            # session.pop('user_id', None) 
            # g.user = None # Ensure g.user is None if DB lookup fails
    logger.debug(f"g.user after load_logged_in_user: {g.user}")
    logger.debug(f"--- End of load_logged_in_user for {request.path} ---")

# Define the custom Jinja2 filter
@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    try:
        # Convert the timestamp to a readable date
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return "Invalid date"

# Register the filter with the app
app.jinja_env.filters['timestamp_to_date'] = timestamp_to_date

# Register Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)  # auth_bp has /login, /register, /logout
app.register_blueprint(api_bp, url_prefix='/api')  # api_bp has its own url_prefix defined
app.register_blueprint(chat_bp, url_prefix='/chat')  # Neuer Blueprint

# SocketIO Event-Handler aus chat_routes importieren, um sie zu registrieren
from routes.chat_routes import register_chat_events
register_chat_events(socketio)

# Ensure the app object is exposed for WSGI servers
application = app

if __name__ == '__main__':
    # Only for local development
    logger.info("Starting Flask app with SocketIO in debug mode...")
    socketio.run(app, debug=True)
