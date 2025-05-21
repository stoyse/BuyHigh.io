import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
import requests  # For Firebase REST API
import os
import dotenv
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Lade .env Datei falls vorhanden
dotenv.load_dotenv()

# Initialize Firebase Admin SDK
def initialize_firebase_admin_sdk():
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'firebase-service-account-key.json')
    if os.path.exists(cred_path):
        try:
            cred = credentials.Certificate(cred_path)
            if not firebase_admin._apps:  # Initialize only if not already done
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully.")
            else:
                logger.info("Firebase Admin SDK already initialized.")
        except Exception as e:
            logger.error(f"Error initializing Firebase Admin SDK: {e}")
    else:
        logger.error(f"Firebase service account key not found at {cred_path}. Please ensure the file exists and the path is correct.")

# Call initialize_firebase_admin_sdk at module level if not already initialized by app.py
if not firebase_admin._apps:
    initialize_firebase_admin_sdk()

# Get Firebase Web API Key from various sources with fallbacks
def get_firebase_web_api_key():
    """Get Firebase Web API Key from various sources with fallbacks"""
    api_key = os.getenv('FIREBASE_WEB_API_KEY')
    if api_key:
        return api_key
    
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                api_key = config.get('FIREBASE_WEB_API_KEY')
                if api_key:
                    return api_key
    except Exception as e:
        print(f"Error reading config.json: {e}")
    
    try:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('FIREBASE_WEB_API_KEY='):
                        api_key = line.strip().split('=', 1)[1].strip('\'"')
                        if api_key:
                            return api_key
    except Exception as e:
        print(f"Error reading .env file: {e}")
    
    return None

# Get Firebase Web API Key
FIREBASE_WEB_API_KEY = get_firebase_web_api_key()

# Display clear error about the missing API Key
if not FIREBASE_WEB_API_KEY:
    error_message = """
    ============================================
    FEHLER: FIREBASE_WEB_API_KEY ist nicht gesetzt!
    ============================================
    
    Bitte setze den Firebase Web API Key mit einer dieser Methoden:
    
    1. Als Umgebungsvariable:
       export FIREBASE_WEB_API_KEY=dein_api_key
       
    2. In einer .env Datei im Projektverzeichnis:
       FIREBASE_WEB_API_KEY=dein_api_key
       
    3. In einer config.json Datei im Projektverzeichnis:
       {
         "FIREBASE_WEB_API_KEY": "dein_api_key"
       }
       
    Den API Key findest du in der Firebase Console unter:
    Project Settings -> Web API Key
    """
    print(error_message)

def create_firebase_user(email, password, username):
    """Creates a new user in Firebase Authentication."""
    try:
        user_record = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=username
        )
        return user_record.uid
    except firebase_auth.EmailAlreadyExistsError:
        raise ValueError(f"Email {email} is already registered with Firebase.")
    except Exception as e:
        logger.error(f"Firebase user creation error: {e}")
        raise ValueError(f"Could not create user in Firebase: {e}")

def login_firebase_user_rest(email, password):
    """
    Signs in a user using Firebase Auth REST API.
    Returns user's UID and ID token on success.
    """
    if not FIREBASE_WEB_API_KEY:
        error_message = "FIREBASE_WEB_API_KEY ist nicht gesetzt. Login unmöglich."
        logger.error(error_message)
        raise EnvironmentError(error_message)

    rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    try:
        logger.info(f"Attempting Firebase login for email: {email}")
        response = requests.post(rest_api_url, json=payload)
        
        if response.status_code == 400:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Unknown error")
            logger.warning(f"Firebase login failed with error: {error_message}")
            
            if error_message == "INVALID_LOGIN_CREDENTIALS":
                raise ValueError("Ungültige Anmeldedaten. E-Mail oder Passwort falsch oder Benutzer existiert nicht.")
            elif "INVALID_PASSWORD" in error_message:
                raise ValueError("Falsches Passwort.")
            elif "EMAIL_NOT_FOUND" in error_message:
                raise ValueError("Kein Konto mit dieser E-Mail-Adresse gefunden.")
            elif "USER_DISABLED" in error_message:
                raise ValueError("Dieses Konto wurde deaktiviert.")
            elif "TOO_MANY_ATTEMPTS_TRY_LATER" in error_message:
                raise ValueError("Zu viele fehlgeschlagene Anmeldeversuche. Bitte versuche es später erneut.")
            else:
                raise ValueError(f"Firebase login failed: {error_message}")
        
        response.raise_for_status()
        data = response.json()
        logger.info(f"Firebase login successful for email: {email}")
        return data.get('localId'), data.get('idToken')
    except requests.exceptions.HTTPError as e:
        error_json = e.response.json() if hasattr(e, 'response') and e.response is not None else {}
        error_message = error_json.get("error", {}).get("message", "Unknown login error")
        logger.warning(f"Firebase HTTP error: {error_message}")
        raise ValueError(f"Firebase login failed: {error_message}")
    except Exception as e:
        logger.error(f"Firebase REST API login error: {e}")
        raise ValueError(f"Could not sign in via Firebase REST API: {e}")

def delete_firebase_user(uid):
    """Deletes a user from Firebase Authentication."""
    try:
        firebase_auth.delete_user(uid)
        return True
    except Exception as e:
        logger.error(f"Error deleting Firebase user {uid}: {e}")
        return False

def verify_firebase_password_rest(email, password):
    """
    Verifies a user's password using the Firebase Auth REST API.
    This is essentially trying to log in.
    Returns True if password is correct, False otherwise.
    """
    try:
        _, _ = login_firebase_user_rest(email, password)
        return True
    except ValueError:
        return False
    except Exception as e:
        return False

def verify_firebase_id_token(id_token):
    """Verifiziert ein Firebase ID Token mit dem Admin SDK."""
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except firebase_auth.FirebaseError as e:
        logger.error(f"Error verifying Firebase ID token: {e}")
        raise ValueError(f"Invalid Firebase ID token: {e}")
    except Exception as e:
        logger.error(f"Unexpected error verifying Firebase ID token: {e}")
        raise ValueError(f"Could not verify ID token: {e}")

def get_or_create_local_user_from_firebase(decoded_token, db):
    """
    Ruft einen Benutzer anhand der Firebase UID ab oder erstellt einen neuen Benutzer
    in der lokalen Datenbank.
    """
    firebase_uid = decoded_token['uid']
    email = decoded_token.get('email')
    if email:
        username = decoded_token.get('name') or decoded_token.get('display_name') or email.split('@')[0]
    else:
        username = decoded_token.get('name') or decoded_token.get('display_name') or f"guest_{firebase_uid[:8]}"
        email = f"{firebase_uid}@anonymous.firebase"

    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE firebase_uid = %s", (firebase_uid,))
    user = cursor.fetchone()

    if user:
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE firebase_uid = %s", (firebase_uid,))
        db.commit()
        print(f"Local user found and updated: {firebase_uid}")
    else:
        cursor.execute(
            "INSERT INTO users (username, email, firebase_uid, email_verified, last_login) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP) RETURNING id",
            (username, email, firebase_uid, decoded_token.get('email_verified', False))
        )
        user_id_row = cursor.fetchone()
        db.commit()
        user_id = user_id_row['id'] if user_id_row else None
        if user_id:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            print(f"New local user created: {firebase_uid} with username {username}")
        else:
            print(f"Failed to create new local user for firebase_uid: {firebase_uid}")
            user = None

    return user

def send_password_reset_email(email):
    """Sends a password reset email using Firebase Auth REST API."""
    if not FIREBASE_WEB_API_KEY:
        raise EnvironmentError("FIREBASE_WEB_API_KEY is not set.")

    rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
    payload = {
        "requestType": "PASSWORD_RESET",
        "email": email
    }
    try:
        response = requests.post(rest_api_url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_json = e.response.json()
        error_message = error_json.get("error", {}).get("message", "Unknown error")
        if "EMAIL_NOT_FOUND" in error_message:
            raise ValueError("No account exists with this email address.")
        raise ValueError(f"Password reset failed: {error_message}")
    except Exception as e:
        logger.error(f"Firebase REST API password reset error: {e}")
        raise ValueError(f"Could not send password reset email: {e}")

def change_firebase_password(uid, new_password):
    """Changes a Firebase user's password using the Admin SDK."""
    try:
        firebase_auth.update_user(
            uid,
            password=new_password
        )
        return True
    except firebase_auth.FirebaseError as e:
        logger.error(f"Firebase error changing password: {e}")
        if "WEAK_PASSWORD" in str(e):
            raise ValueError("Password should be at least 6 characters long")
        raise ValueError(f"Could not change password: {e}")
    except Exception as e:
        logger.error(f"Unexpected error changing Firebase password: {e}")
        raise ValueError(f"Could not change password: {e}")

def get_google_auth_url():
    """Erstellt eine Google OAuth-URL"""
    import urllib.parse
    
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    
    if not client_id or not redirect_uri:
        raise ValueError("GOOGLE_CLIENT_ID und GOOGLE_REDIRECT_URI müssen in den Umgebungsvariablen gesetzt sein")
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'email profile',
        'prompt': 'select_account'
    }
    
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
    return auth_url

def exchange_google_code(auth_code):
    """Tauscht den OAuth-Code gegen Benutzerinformationen aus"""
    import requests
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    
    if not client_id or not client_secret or not redirect_uri:
        raise ValueError("Google OAuth Konfiguration unvollständig")
    
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': auth_code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    response = requests.post(token_url, data=token_data)
    if not response.ok:
        return None
    
    token_json = response.json()
    id_info = id_token.verify_oauth2_token(
        token_json['id_token'],
        google_requests.Request(),
        client_id
    )
    
    firebase_uid = 'google_' + id_info['sub']
    
    return {
        'email': id_info['email'],
        'name': id_info.get('name'),
        'firebase_uid': firebase_uid,
        'id_token': token_json['id_token']
    }

def create_anonymous_user():
    """
    Erstellt einen anonymen Benutzer in Firebase.
    """
    try:
        if not firebase_admin._apps:
            initialize_firebase_admin_sdk()
            if not firebase_admin._apps:
                logger.error("Firebase not initialized, cannot create anonymous user.")
                return None

        user_record = firebase_admin.auth.create_user()
        logger.info(f"Anonymer Firebase-Benutzer erstellt: UID={user_record.uid}")
        return {"uid": user_record.uid}
    except Exception as e:
        logger.error(f"Fehler beim Erstellen eines anonymen Firebase-Benutzers: {e}", exc_info=True)
        return None
