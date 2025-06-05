import firebase_admin
from firebase_admin import credentials, auth as firebase_auth_module
import os
import logging

# Logger für dieses Modul. Verwende den gleichen Logger-Namen wie in router/__init__.py
# oder einen spezifischen für utils.auth, falls gewünscht.
# Hier verwenden wir einen neuen Logger für Klarheit.
logger = logging.getLogger("buyhigh.utils.auth")
if not logger.hasHandlers(): # Handler nur einmal hinzufügen
    # Konfiguriere den Logger, wenn er noch nicht konfiguriert ist
    # (z.B. wenn dieses Modul vor der Haupt-Logger-Konfiguration importiert wird)
    handler = logging.StreamHandler() # Oder FileHandler, je nach Bedarf
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO) # Oder logging.DEBUG

def initialize_firebase_app():
    """
    Initialisiert die Firebase Admin App, falls noch nicht geschehen.
    Verlässt sich primär auf die Umgebungsvariable GOOGLE_APPLICATION_CREDENTIALS.
    """
    if not firebase_admin._apps:
        try:
            cred_path_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            logger.info(f"UTILS.AUTH: GOOGLE_APPLICATION_CREDENTIALS Wert: {cred_path_env}")

            if cred_path_env and os.path.exists(cred_path_env):
                # Wenn die Umgebungsvariable gesetzt ist und der Pfad existiert,
                # initialisiere die App ohne Argumente (SDK findet es automatisch).
                firebase_admin.initialize_app()
                logger.info(f"UTILS.AUTH: Firebase Admin SDK erfolgreich initialisiert mittels GOOGLE_APPLICATION_CREDENTIALS: {cred_path_env}")
            else:
                if cred_path_env: # Variable war gesetzt, aber Pfad ungültig
                    logger.error(f"UTILS.AUTH: GOOGLE_APPLICATION_CREDENTIALS ist auf '{cred_path_env}' gesetzt, aber die Datei wurde nicht gefunden.")
                else: # Variable war nicht gesetzt
                    logger.error("UTILS.AUTH: GOOGLE_APPLICATION_CREDENTIALS ist nicht gesetzt.")
                
                # Als absoluten Notfall-Fallback, versuche den relativen Pfad, der den ursprünglichen Fehler verursacht hat.
                # Dies sollte idealerweise nicht notwendig sein, wenn main.py die Variable korrekt setzt.
                fallback_key_filename = "buyhighio-firebase-adminsdk-fbsvc-df9d657bec.json"
                # Versuche, es im Projektstamm/utils oder Projektstamm zu finden
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # BuyHigh.io
                fallback_path_in_utils = os.path.join(project_root, "utils", fallback_key_filename)
                
                if os.path.exists(fallback_path_in_utils):
                    logger.warning(f"UTILS.AUTH: Versuche Fallback-Initialisierung mit: {fallback_path_in_utils}")
                    cred = credentials.Certificate(fallback_path_in_utils)
                    firebase_admin.initialize_app(cred)
                    logger.info(f"UTILS.AUTH: Firebase Admin SDK initialisiert mit Fallback-Schlüsseldatei: {fallback_path_in_utils}")
                else:
                    logger.critical(f"UTILS.AUTH: Firebase Admin SDK konnte nicht initialisiert werden. Weder GOOGLE_APPLICATION_CREDENTIALS noch Fallback-Schlüsseldatei ('{fallback_key_filename}') gefunden/gültig.")
                    # Hier könnte man einen Fehler auslösen, wenn Firebase kritisch ist:
                    # raise EnvironmentError("Firebase Admin SDK konnte nicht initialisiert werden.")
        except Exception as e:
            logger.critical(f"UTILS.AUTH: Kritischer Fehler bei der Initialisierung von Firebase Admin SDK: {e}", exc_info=True)

# Initialisiere Firebase, wenn dieses Modul importiert wird.
# Da main.py die Umgebungsvariable vorher setzt, sollte dies jetzt funktionieren.
initialize_firebase_app()

def create_firebase_user(email: str, password: str, display_name: str = None):
    """
    Erstellt einen neuen Benutzer in Firebase Authentication.
    """
    logger.info(f"UTILS.AUTH: create_firebase_user aufgerufen für E-Mail: {email}")
    if not firebase_admin._apps:
        logger.error("UTILS.AUTH: Firebase App nicht initialisiert. Benutzererstellung nicht möglich.")
        raise ConnectionError("Firebase ist nicht initialisiert. Benutzererstellung fehlgeschlagen.")
    
    try:
        user_record = firebase_auth_module.create_user(
            email=email,
            password=password,
            display_name=display_name,
            email_verified=False # Standardmäßig nicht verifiziert, kann später geändert werden
        )
        logger.info(f"UTILS.AUTH: Firebase-Benutzer erfolgreich erstellt: {user_record.uid} für E-Mail: {email}")
        return user_record
    except firebase_auth_module.EmailAlreadyExistsError:
        logger.warning(f"UTILS.AUTH: E-Mail {email} existiert bereits in Firebase.")
        # Hier könnten Sie den bestehenden Benutzer abrufen und zurückgeben oder einen spezifischen Fehler auslösen.
        # Für dieses Beispiel lösen wir einen ValueError aus, der im aufrufenden Code behandelt werden kann.
        raise ValueError(f"EMAIL_EXISTS: Die E-Mail-Adresse {email} wird bereits verwendet.")
    except firebase_auth_module.FirebaseError as e:
        # Allgemeiner Firebase-Fehler
        logger.error(f"UTILS.AUTH: Fehler beim Erstellen des Firebase-Benutzers für {email}: {e}")
        # Prüfen auf spezifische Fehler, z.B. schwaches Passwort
        if "WEAK_PASSWORD" in str(e).upper(): # Firebase gibt oft Fehlercodes in der Nachricht zurück
            raise ValueError("WEAK_PASSWORD: Das Passwort ist zu schwach. Es muss mindestens 6 Zeichen lang sein.")
        raise
    except Exception as e:
        logger.error(f"UTILS.AUTH: Unerwarteter Fehler beim Erstellen des Firebase-Benutzers für {email}: {e}", exc_info=True)
        raise

def login_firebase_user_rest(email: str, password: str):
    """
    Authentifiziert einen Benutzer mit Firebase E-Mail und Passwort.
    HINWEIS: Das Firebase Admin SDK dient normalerweise nicht der direkten Anmeldung von Endbenutzern
    mit E-Mail/Passwort. Dies geschieht typischerweise clientseitig oder über die Firebase Auth REST API.
    Diese Funktion ist hier als Platzhalter oder für einen spezifischen serverseitigen Anwendungsfall.
    """
    logger.info(f"UTILS.AUTH: login_firebase_user_rest aufgerufen für E-Mail: {email}")
    if not firebase_admin._apps:
        logger.error("UTILS.AUTH: Firebase App nicht initialisiert. Anmeldung nicht möglich.")
        raise ConnectionError("Firebase ist nicht initialisiert. Anmeldung fehlgeschlagen.")

    # Dies ist eine stark vereinfachte Mock-Implementierung.
    # Für eine echte E-Mail/Passwort-Anmeldung serverseitig müsste man die
    # Firebase Authentication REST API verwenden (Identity Toolkit API).
    # https://firebase.google.com/docs/reference/rest/auth
    # Das Admin SDK wird dann verwendet, um ID-Tokens zu überprüfen, die vom Client gesendet werden.

    # Beispielhafte Mock-Antwort (NICHT FÜR PRODUKTION)
    if email and password: # Sehr einfache Prüfung
        mock_uid = f"mock-uid-{email.split('@')[0]}"
        mock_id_token = f"mock-token-for-{mock_uid}" # In echt wäre dies ein JWT
        logger.info(f"UTILS.AUTH: Mock-Anmeldung erfolgreich für {email}. UID: {mock_uid}")
        return mock_uid, mock_id_token
    else:
        logger.warning(f"UTILS.AUTH: Ungültige Anmeldedaten für {email}.")
        raise ValueError("Ungültige E-Mail oder Passwort für Mock-Anmeldung.")

def verify_firebase_id_token(id_token: str):
    """
    Überprüft ein Firebase ID-Token.
    """
    logger.info("UTILS.AUTH: Entered verify_firebase_id_token") # DIAGNOSTIC LOG
    logger.debug(f"UTILS.AUTH: Token to verify (first 100 chars): {id_token[:100]}...")
    logger.debug(f"UTILS.AUTH: Token length: {len(id_token)}")
    
    if not firebase_admin._apps:
        logger.error("UTILS.AUTH: Firebase App nicht initialisiert. Token-Überprüfung nicht möglich.")
        return None
    try:
        logger.debug("UTILS.AUTH: Calling firebase_auth_module.verify_id_token...")
        decoded_token = firebase_auth_module.verify_id_token(id_token)
        uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        logger.info(f"UTILS.AUTH: ID-Token erfolgreich verifiziert für UID: {uid}, Email: {email}")
        logger.debug(f"UTILS.AUTH: Decoded token keys: {list(decoded_token.keys())}")
        return decoded_token
    except firebase_admin.auth.ExpiredIdTokenError:
        logger.warning(f"UTILS.AUTH: Firebase ID-Token ist abgelaufen.")
        return None
    except firebase_admin.auth.InvalidIdTokenError as e:
        logger.warning(f"UTILS.AUTH: Firebase ID-Token ist ungültig: {e}")
        return None
    except Exception as e:
        logger.error(f"UTILS.AUTH: Fehler bei der Überprüfung des Firebase ID-Tokens: {e}", exc_info=True)
        return None

def verify_google_id_token(id_token: str):
    """
    Verifiziert ein Google OAuth ID-Token direkt ohne Firebase.
    Dies ist notwendig für Tokens, die vom Google OAuth-Flow kommen.
    """
    logger.info("UTILS.AUTH: Entered verify_google_id_token") # DIAGNOSTIC LOG
    logger.debug(f"UTILS.AUTH: Google token to verify (first 100 chars): {id_token[:100]}...")
    logger.debug(f"UTILS.AUTH: Google token length: {len(id_token)}")
    
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests
        import os # Import os module to access environment variables
        
        # Google's Client ID - Lese aus Umgebungsvariable
        google_client_id = os.getenv("FIREBASE_CLIENT_ID")
        logger.debug(f"UTILS.AUTH: Using Google Client ID: {google_client_id[:20] if google_client_id else 'None'}...")
        
        if not google_client_id:
            logger.error("UTILS.AUTH: FIREBASE_CLIENT_ID ist nicht in den Umgebungsvariablen gesetzt.")
            return None
        
        logger.debug("UTILS.AUTH: Calling google_id_token.verify_oauth2_token...")
        # Verifiziere das Token direkt mit Google
        decoded_token = google_id_token.verify_oauth2_token(
            id_token, 
            requests.Request(), 
            google_client_id
        )
        
        logger.debug(f"UTILS.AUTH: Google token decoded. Keys: {list(decoded_token.keys())}")
        logger.debug(f"UTILS.AUTH: Google token issuer: {decoded_token.get('iss')}")
        logger.debug(f"UTILS.AUTH: Google token audience: {decoded_token.get('aud')}")
        
        # Überprüfe, ob der Issuer korrekt ist
        if decoded_token['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            logger.warning(f"UTILS.AUTH: Ungültiger Issuer: {decoded_token['iss']}")
            return None
            
        logger.info(f"UTILS.AUTH: Google OAuth Token erfolgreich verifiziert für: {decoded_token.get('email')}")
        
        # Erstelle Firebase-ähnliche Token-Struktur für Kompatibilität
        firebase_compatible_token = {
            'uid': decoded_token.get('sub'),  # Google's unique user ID
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            'picture': decoded_token.get('picture'),
            'email_verified': decoded_token.get('email_verified'),
            'iss': 'google.com'  # Markiere als Google Token
        }
        
        logger.debug(f"UTILS.AUTH: Created Firebase-compatible token: {firebase_compatible_token}")
        return firebase_compatible_token
        
    except ValueError as e:
        logger.warning(f"UTILS.AUTH: Google ID-Token Verifikation fehlgeschlagen: {e}")
        return None
    except ImportError as e:
        logger.error(f"UTILS.AUTH: Google Auth Library nicht verfügbar: {e}")
        return None
    except Exception as e:
        logger.error(f"UTILS.AUTH: Fehler bei der Google Token-Verifikation: {e}", exc_info=True)
        return None
