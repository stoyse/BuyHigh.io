"""
Mock-Authentifizierungsfunktionen für den Fall, dass Firebase nicht verfügbar ist.
"""

import logging
import os
import json

# Logger konfigurieren
logger = logging.getLogger(__name__)

def get_mock_firebase_token(email, password):
    """
    Erstellt ein Mock-Token für Testzwecke, wenn Firebase nicht verfügbar ist.
    
    Args:
        email (str): E-Mail-Adresse des Benutzers
        password (str): Passwort des Benutzers
    
    Returns:
        tuple: (firebase_uid, id_token) als Mock-Werte
    """
    # Einfache Validierung - In der Praxis würde Firebase dies tun
    if not email or not '@' in email or not password or len(password) < 6:
        raise ValueError("Ungültige E-Mail oder Passwort")
    
    # Mock-UID basierend auf der E-Mail generieren
    firebase_uid = f"mock-{email.split('@')[0]}-uid"
    id_token = f"mock-token-{firebase_uid}"
    
    logger.info(f"Mock-Authentifizierung für {email} erstellt: {firebase_uid}")
    
    return firebase_uid, id_token

def check_if_firebase_config_exists():
    """
    Überprüft, ob die Firebase-Konfigurationsdatei existiert.
    
    Returns:
        bool: True, wenn die Datei existiert, sonst False
    """
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                              "buyhighio-firebase-adminsdk-fbsvc-df9d657bec.json")
    return os.path.isfile(config_file)
