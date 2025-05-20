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
    if not firebase_admin._apps:
        logger.error("UTILS.AUTH: Firebase App nicht initialisiert. Token-Überprüfung nicht möglich.")
        return None
    try:
        decoded_token = firebase_auth_module.verify_id_token(id_token)
        uid = decoded_token.get('uid')
        logger.info(f"UTILS.AUTH: ID-Token erfolgreich verifiziert für UID: {uid}")
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
