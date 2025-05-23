"""
Mock authentication functions for when Firebase is not available.
"""

import logging
import os
import json

# Configure logger
logger = logging.getLogger(__name__)

def get_mock_firebase_token(email, password):
    """
    Creates a mock token for testing purposes when Firebase is not available.
    
    Args:
        email (str): User's email address
        password (str): User's password
    
    Returns:
        tuple: (firebase_uid, id_token) as mock values
    """
    # Simple validation - In practice, Firebase would do this
    if not email or not '@' in email or not password or len(password) < 6:
        raise ValueError("Invalid email or password")
    
    # Generate mock UID based on the email
    firebase_uid = f"mock-{email.split('@')[0]}-uid"
    id_token = f"mock-token-{firebase_uid}"
    
    logger.info(f"Mock authentication created for {email}: {firebase_uid}")
    
    return firebase_uid, id_token

def check_if_firebase_config_exists():
    """
    Checks if the Firebase configuration file exists.
    
    Returns:
        bool: True if the file exists, otherwise False
    """
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                              "buyhighio-firebase-adminsdk-fbsvc-df9d657bec.json")
    return os.path.isfile(config_file)
