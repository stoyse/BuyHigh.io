import firebase_admin
from firebase_admin import credentials, auth as firebase_auth_sdk  # Alias für Firebase Admin Auth
import requests
import logging
import os
from datetime import datetime, timedelta  # Hinzugefügt für Token-Überprüfung

# Firebase Web API Key (wird für REST API Aufrufe benötigt)
FIREBASE_WEB_API_KEY = os.getenv('FIREBASE_WEB_API_KEY')

# Logger konfigurieren
logger = logging.getLogger(__name__)

# --- Firebase Admin SDK Initialisierung ---
# Diese Funktion wird nun von app.py aufgerufen, um eine zentrale Initialisierung sicherzustellen.
_admin_sdk_initialized = False

def initialize_firebase_app():
    global _admin_sdk_initialized
    if _admin_sdk_initialized:
        logger.debug("Firebase Admin SDK bereits initialisiert.")
        return True
    
    logger.info("Initialisiere Firebase Admin SDK...")
    try:
        cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not cred_path:
            logger.error("GOOGLE_APPLICATION_CREDENTIALS Umgebungsvariable nicht gesetzt. Firebase Admin SDK kann nicht initialisiert werden.")
            return False
        if not os.path.exists(cred_path):
            logger.error(f"Firebase Admin SDK Anmeldeinformationsdatei nicht gefunden: {cred_path}")
            return False

        # Prüfe, ob schon eine Default-App existiert (könnte von firebase_db_handler kommen)
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK erfolgreich initialisiert (neue App).")
        else:
            logger.info("Firebase Admin SDK: Verwende existierende Default-App.")
            
        _admin_sdk_initialized = True
        return True
    except Exception as e:
        logger.error(f"Fehler bei der Initialisierung des Firebase Admin SDK: {e}", exc_info=True)
        _admin_sdk_initialized = False
        return False

# Sicherstellen, dass die Initialisierung beim Import des Moduls versucht wird,
# falls app.py es nicht explizit tut (obwohl es das sollte).
if not _admin_sdk_initialized:
    initialize_firebase_app()

def sign_in_with_email_password(email, password):
    """Authentifiziere einen Benutzer mit E-Mail und Passwort"""
    logger = logging.getLogger(__name__)
    
    try:
        # Debug-Logging
        logger.info(f"Attempting to sign in user with email: {email}")
        
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Macht Fehler sichtbarer
        
        data = response.json()
        logger.info(f"Firebase authentication successful for email: {email}")
        return data
        
    except requests.exceptions.HTTPError as e:
        error_json = e.response.json() if hasattr(e, 'response') and e.response is not None else {}
        error_message = error_json.get('error', {}).get('message', 'Unknown error')
        
        # More detailed error messages based on error code
        if error_message == 'EMAIL_NOT_FOUND':
            logger.error(f"Login failed: Email not registered in Firebase: {email}")
        elif error_message == 'INVALID_PASSWORD':
            logger.error(f"Login failed: Invalid password for email: {email}")
        elif error_message == 'USER_DISABLED':
            logger.error(f"Login failed: User account is disabled: {email}")
        else:
            logger.error(f"Login failed with error: {error_message} for email: {email}")
            
        return None
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        return None
    
def sign_in_anonymously():
    """Meldet einen Benutzer anonym über Firebase an"""
    logger = logging.getLogger(__name__)

    try:
        logger.info("Attempting anonymous Firebase login...")

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
        payload = {
            "returnSecureToken": True
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        logger.info("Anonymous Firebase login successful.")
        logger.debug(f"User ID: {data.get('localId')}, ID Token: {data.get('idToken')}")
        return data

    except requests.exceptions.HTTPError as e:
        error_json = e.response.json() if hasattr(e, 'response') and e.response is not None else {}
        error_message = error_json.get('error', {}).get('message', 'Unknown error')
        logger.error(f"Anonymous login failed with error: {error_message}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during anonymous login: {str(e)}")
        return None