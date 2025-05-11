import firebase_admin
from firebase_admin import db, credentials
import json
import os
import time
import logging
from datetime import datetime
import sqlite3
import dotenv

# Configure logging
logger = logging.getLogger(__name__)
dotenv.load_dotenv()  # Ensure .env is loaded if not already done

# Firebase configuration
FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')
if not FIREBASE_DATABASE_URL:
    logger.critical("FIREBASE_DATABASE_URL environment variable not set. Firebase DB Handler cannot be initialized.")
MAX_RETRIES = 3

# Global variables for Firebase instances
_firebase_app = None
_db_instance = None
_firebase_initialized_successfully = False  # Flag for successful initialization

# Initialize Firebase Realtime Database
def initialize_firebase_db():
    """Initialize Firebase Realtime Database connection"""
    global _firebase_app, _db_instance, _firebase_initialized_successfully
    logger.debug("initialize_firebase_db called.")

    if _db_instance and _firebase_initialized_successfully:
        logger.debug("Firebase DB already successfully initialized and instance exists.")
        return _db_instance

    if _firebase_initialized_successfully and _db_instance is None:
        logger.warning("Firebase marked as successfully initialized, but _db_instance is None. Attempting reinitialization.")
        _firebase_initialized_successfully = False  # Reset for reinitialization

    if not FIREBASE_DATABASE_URL:
        logger.error("FIREBASE_DATABASE_URL not set. Firebase cannot be initialized.")
        print("DEBUG: FIREBASE_DATABASE_URL fehlt oder leer!")
        return None

    use_firebase_env = os.getenv("USE_FIREBASE", "false").lower() == "true"
    if not use_firebase_env:
        logger.warning("Firebase is disabled in configuration (USE_FIREBASE). Initialization skipped.")
        print("DEBUG: USE_FIREBASE ist nicht 'true'!")
        return None

    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path:
        logger.error("GOOGLE_APPLICATION_CREDENTIALS environment variable not set. Firebase cannot be initialized.")
        print("DEBUG: GOOGLE_APPLICATION_CREDENTIALS fehlt!")
        return None

    if not os.path.exists(cred_path):
        logger.error(f"Firebase credentials file not found: {cred_path}")
        print(f"DEBUG: Credentials-Datei nicht gefunden: {cred_path}")
        return None

    try:
        if not firebase_admin._apps:
            logger.info(f"Initializing new Firebase app with credentials: {cred_path} and DB URL: {FIREBASE_DATABASE_URL}")
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred, {
                'databaseURL': FIREBASE_DATABASE_URL
            })
            logger.info("New Firebase app successfully initialized.")
        else:
            _firebase_app = firebase_admin.get_app()
            logger.info(f"Using existing Firebase app: {_firebase_app.name}")

        _db_instance = firebase_admin.db.reference("/")
        _firebase_initialized_successfully = True  # Mark as successfully initialized
        logger.info("Firebase Realtime Database successfully initialized and DB reference obtained.")
        return _db_instance

    except Exception as e:
        logger.error(f"Error initializing Firebase: {e}", exc_info=True)
        _db_instance = None  # Ensure instance is None on error
        _firebase_initialized_successfully = False
        return None

# Utility function to check if we can use Firebase
def can_use_firebase():
    global _firebase_initialized_successfully
    """Check if we can use Firebase or need to fallback to SQLite"""
    logger.debug("can_use_firebase called.")
    if not _firebase_initialized_successfully:
        logger.warning("Firebase not successfully initialized (according to flag). Firebase not usable.")
        return False
        
    if not FIREBASE_DATABASE_URL:
        logger.warning("FIREBASE_DATABASE_URL not set. Firebase not usable.")
        return False
        
    db_ref_check = initialize_firebase_db()
    if not db_ref_check:
        logger.warning("initialize_firebase_db() did not return an instance. Firebase not usable.")
        _firebase_initialized_successfully = False
        return False
            
    try:
        test_ref = db_ref_check.child(".info/connected")
        connected_status = test_ref.get()
        logger.info(f"Firebase connection test: .info/connected = {connected_status}")
        if connected_status:
            logger.debug("Firebase is usable.")
            return True
        else:
            logger.warning("Firebase .info/connected is false. Firebase may not be usable.")
            _firebase_initialized_successfully = False
            return False
    except Exception as e:
        logger.error(f"Firebase access error during can_use_firebase test: {e}. Firebase not usable.", exc_info=True)
        _firebase_initialized_successfully = False
        return False

# Chat Room Operations
def get_user_chats(user_id):
    """Get all chats the user participates in"""
    logger.info(f"Firebase: get_user_chats for user ID: {user_id}")
    if not can_use_firebase():
        logger.warning("Firebase not usable in get_user_chats. Falling back to SQLite.")
        import chat_db_handler
        return chat_db_handler.get_user_chats(user_id)
    
    db_ref = initialize_firebase_db()
    if not db_ref:
        logger.error("Firebase DB not initialized in get_user_chats.")
        return []

    try:
        logger.debug(f"Firebase: Fetching chat participations for user {user_id}.")
        participants_ref = db_ref.child("chat_participants")
        all_participants_data = participants_ref.get() or {}
        logger.debug(f"Firebase: Raw data of all chat participants (truncated): {str(all_participants_data)[:500] if all_participants_data else '{}'}")
        
        result = []
        user_id_str = str(user_id)
        
        if isinstance(all_participants_data, dict):
            for chat_id_fb, participants_in_chat in all_participants_data.items():
                logger.debug(f"Firebase: Checking chat {chat_id_fb}, participants: {participants_in_chat}")
                
                is_participant_fb = False
                if isinstance(participants_in_chat, dict) and user_id_str in participants_in_chat:
                    is_participant_fb = True
                
                if is_participant_fb:
                    logger.info(f"Firebase: User {user_id_str} is a participant in chat {chat_id_fb}.")
                    chat_detail_ref = db_ref.child(f"chats/{chat_id_fb}")
                    chat_data_fb = chat_detail_ref.get() or {}
                    logger.debug(f"Firebase: Chat details for {chat_id_fb}: {chat_data_fb}")
                    
                    messages_for_chat_ref = db_ref.child(f"messages/{chat_id_fb}")
                    last_message_text = "No messages"
                    last_activity_formatted = "Unknown"
                    
                    try:
                        messages_query = messages_for_chat_ref.order_by_child("sent_at").limit_to_last(1)
                        last_messages_data = messages_query.get()
                        if last_messages_data and isinstance(last_messages_data, dict):
                            last_msg_obj = next(iter(last_messages_data.values()), None)
                            if last_msg_obj and isinstance(last_msg_obj, dict):
                                last_message_text = last_msg_obj.get("message_text", "Message without text")
                                sent_at_ms = last_msg_obj.get("sent_at")
                                if sent_at_ms:
                                    dt_object = datetime.fromtimestamp(sent_at_ms / 1000)
                                    last_activity_formatted = dt_object.strftime('%d.%m.%y %H:%M')
                        logger.debug(f"Firebase: Last message for chat {chat_id_fb}: '{last_message_text[:30]}...'")
                    except Exception as e_last_msg:
                        logger.warning(f"Firebase: Error fetching last message for chat {chat_id_fb}: {e_last_msg}. Using default values.")

                    chat_info_entry = {
                        "id": chat_id_fb,
                        "name": chat_data_fb.get("name", "Unnamed Chat") if isinstance(chat_data_fb, dict) else "Unnamed Chat",
                        "last_message": last_message_text,
                        "last_activity": last_activity_formatted
                    }
                    result.append(chat_info_entry)
        
        logger.info(f"Firebase: Compiled {len(result)} chats for user {user_id_str}.")
        return result
    except Exception as e:
        logger.error(f"Firebase: Error fetching user chats for {user_id}: {e}", exc_info=True)
        return []

# Other functions remain unchanged
