import requests
import logging

# Firebase API Key
FIREBASE_API_KEY = "your_firebase_api_key_here"

def sign_in_with_email_password(email, password):
    """Authentifiziere einen Benutzer mit E-Mail und Passwort"""
    logger = logging.getLogger(__name__)
    
    try:
        # Debug-Logging
        logger.info(f"Attempting to sign in user with email: {email}")
        
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
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
        
        # Detaillierte Fehlermeldungen
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