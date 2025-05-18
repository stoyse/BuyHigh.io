from flask import Flask, request, session, flash, g, redirect, url_for, render_template, jsonify
import os
import datetime
from flask_socketio import SocketIO
import logging
from logging.handlers import RotatingFileHandler  # Hinzugefügt für Dateiprotokollierung
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import firebase_admin  # Added for Firebase Admin SDK
from flask_cors import CORS  # Importiere die Flask-CORS-Erweiterung

load_dotenv()  # Load environment variables from .env file

import database.handler.postgres.postgres_db_handler as db_handler
import database.handler.postgres.postgre_transactions_handler as transactions_handler
import auth as auth_module  # Import our updated auth module
from database.handler.postgres.postgres_db_handler import add_analytics  # Import add_analytics

# Import Blueprints
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.api_routes import api_bp  # Korrigiert von "api" zu "api_bp"
from routes.chat_routes import chat_bp
from routes.dev_routes import dev_bp
from routes.roadmap_routes import roadmap_bp
from routes.gambling_routes import gambling_bp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "https://buy-high-io.vercel.app"]}}, supports_credentials=True)  # Aktiviert CORS mit Anmeldeinformationen
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # TODO: In Produktionsumgebung sicher verwalten!
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)  # Session für 7 Tage gültig

# Configure logging early to use it immediately
if not logging.getLogger().hasHandlers():  # This check might be too simple if other libs configure logging
    logging.basicConfig(level=logging.INFO)  # Changed from DEBUG to INFO for less noise from basicConfig
logger = logging.getLogger(__name__)  # Logger für app.py

# Dateiprotokollierung einrichten
log_dir = os.path.join(app.root_path, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

# Formatter für Dateiprotokolle
file_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')

# RotatingFileHandler
# Rotiert bei 1MB, behält 5 Backup-Dateien
file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.INFO)  # Changed from DEBUG to INFO for file logs unless DEBUG is truly needed for app.log

# Füge den Handler zum Root-Logger hinzu, damit alle Module ihn verwenden können
logging.getLogger().addHandler(file_handler)
# Füge den Handler auch zum App-Logger hinzu (obwohl der Root-Logger ihn bereits abdeckt, schadet es nicht)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)  # Changed from DEBUG to INFO

logger.info("Flask App Logger initialisiert und Dateiprotokollierung konfiguriert.")
add_analytics(None, "app_logger_initialized", "app:module_level")

# Load database path from environment variable or default value
DATABASE_ENV_PATH_RAW = os.getenv('DATABASE_FILE_PATH', 'database/database.db')
# Clean the path: remove potential comments
DATABASE_ENV_PATH = DATABASE_ENV_PATH_RAW.split('#')[0].strip()
logger.debug(f"Roher Wert von DATABASE_FILE_PATH (aus os.getenv): '{DATABASE_ENV_PATH_RAW}'")
logger.debug(f"Bereinigter Wert von DATABASE_FILE_PATH: '{DATABASE_ENV_PATH}'")

# Korrigiere den Datenbankpfad - verwende app.root_path direkt anstelle von '..'
if not os.path.isabs(DATABASE_ENV_PATH):
    # Wenn der Pfad relativ ist und '..' enthält, ersetze durch einen absoluten Pfad im Projektverzeichnis
    if '..' in DATABASE_ENV_PATH:
        DATABASE_ENV_PATH = os.path.join(app.root_path, 'database/database.db')
        logger.debug(f"Relativer Pfad mit '..' erkannt, ersetze durch: '{DATABASE_ENV_PATH}'")
    else:
        # Sonst kombiniere wie bisher mit app.root_path
        DATABASE_ENV_PATH = os.path.join(app.root_path, DATABASE_ENV_PATH)
        logger.debug(f"DATABASE_FILE_PATH ist relativ. Verknüpft mit app.root_path: '{DATABASE_ENV_PATH}'")
else:
    logger.debug(f"DATABASE_FILE_PATH ist absolut: '{DATABASE_ENV_PATH}'")

app.config['DATABASE'] = DATABASE_ENV_PATH
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
else:
    logger.debug(f"Datenbankverzeichnis '{db_dir}' existiert bereits oder ist nicht spezifiziert.")

# Initialize Firebase Admin SDK
if not os.getenv('FIREBASE_WEB_API_KEY'):
    logger.warning("FIREBASE_WEB_API_KEY Umgebungsvariable ist nicht gesetzt. Login-Funktionalität wird fehlschlagen.")
    add_analytics(None, "firebase_web_api_key_missing_warning", "app:module_level")

# Check if the Firebase Default-App is already initialized
if not firebase_admin._apps:
    logger.info("Keine Firebase-App von anderen Modulen initialisiert. Rufe auth_module.initialize_firebase_admin_sdk() auf.")
    # Use the renamed function from auth.py
    auth_module.initialize_firebase_admin_sdk()  # Analytics inside this function
else:
    logger.info("Firebase Admin SDK App bereits initialisiert. Überspringe redundanten Aufruf.")
    add_analytics(None, "firebase_sdk_already_initialized_skip", "app:module_level")

# --- Klarer Hinweis, welche DB verwendet wird ---
USE_FIREBASE = os.getenv('USE_FIREBASE', 'true').lower() == 'true'
if USE_FIREBASE:
    try:
        # Korrigiere den Import-Pfad - entferne 'sqlite' da es nicht existiert
        import firebase_admin.db as firebase_db_handler

        # Füge eine einfache can_use_firebase Funktion hinzu
        def can_use_firebase():
            return firebase_admin._apps and 'default' in firebase_admin._apps

        if can_use_firebase():
            logger.info("✅ SYSTEM: Verwende Firebase Realtime Database als primäres Daten-Backend.")
        else:
            logger.warning("⚠️ SYSTEM: Firebase konfiguriert, aber nicht verfügbar. Fallback auf lokale Datenbank!")
    except Exception as e:
        logger.error(f"❌ SYSTEM: Firebase Import/Initialisierung fehlgeschlagen ({e}). Verwende nur lokale Datenbank!")
else:
    logger.info("ℹ️ SYSTEM: Firebase ist in .env deaktiviert. Verwende lokale Datenbank als Daten-Backend.")

socketio = SocketIO(app, cors_allowed_origins="*")
logger.info("SocketIO initialisiert.")
add_analytics(None, "socketio_initialized", "app:module_level")

# Initialize database
logger.info("Initialisiere Datenbank und Asset-Typen...")
db_handler.init_db()  # Ensure init_db() uses app.config['DATABASE'] or is consistent
transactions_handler.init_asset_types()  # Ensure asset types are initialized
logger.info("Datenbank und Asset-Typen initialisiert.")
add_analytics(None, "db_and_asset_types_initialized", "app:module_level")

# New database helper functions
def get_db():
    if 'db' not in g:
        try:
            logger.debug("PostgreSQL-Datenbankverbindung wird geöffnet.")
            pg_host = os.getenv('POSTGRES_HOST')
            pg_port = os.getenv('POSTGRES_PORT')
            pg_db = os.getenv('POSTGRES_DB')
            pg_user = os.getenv('POSTGRES_USER')
            pg_password = os.getenv('POSTGRES_PASSWORD')
            dsn = f"dbname={pg_db} user={pg_user} password={pg_password} host={pg_host} port={pg_port}"
            g.db = psycopg2.connect(
                dsn=dsn,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            logger.debug("PostgreSQL-Datenbankverbindung erfolgreich geöffnet.")
        except psycopg2.Error as e:
            logger.error(f"PostgreSQL-Datenbankverbindungsfehler: {e}")
            raise
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
        logger.debug("PostgreSQL-Datenbankverbindung geschlossen.")
    if e:
        logger.error(f"Fehler während Teardown App Context: {e}")

@app.before_request
def load_logged_in_user():
    logger.debug(f"--- Request zu {request.path} ---")
    logger.debug(f"Session-Inhalt: {dict(session)}")
    firebase_uid = session.get('firebase_uid')  # Changed from user_id to firebase_uid

    if firebase_uid is None:
        g.user = None
        logger.debug(f"Keine 'firebase_uid' in Session. g.user ist None.")
    else:
        logger.debug(f"Gefundene 'firebase_uid': {firebase_uid} in Session. Versuche Benutzer aus lokaler DB zu laden.")
        g.user = db_handler.get_user_by_firebase_uid(firebase_uid)
        if g.user:
            logger.info(f"Benutzer erfolgreich geladen (Lokale ID: {g.user.get('id')}, Benutzername: {g.user.get('username')}, Firebase UID: {g.user.get('firebase_uid')}) in g.user.")
            session.permanent = True  # Ensure session remains permanent on activity
        else:
            logger.warning(f"'firebase_uid' {firebase_uid} war in Session, aber kein Benutzer in lokaler DB gefunden. Lösche Session.")
            session.pop('firebase_uid', None)
            session.pop('user_id', None)  # Auch user_id entfernen, falls vorhanden
            g.user = None
    logger.debug(f"g.user nach load_logged_in_user: {g.user}")
    logger.debug(f"--- Ende von load_logged_in_user für {request.path} ---")

# Define the custom Jinja2 filter
@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    try:
        dt_object = datetime.datetime.fromtimestamp(timestamp)
        formatted_date = dt_object.strftime('%Y-%m-%d %H:%M:%S')
        logger.debug(f"Timestamp {timestamp} zu Datum konvertiert: {formatted_date}")
        return formatted_date
    except (ValueError, TypeError) as e:
        logger.warning(f"Ungültiger Timestamp für Konvertierung: {timestamp}, Fehler: {e}")
        return "Invalid date"

app.jinja_env.filters['timestamp_to_date'] = timestamp_to_date

@app.errorhandler(404)
def page_not_found(e):
    user_id_for_analytics = g.user.get('id') if hasattr(g, 'user') and g.user else None
    add_analytics(user_id_for_analytics, "error_404", f"app:page_not_found:url={request.url},error={e}")
    logger.warning(f"404 Fehler - Seite nicht gefunden: {request.url}", exc_info=e)
    return render_template('404.html'), 404

@app.errorhandler(405)
def method_not_allowed(e):
    user_id_for_analytics = g.user.get('id') if hasattr(g, 'user') and g.user else None
    add_analytics(user_id_for_analytics, "error_405", f"app:method_not_allowed:url={request.url},method={request.method},error={e}")
    logger.warning(f"405 Fehler - Methode nicht erlaubt: {request.method} für {request.url}", exc_info=e)
    return render_template('405.html'), 405

# Register Blueprints
logger.info("Registriere Blueprints...")
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(api_bp, url_prefix='/api')  # Korrigiert von "api" zu "api_bp"
app.register_blueprint(chat_bp, url_prefix='/chat')
app.register_blueprint(dev_bp, url_prefix='/dev')
app.register_blueprint(roadmap_bp, url_prefix='/roadmap')
app.register_blueprint(gambling_bp, url_prefix='/gambling')
logger.info("Blueprints registriert.")
add_analytics(None, "blueprints_registered", "app:module_level")

from routes.chat_routes import register_chat_events
logger.info("Registriere Chat-Events für SocketIO...")
register_chat_events(socketio)
logger.info("Chat-Events registriert.")
add_analytics(None, "chat_events_registered", "app:module_level")

@app.route('/auth/google-signin', methods=['POST'])
def google_signin():
    add_analytics(None, "google_signin_attempt", "app:google_signin")
    logger.info("Google Sign-In Anfrage erhalten.")
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        if not id_token:
            logger.warning("Kein ID-Token im Google Sign-In Request angegeben.")
            add_analytics(None, "google_signin_fail_no_id_token", "app:google_signin")
            return jsonify({"success": False, "error": "No ID token provided."}), 400

        logger.debug(f"Empfangenes ID-Token (erste 30 Zeichen): {id_token[:30]}...")

        decoded_token = auth_module.verify_firebase_id_token(id_token)
        logger.info(f"Firebase ID-Token verifiziert für UID: {decoded_token.get('uid')}")
        try:
            db_conn = get_db()
        except psycopg2.OperationalError as db_err:
            logger.error(f"PostgreSQL-Verbindungsfehler während Google Sign-In: {db_err}", exc_info=True)
            add_analytics(None, "google_signin_db_conn_error", f"app:google_signin:error={db_err}")
            return jsonify({"success": False, "error": "Database connection failed. Please try again later."}), 503

        local_user = auth_module.get_or_create_local_user_from_firebase(decoded_token, db_conn)

        if not local_user:
            logger.error("Fehler beim Abrufen oder Erstellen des lokalen Benutzers nach Google Sign-In.")
            add_analytics(decoded_token.get('uid'), "google_signin_fail_get_or_create_local_user", "app:google_signin")
            return jsonify({"success": False, "error": "Failed to get or create local user."}), 500

        logger.info(f"Lokaler Benutzer (ID: {local_user['id']}) für Google Sign-In erhalten/erstellt.")

        session.clear()
        session['firebase_uid'] = decoded_token['uid']
        session['user_id'] = local_user['id']
        session.permanent = True
        logger.info(f"Session für Benutzer {local_user['id']} (Firebase UID: {decoded_token.get('uid')}) nach Google Sign-In gesetzt.")
        add_analytics(local_user['id'], "google_signin_success", f"app:google_signin:uid={decoded_token.get('uid')}")

        return jsonify({"success": True, "redirect_url": url_for('main.index')})

    except ValueError as e:
        logger.error(f"ValueError während Google Sign-In: {e}", exc_info=True)
        add_analytics(None, "google_signin_value_error", f"app:google_signin:error={e}")
        return jsonify({"success": False, "error": str(e)}), 401
    except Exception as e:
        logger.error(f"Unerwarteter Fehler während Google Sign-In: {e}", exc_info=True)
        add_analytics(None, "google_signin_exception", f"app:google_signin:error={e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500

@app.route('/auth/firebase-config')
def firebase_config():
    add_analytics(None, "get_firebase_config", "app:firebase_config")
    logger.debug("Firebase-Konfigurationsanfrage empfangen.")
    config = {
        "apiKey": os.environ.get("FIREBASE_WEB_API_KEY"),
        "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
    }
    if not all([config["apiKey"], config["authDomain"], config["projectId"]]):
        logger.error("Firebase Web-Konfiguration ist unvollständig. Bitte Umgebungsvariablen prüfen.")
        add_analytics(None, "get_firebase_config_incomplete", "app:firebase_config")
        return jsonify({"error": "Firebase configuration is incomplete on the server."}), 500

    logger.debug(f"Firebase-Konfiguration gesendet: {config}")
    return jsonify(config)

@app.route('/auth/anonymous-login', methods=['POST'])
def anonymous_login():
    add_analytics(None, "anonymous_login_attempt", "app:anonymous_login")
    logger.info("Anonyme Anmeldung angefordert.")
    try:
        # Generiere eine anonyme Firebase-Benutzer-ID
        anonymous_user = auth_module.create_anonymous_user()
        if not anonymous_user:
            logger.error("Fehler beim Erstellen eines anonymen Benutzers.")
            add_analytics(None, "anonymous_login_fail_create_fb_user", "app:anonymous_login")
            return jsonify({"success": False, "error": "Failed to create anonymous user."}), 500

        logger.info(f"Anonymer Benutzer erstellt: UID={anonymous_user['uid']}")

        # Speichere den anonymen Benutzer in der lokalen Datenbank
        db_conn = get_db()
        local_user = auth_module.get_or_create_local_user_from_firebase(anonymous_user, db_conn)

        if not local_user:
            logger.error("Fehler beim Abrufen oder Erstellen des lokalen Benutzers für anonymen Login.")
            add_analytics(anonymous_user['uid'], "anonymous_login_fail_get_or_create_local_user", "app:anonymous_login")
            return jsonify({"success": False, "error": "Failed to get or create local user."}), 500

        logger.info(f"Lokaler Benutzer (ID: {local_user['id']}) für anonymen Login erhalten/erstellt.")

        # Setze die Session
        session.clear()
        session['firebase_uid'] = anonymous_user['uid']
        session['user_id'] = local_user['id']
        session.permanent = True
        logger.info(f"Session für anonymen Benutzer {local_user['id']} (Firebase UID: {anonymous_user['uid']}) gesetzt.")
        add_analytics(local_user['id'], "anonymous_login_success", f"app:anonymous_login:uid={anonymous_user['uid']}")

        return jsonify({"success": True, "redirect_url": url_for('main.index')})

    except Exception as e:
        logger.error(f"Fehler während der anonymen Anmeldung: {e}", exc_info=True)
        add_analytics(None, "anonymous_login_exception", f"app:anonymous_login:error={e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500

application = app

#if __name__ == '__main__':
#    add_analytics(None, "app_start_main_block", "app:main_block")
#    logger.info("Starte Flask App mit SocketIO im Debug-Modus auf Port 5000...")
#    socketio.run(app, debug=True, port=5000)
