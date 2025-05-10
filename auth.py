import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
import requests  # For Firebase REST API
import os

# Initialize Firebase Admin SDK
# It's better to initialize it once in app.py
# For now, ensure it's initialized before use.
# Consider moving initialization to app.py for a central place.

def initialize_firebase_app():
    # Initialisiert das Firebase Admin SDK (wird beim App-Start aufgerufen)
    # Path to your Firebase service account key JSON file
    # Recommended: Use environment variable GOOGLE_APPLICATION_CREDENTIALS
    # If not set, fallback to a local file path (adjust as needed)
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'firebase-service-account-key.json')
    if os.path.exists(cred_path):
        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            print(f"Error initializing Firebase Admin SDK: {e}")
            # Handle initialization error, maybe raise an exception or log critical error
    else:
        print(f"Firebase service account key not found at {cred_path}. Firebase Admin SDK not initialized.")
        # Handle missing key file

# Call initialization once, ideally at app startup.
# For simplicity here, but better in app.py
# if not firebase_admin._apps:
# initialize_firebase_app()
# This will be called from app.py

# Get Firebase Web API Key from environment variable or config
FIREBASE_WEB_API_KEY = os.getenv('FIREBASE_WEB_API_KEY')  # You need to set this env variable

def create_firebase_user(email, password, username):
    # Legt einen neuen User in Firebase Authentication an
    """Creates a new user in Firebase Authentication."""
    try:
        user_record = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=username  # Firebase can store a display name
        )
        return user_record.uid
    except firebase_auth.EmailAlreadyExistsError:
        raise ValueError(f"Email {email} is already registered with Firebase.")
    except Exception as e:
        # Log the detailed error from Firebase
        print(f"Firebase user creation error: {e}")
        raise ValueError(f"Could not create user in Firebase: {e}")


def login_firebase_user_rest(email, password):
    # Meldet einen User über das Firebase Auth REST API an (liefert UID und ID Token)
    """
    Signs in a user using Firebase Auth REST API.
    Returns user's UID and ID token on success.
    """
    if not FIREBASE_WEB_API_KEY:
        raise EnvironmentError("FIREBASE_WEB_API_KEY is not set.")

    rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    try:
        response = requests.post(rest_api_url, json=payload)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        data = response.json()
        return data.get('localId'), data.get('idToken')  # UID, ID Token
    except requests.exceptions.HTTPError as e:
        error_json = e.response.json()
        error_message = error_json.get("error", {}).get("message", "Unknown login error")
        if "INVALID_PASSWORD" in error_message or "EMAIL_NOT_FOUND" in error_message:
            raise ValueError("Incorrect email or password.")
        raise ValueError(f"Firebase login failed: {error_message}")
    except Exception as e:
        print(f"Firebase REST API login error: {e}")
        raise ValueError(f"Could not sign in via Firebase REST API: {e}")


def delete_firebase_user(uid):
    # Löscht einen User aus Firebase Authentication
    """Deletes a user from Firebase Authentication."""
    try:
        firebase_auth.delete_user(uid)
        return True
    except Exception as e:
        print(f"Error deleting Firebase user {uid}: {e}")
        return False

def verify_firebase_password_rest(email, password):
    # Prüft das Passwort eines Users über das Firebase Auth REST API (Login-Test)
    """
    Verifies a user's password using the Firebase Auth REST API.
    This is essentially trying to log in.
    Returns True if password is correct, False otherwise.
    """
    try:
        _, _ = login_firebase_user_rest(email, password)
        return True  # Login successful means password is correct
    except ValueError:  # Catches "Incorrect email or password" or other login failures
        return False
    except Exception:
        return False  # Catch any other unexpected errors

def verify_firebase_id_token(id_token):
    """Verifiziert ein Firebase ID Token mit dem Admin SDK."""
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except firebase_auth.FirebaseError as e:
        print(f"Error verifying Firebase ID token: {e}")
        raise ValueError(f"Invalid Firebase ID token: {e}")
    except Exception as e:
        print(f"Unexpected error verifying Firebase ID token: {e}")
        raise ValueError(f"Could not verify ID token: {e}")

def get_or_create_local_user_from_firebase(decoded_token, db): # db ist Ihre Datenbankverbindung/-cursor
    """
    Ruft einen Benutzer anhand der Firebase UID ab oder erstellt einen neuen Benutzer
    in der lokalen Datenbank.
    """
    firebase_uid = decoded_token['uid']
    email = decoded_token.get('email')
    # Firebase gibt 'name' für Google, 'displayName' könnte auch vorhanden sein
    username = decoded_token.get('name') or decoded_token.get('display_name') or email.split('@')[0] 
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE firebase_uid = ?", (firebase_uid,))
    user = cursor.fetchone()

    if user:
        # Benutzer existiert, ggf. last_login aktualisieren
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE firebase_uid = ?", (firebase_uid,))
        db.commit()
        print(f"Local user found and updated: {firebase_uid}")
    else:
        # Benutzer existiert nicht, neu erstellen
        # password_hash ist für Firebase-Benutzer nicht relevant, kann NULL bleiben
        cursor.execute(
            "INSERT INTO users (username, email, firebase_uid, email_verified, last_login) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (username, email, firebase_uid, decoded_token.get('email_verified', False))
        )
        db.commit()
        user_id = cursor.lastrowid
        # Hole den neu erstellten Benutzer, um ihn zurückzugeben (optional, aber gut für Konsistenz)
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        print(f"New local user created: {firebase_uid} with username {username}")
    
    return user # Gibt das Benutzerobjekt (als Tupel/Dict von der DB) oder None zurück

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
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_json = e.response.json()
        error_message = error_json.get("error", {}).get("message", "Unknown error")
        if "EMAIL_NOT_FOUND" in error_message:
            raise ValueError("No account exists with this email address.")
        raise ValueError(f"Password reset failed: {error_message}")
    except Exception as e:
        print(f"Firebase REST API password reset error: {e}")
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
        print(f"Firebase error changing password: {e}")
        if "WEAK_PASSWORD" in str(e):
            raise ValueError("Password should be at least 6 characters long")
        raise ValueError(f"Could not change password: {e}")
    except Exception as e:
        print(f"Unexpected error changing Firebase password: {e}")
        raise ValueError(f"Could not change password: {e}")
