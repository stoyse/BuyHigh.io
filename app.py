from flask import Flask, request, session, flash, g, redirect, url_for, render_template, jsonify
import os
import datetime
from flask_socketio import SocketIO
import logging
import sqlite3
from dotenv import load_dotenv  # Added for loading .env files

load_dotenv()  # Load environment variables from .env file

import db_handler
import transactions_handler
import auth as auth_module  # Import our updated auth module

# Import Blueprints
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.api_routes import api_bp
from routes.chat_routes import chat_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # Replace with a strong, static secret key in production

# Configure logging early to use it immediately
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load database path from environment variable or default value
DATABASE_ENV_PATH_RAW = os.getenv('DATABASE_FILE_PATH', 'database/database.db')
# Clean the path: remove potential comments
DATABASE_ENV_PATH = DATABASE_ENV_PATH_RAW.split('#')[0].strip()
logger.debug(f"Roher Wert von DATABASE_FILE_PATH (aus os.getenv): '{DATABASE_ENV_PATH_RAW}'")
logger.debug(f"Bereinigter Wert von DATABASE_FILE_PATH: '{DATABASE_ENV_PATH}'")

if not os.path.isabs(DATABASE_ENV_PATH):
    app.config['DATABASE'] = os.path.join(app.root_path, DATABASE_ENV_PATH)
    logger.debug(f"DATABASE_FILE_PATH ist relativ. Verknüpft mit app.root_path: '{app.config['DATABASE']}'")
else:
    app.config['DATABASE'] = DATABASE_ENV_PATH
    logger.debug(f"DATABASE_FILE_PATH ist absolut: '{app.config['DATABASE']}'")

logger.info(f"Finaler app.config['DATABASE'] Pfad ist gesetzt auf: {app.config['DATABASE']}")

# Ensure the database directory exists
db_dir = os.path.dirname(app.config['DATABASE'])
if db_dir and not os.path.exists(db_dir):
    try:
        os.makedirs(db_dir, exist_ok=True)  # exist_ok=True prevents errors if the directory already exists
        logger.info(f"Datenbankverzeichnis erstellt: {db_dir}")
    except OSError as e:
        logger.error(f"Fehler beim Erstellen des Datenbankverzeichnisses {db_dir}: {e}")
        # Consider terminating the application if this is critical.

# Initialize Firebase Admin SDK
if not os.getenv('FIREBASE_WEB_API_KEY'):
    print("WARNING: FIREBASE_WEB_API_KEY environment variable is not set. Login functionality will fail.")
auth_module.initialize_firebase_app()  # Initialize Firebase

socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize database
db_handler.init_db()  # Ensure init_db() uses app.config['DATABASE'] or is consistent
transactions_handler.init_asset_types()  # Ensure asset types are initialized

# New database helper functions
def get_db():
    if 'db' not in g:
        try:
            g.db = sqlite3.connect(
                app.config['DATABASE'],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.before_request
def load_logged_in_user():
    logger.debug(f"--- Request to {request.path} ---")
    logger.debug(f"Session contents: {dict(session)}")
    firebase_uid = session.get('firebase_uid')  # Changed from user_id to firebase_uid
    
    if firebase_uid is None:
        g.user = None
        logger.debug(f"No 'firebase_uid' in session. g.user is None.")
    else:
        logger.debug(f"Found 'firebase_uid': {firebase_uid} in session. Attempting to load user from local DB.")
        g.user = db_handler.get_user_by_firebase_uid(firebase_uid)
        if g.user:
            logger.debug(f"Successfully loaded user (Local ID: {g.user.get('id')}, Username: {g.user.get('username')}, Firebase UID: {g.user.get('firebase_uid')}) into g.user.")
        else:
            logger.warning(f"'firebase_uid' {firebase_uid} was in session, but no user found in local DB. Clearing session.")
            session.pop('firebase_uid', None) 
            g.user = None
    logger.debug(f"g.user after load_logged_in_user: {g.user}")
    logger.debug(f"--- End of load_logged_in_user for {request.path} ---")

# Define the custom Jinja2 filter
@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    try:
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return "Invalid date"

app.jinja_env.filters['timestamp_to_date'] = timestamp_to_date

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return render_template('405.html'), 405

# Register Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(chat_bp, url_prefix='/chat')

from routes.chat_routes import register_chat_events
register_chat_events(socketio)

@app.route('/auth/google-signin', methods=['POST'])
def google_signin():
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        if not id_token:
            return jsonify({"success": False, "error": "No ID token provided."}), 400

        decoded_token = auth_module.verify_firebase_id_token(id_token)
        db_conn = get_db()  # Changed: Uses the newly defined get_db() function
        local_user = auth_module.get_or_create_local_user_from_firebase(decoded_token, db_conn)

        if not local_user:
            return jsonify({"success": False, "error": "Failed to get or create local user."}), 500

        session.clear()
        session['firebase_uid'] = decoded_token['uid']
        session.permanent = True

        return jsonify({"success": True, "redirect_url": url_for('main.index')})  # Korrigiert von 'index' zu 'main.index'

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 401
    except Exception as e:
        logger.error(f"Unexpected error during Google sign-in: {e}", exc_info=True)
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500

@app.route('/auth/firebase-config')
def firebase_config():
    config = {
        "apiKey": os.environ.get("FIREBASE_WEB_API_KEY"),
        "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
    }
    if not all([config["apiKey"], config["authDomain"], config["projectId"]]):
        print("ERROR: Firebase Web configuration is incomplete. Please check the environment variables.")
        return jsonify({"error": "Firebase configuration is incomplete on the server."}), 500
        
    return jsonify(config)

application = app

if __name__ == '__main__':
    logger.info("Starting Flask app with SocketIO in debug mode...")
    socketio.run(app, debug=True, port=5000)
