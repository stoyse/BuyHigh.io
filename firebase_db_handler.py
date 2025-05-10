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

# Firebase configuration
FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')
if not FIREBASE_DATABASE_URL:
    logger.error("FIREBASE_DATABASE_URL environment variable not set")
    raise ValueError("FIREBASE_DATABASE_URL must be set in the environment variables")
MAX_RETRIES = 3

# Global variables for Firebase instances
_firebase_app = None
_db_instance = None

# Initialize Firebase Realtime Database
def initialize_firebase_db():
    """Initialize Firebase Realtime Database connection"""
    global _firebase_app, _db_instance

    if _db_instance:
        return _db_instance

    try:
        use_firebase = os.getenv("USE_FIREBASE", "false").lower() == "true"
        if not use_firebase:
            logger.warning("Firebase is disabled in configuration.")
            return None

        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not cred_path:
            logger.error("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
            return None

        if not os.path.exists(cred_path):
            logger.error(f"Firebase credentials file not found: {cred_path}")
            return None

        # Prüfe, ob schon eine App existiert
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred, {
                'databaseURL': FIREBASE_DATABASE_URL
            })
        else:
            _firebase_app = firebase_admin.get_app()

        _db_instance = firebase_admin.db.reference("/")
        logger.info("Firebase Realtime Database initialized successfully")
        return _db_instance

    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return None

# Utility function to check if we can use Firebase
def can_use_firebase():
    """Check if we can use Firebase or need to fallback to SQLite"""
    if not FIREBASE_DATABASE_URL:
        logger.warning("FIREBASE_DATABASE_URL not set. Using SQLite fallback.")
        return False
        
    try:
        # Try to access Firebase to see if it's working
        db_ref = initialize_firebase_db()
        if not db_ref:
            return False
            
        ref = db_ref.child("test")
        ref.get()
        return True
    except Exception as e:
        logger.error(f"Firebase access error: {e}. Using SQLite fallback.")
        return False

# Helper for Firebase quota errors handling
def handle_firebase_operation(operation_func, *args, **kwargs):
    """Execute Firebase operation with retry and fallback to SQLite on quota error"""
    for attempt in range(MAX_RETRIES):
        try:
            return operation_func(*args, **kwargs), True  # Return result and success flag
        except Exception as e:
            error_str = str(e).lower()
            if "quota" in error_str or "too many requests" in error_str:
                logger.warning(f"Firebase quota reached. Switching to SQLite fallback.")
                return None, False  # Return None and failure flag
            elif attempt < MAX_RETRIES - 1:
                logger.warning(f"Firebase operation failed. Retrying {attempt+1}/{MAX_RETRIES}. Error: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Firebase operation failed after {MAX_RETRIES} attempts: {e}")
                return None, False  # Return None and failure flag
    return None, False

# Chat Room Operations
def get_user_chats(user_id):
    """Get all chats the user participates in"""
    if not can_use_firebase():
        import chat_db_handler
        return chat_db_handler.get_user_chats(user_id)
    
    try:
        # Debug Logging hinzufügen
        logger.info(f"Getting chats for user_id: {user_id} (type: {type(user_id)})")
        
        # Get all chat participants
        participants_ref = db.reference("/chat_participants")
        chats_data = participants_ref.get() or {}
        logger.info(f"Raw chat participants data from Firebase: {chats_data}")
        
        result = []
        user_id_str = str(user_id)  # Konvertiere zu String für den Vergleich
        
        if isinstance(chats_data, dict):
            # Für jedes Chat-ID
            for chat_id, participants in chats_data.items():
                logger.info(f"Checking chat {chat_id}, participants: {participants}")
                
                # Überprüfen, ob der Benutzer ein Teilnehmer ist
                is_participant = False
                if isinstance(participants, dict) and user_id_str in participants:
                    is_participant = True
                
                if is_participant:
                    # Chat-Daten abrufen
                    chat_ref = db.reference(f"/chats/{chat_id}")
                    chat_data = chat_ref.get() or {}
                    
                    # Letzte Nachricht abrufen
                    messages_ref = db.reference(f"/messages/{chat_id}")
                    try:
                        messages = messages_ref.order_by_child("sent_at").limit_to_last(1).get() or {}
                    except Exception as e:
                        logger.warning(f"Could not order by sent_at, using unsorted fetch: {e}")
                        messages = messages_ref.get() or {}
                    
                    chat_info = {
                        "id": chat_id,
                        "name": chat_data.get("name", "Unbenannt") if isinstance(chat_data, dict) else "Unbenannt",
                        "last_message": "",
                        "last_activity": None
                    }
                    
                    # Letzte Nachricht verarbeiten
                    if isinstance(messages, dict) and messages:
                        last_msg_key = max(messages.keys(), key=lambda k: messages[k].get("sent_at", 0))
                        last_msg = messages[last_msg_key]
                        chat_info["last_message"] = last_msg.get("message_text", "")
                        
                        # Zeit formatieren
                        sent_timestamp = last_msg.get("sent_at", 0) / 1000  # Convert from milliseconds
                        now = time.time()
                        delta = now - sent_timestamp
                        
                        if delta > 86400:  # > 1 day
                            chat_info["last_activity"] = f"vor {int(delta // 86400)} Tag(en)"
                        elif delta > 3600:  # > 1 hour
                            chat_info["last_activity"] = f"vor {int(delta // 3600)} Std"
                        elif delta > 60:  # > 1 minute
                            chat_info["last_activity"] = f"vor {int(delta // 60)} Min"
                        else:
                            chat_info["last_activity"] = "gerade eben"
                    
                    result.append(chat_info)
        
        logger.info(f"Returning {len(result)} chats for user {user_id}")
        return result
    except Exception as e:
        logger.error(f"Error getting user chats from Firebase: {e}", exc_info=True)
        import chat_db_handler
        return chat_db_handler.get_user_chats(user_id)

# Helper function to process chat details
def process_chat_details(chat_id, chat_data, messages):
    """Process chat data and format for display"""
    # Format last message info
    last_message = ""
    last_activity = None
    
    if messages:
        if isinstance(messages, dict):
            # Get the first message from dictionary
            last_msg = next(iter(messages.values()), {})
        elif isinstance(messages, list):
            # Get the last message from list (should be only one due to limit_to_last(1))
            last_msg = messages[-1] if messages else {}
        else:
            last_msg = {}
            
        last_message = last_msg.get("message_text", "")
        
        # Format timestamp for display
        if "sent_at" in last_msg:
            sent_timestamp = last_msg.get("sent_at", 0) / 1000  # Convert from milliseconds
            now = time.time()
            delta = now - sent_timestamp
            
            if delta > 86400:  # > 1 day
                last_activity = f"vor {int(delta // 86400)} Tag(en)"
            elif delta > 3600:  # > 1 hour
                last_activity = f"vor {int(delta // 3600)} Std"
            elif delta > 60:  # > 1 minute
                last_activity = f"vor {int(delta // 60)} Min"
            else:
                last_activity = "gerade eben"
    
    # Return formatted chat info
    return {
        "id": chat_id,
        "name": chat_data.get("name", "Unbenannt") if isinstance(chat_data, dict) else "Unbenannt",
        "last_message": last_message,
        "last_activity": last_activity
    }

def get_chat_by_id(chat_id):
    """Get chat details by ID"""
    if not can_use_firebase():
        import chat_db_handler
        return chat_db_handler.get_chat_by_id(chat_id)
    
    try:
        logger.info(f"Retrieving chat with ID {chat_id} from Firebase")
        chat_ref = db.reference(f"/chats/{chat_id}")
        chat_data = chat_ref.get()
        
        if not chat_data:
            logger.warning(f"Chat with ID {chat_id} not found in Firebase")
            
            # Try to debug by listing all chats
            try:
                all_chats_ref = db.reference("/chats")
                all_chats = all_chats_ref.get() or {}
                logger.info(f"Available chats in Firebase: {all_chats.keys() if isinstance(all_chats, dict) else 'not a dict'}")
            except Exception as e:
                logger.error(f"Failed to list all chats: {e}")
            
            return None
        
        logger.info(f"Found chat in Firebase: {chat_data}")
        chat_info = {
            "id": chat_id,
            "name": chat_data.get("name", "Unbenannter Chat"),
            "created_at": chat_data.get("created_at", ""),
            "created_by": chat_data.get("created_by", None),
            "members_can_invite": chat_data.get("members_can_invite", False)
        }
        logger.info(f"Formatted chat info: {chat_info}")
        return chat_info
    except Exception as e:
        logger.error(f"Error getting chat by ID from Firebase: {e}", exc_info=True)
        import chat_db_handler
        return chat_db_handler.get_chat_by_id(chat_id)

def create_chat(chat_name, user_id):
    """Create a new chat room"""
    if not can_use_firebase():
        import chat_db_handler
        return chat_db_handler.create_chat(chat_name, user_id)
    
    try:
        # Generate a new reference for the chat
        chats_ref = db.reference("/chats")
        new_chat_ref = chats_ref.push()
        chat_id = new_chat_ref.key
        
        # Current timestamp in milliseconds
        current_time = int(time.time() * 1000)
        
        # Set chat data
        new_chat_ref.set({
            "name": chat_name,
            "created_at": current_time,
            "created_by": str(user_id), # Sicherstellen, dass user_id als String gespeichert wird
            "members_can_invite": False
        })
        
        # Add creator as participant - mit robuster Fehlerbehandlung
        creator_username = "User"  # Default username
        try:
            # Import kann fehlschlagen - umschließe mit try/except
            from db_handler import get_user_by_firebase_uid, get_user_by_id  # Beide möglichen Funktionen probieren
            
            # Versuche beide Funktionen, falls verfügbar
            if 'get_user_by_id' in locals():
                user = get_user_by_id(user_id)
                if user and "username" in user:
                    creator_username = user.get("username")
            elif 'get_user_by_firebase_uid' in locals():
                user = get_user_by_firebase_uid(user_id)
                if user and "username" in user:
                    creator_username = user.get("username")
        except ImportError:
            logger.warning(f"Could not import user retrieval functions from db_handler. Using default username.")
        except Exception as e:
            logger.warning(f"Error getting username for user {user_id}: {e}")
        
        participant_ref = db.reference(f"/chat_participants/{chat_id}/{str(user_id)}") # Pfad auch mit String user_id
        participant_ref.set({
            "chat_name": creator_username,  # Store the user's name, not the chat room's name
            "joined_at": current_time
        })
        
        return chat_id
    except Exception as e:
        logger.error(f"Error creating chat in Firebase: {e}", exc_info=True)
        import chat_db_handler
        return chat_db_handler.create_chat(chat_name, user_id)

def is_chat_participant(chat_id, user_id):
    """Check if user is a participant in the chat"""
    if not can_use_firebase():
        import chat_db_handler
        return chat_db_handler.is_chat_participant(chat_id, user_id)
    
    try:
        # Wichtig: IDs zu Strings konvertieren für Firebase
        chat_id_str = str(chat_id)
        user_id_str = str(user_id)
        
        # Direkte Anfrage an die Firebase-Datenbank
        participant_ref = db.reference(f"/chat_participants/{chat_id_str}/{user_id_str}")
        participant_data = participant_ref.get()
        
        logger.debug(f"Checking if user {user_id_str} is participant in chat {chat_id_str}: {participant_data is not None}")
        
        return participant_data is not None
    except Exception as e:
        logger.error(f"Error checking chat participant in Firebase: {e}", exc_info=True)
        import chat_db_handler
        return chat_db_handler.is_chat_participant(chat_id, user_id)

def join_chat(chat_id, user_id):
    """Add user to a chat"""
    if not can_use_firebase():
        import chat_db_handler
        return chat_db_handler.join_chat(chat_id, user_id)
    
    try:
        # Wichtig: IDs zu Strings konvertieren für Firebase
        chat_id_str = str(chat_id)
        user_id_str = str(user_id)
        
        # Check if already a participant
        if is_chat_participant(chat_id_str, user_id_str):
            logger.info(f"User {user_id_str} is already participant in chat {chat_id_str}")
            return True
        
        # Get username
        username = "User"  # Default username
        try:
            import db_handler
            user = db_handler.get_user_by_id(user_id)
            if user and "username" in user:
                username = user["username"]
                logger.info(f"Found username '{username}' for user {user_id_str}")
        except Exception as e:
            logger.warning(f"Error getting username for user {user_id_str}: {e}")
        
        # Add to participants
        participant_ref = db.reference(f"/chat_participants/{chat_id_str}/{user_id_str}")
        participant_data = {
            "chat_name": username,
            "joined_at": int(time.time() * 1000)
        }
        
        logger.info(f"Adding user {user_id_str} as participant to chat {chat_id_str} with data: {participant_data}")
        participant_ref.set(participant_data)
        
        # Überprüfe, ob der Eintrag wirklich erstellt wurde
        verification = participant_ref.get()
        if verification:
            logger.info(f"Successfully added user {user_id_str} to chat {chat_id_str}")
            return True
        else:
            logger.error(f"Failed to verify participant data for user {user_id_str} in chat {chat_id_str}")
            return False
    except Exception as e:
        logger.error(f"Error joining chat in Firebase: {e}", exc_info=True)
        import chat_db_handler
        return chat_db_handler.join_chat(chat_id, user_id)

def get_chat_messages(chat_id, limit=50, offset=0):
    """Get messages for a chat"""
    if not can_use_firebase():
        import chat_db_handler
        return chat_db_handler.get_chat_messages(chat_id, limit, offset)
    
    try:
        # Versuche erst mit orderBy (erfordert Index in Firebase-Regeln)
        messages_ref = db.reference(f"/messages/{chat_id}")
        try:
            query = messages_ref.order_by_child("sent_at").limit_to_last(limit + offset)
            messages_data = query.get() or {}
        except Exception as index_error:
            if "Index not defined" in str(index_error):
                logger.warning(f"Firebase Index fehlt für sent_at. Hole Daten ohne Sortierung.")
                # Fallback: Ohne orderBy, hole alle Nachrichten und sortiere clientseitig
                messages_data = messages_ref.get() or {}
            else:
                raise  # Andere Fehler weiterleiten
        
        # Process messages
        messages = []
        
        # Handle different data types from Firebase
        if isinstance(messages_data, dict):
            # Process dictionary messages
            for msg_id, msg in messages_data.items():
                if not isinstance(msg, dict):
                    continue
                    
                # Get username with robust error handling
                username = "Unknown"
                try:
                    from db_handler import get_user_by_id, get_user_by_firebase_uid
                    if 'get_user_by_id' in locals():
                        user = get_user_by_id(msg.get("user_id"))
                        if user and "username" in user:
                            username = user.get("username")
                except ImportError:
                    pass
                except Exception:
                    pass
                
                # Format sent_at as ISO string
                sent_at_ms = msg.get("sent_at", 0)
                sent_at = datetime.fromtimestamp(sent_at_ms / 1000).isoformat() + "Z"
                
                messages.append({
                    "id": msg_id,
                    "user_id": msg.get("user_id"),
                    "username": username,
                    "message_text": msg.get("message_text", ""),
                    "sent_at": sent_at,
                    "_timestamp": sent_at_ms  # Für die Sortierung
                })
        
        # Sortiere nach Zeitstempel (aufsteigend)
        messages.sort(key=lambda m: m.get("_timestamp", 0))
        
        # Anwenden von limit und offset clientseitig
        if offset > 0:
            messages = messages[offset:]
        if len(messages) > limit:
            messages = messages[:limit]
            
        # Entferne temporäres Sortierfeld
        for msg in messages:
            if "_timestamp" in msg:
                del msg["_timestamp"]
        
        return messages
    except Exception as e:
        logger.error(f"Error getting chat messages from Firebase: {e}", exc_info=True)
        import chat_db_handler
        return chat_db_handler.get_chat_messages(chat_id, limit, offset)

def add_message_and_get_details(chat_id, user_id, message_text):
    """Add a message to a chat and return message details"""
    if not can_use_firebase():
        import chat_db_handler
        return chat_db_handler.add_message_and_get_details(chat_id, user_id, message_text)
    
    try:
        # Wichtig: IDs zu Strings konvertieren für Firebase
        chat_id_str = str(chat_id)
        user_id_str = str(user_id) # Wird bereits korrekt als String verwendet
        
        logger.info(f"Adding message to Firebase chat {chat_id_str} from user {user_id_str}: {message_text[:50]}...")
        
        # Get username with robust error handling
        username = "Unknown"
        try:
            import db_handler
            user = db_handler.get_user_by_id(user_id)
            if user and "username" in user:
                username = user.get("username")
        except Exception as e:
            logger.warning(f"Error getting username for user {user_id}: {e}")
        
        # Current timestamp in milliseconds
        current_time_ms = int(time.time() * 1000)
        
        # Überprüfen, ob der Chat existiert, falls nicht, einen erstellen
        chat_ref = db.reference(f"/chats/{chat_id_str}")
        chat_data = chat_ref.get()
        if not chat_data:
            # Erstelle einen neuen Chat
            logger.warning(f"Chat {chat_id_str} does not exist, creating it")
            chat_ref.set({
                "name": f"Chat {chat_id_str}",
                "created_at": current_time_ms,
                "created_by": user_id_str # Sicherstellen, dass user_id als String gespeichert wird
            })
        
        # Stelle sicher, dass der Benutzer ein Teilnehmer ist
        participant_ref = db.reference(f"/chat_participants/{chat_id_str}/{user_id_str}")
        participant_data = participant_ref.get()
        if not participant_data:
            # Füge den Benutzer als Teilnehmer hinzu
            logger.info(f"User {user_id_str} is not a participant of chat {chat_id_str}, adding")
            participant_ref.set({
                "chat_name": username,
                "joined_at": current_time_ms
            })
        
        # Add message to the correct path in Firebase
        messages_ref = db.reference(f"/messages/{chat_id_str}")
        new_message_ref = messages_ref.push()
        message_id = new_message_ref.key
        
        message_data = {
            "user_id": user_id_str,  # Bereits korrekt als String
            "message_text": message_text,
            "sent_at": current_time_ms
        }
        
        logger.debug(f"Pushing message to Firebase: {message_data}")
        new_message_ref.set(message_data)
        
        # Verify the message was saved
        saved_data = new_message_ref.get()
        if not saved_data:
            logger.error(f"Failed to save message to Firebase")
            raise Exception("Message not saved to Firebase")
        
        # Format sent_at as ISO string for frontend consistency
        sent_at = datetime.fromtimestamp(current_time_ms / 1000).isoformat() + "Z"
        
        # Return message details
        result = {
            "id": message_id,
            "chat_room_id": chat_id_str,
            "user_id": user_id_str,
            "username": username,
            "message_text": message_text,
            "sent_at": sent_at
        }
        logger.info(f"Message successfully saved, returning: {result}")
        return result
    except Exception as e:
        logger.error(f"Error adding message to Firebase: {e}", exc_info=True)
        import chat_db_handler
        return chat_db_handler.add_message_and_get_details(chat_id, user_id, message_text)

def delete_chat(chat_id):
    """Delete a chat room and all its messages"""
    if not can_use_firebase():
        import chat_db_handler
        return chat_db_handler.delete_chat(chat_id)
    
    try:
        # Delete messages first
        messages_ref = db.reference(f"/messages/{chat_id}")
        messages_ref.delete()
        
        # Delete participants
        participants_ref = db.reference(f"/chat_participants/{chat_id}")
        participants_ref.delete()
        
        # Delete chat room
        chat_ref = db.reference(f"/chats/{chat_id}")
        chat_ref.delete()
        
        return True
    except Exception as e:
        logger.error(f"Error deleting chat in Firebase: {e}")
        import chat_db_handler
        return chat_db_handler.delete_chat(chat_id)

def ensure_user_in_default_chat(user_id):
    """Make sure a user is in the default General chat.
    Finds the 'General' chat and ensures the user is a participant.
    This function will NO LONGER create the 'General' chat if it's not found.
    Creation should be handled by setup_initial_firebase_chat_structure.
    """
    logger.debug(f"ensure_user_in_default_chat: Called for user_id: {user_id}")
    if not can_use_firebase():
        logger.warning("ensure_user_in_default_chat: Firebase not usable, falling back to chat_db_handler.")
        import chat_db_handler
        return chat_db_handler.ensure_user_in_default_chat(user_id)

    db_ref = initialize_firebase_db()
    if not db_ref:
        logger.error("ensure_user_in_default_chat: Failed to initialize Firebase DB. Aborting.")
        return False
    
    try:
        user_id_str = str(user_id) # Ensure user_id is string for consistency
        logger.debug(f"ensure_user_in_default_chat: User ID (string): {user_id_str}")

        # 1. Find the 'General' chat ID using the dedicated function
        logger.debug("ensure_user_in_default_chat: Calling get_default_chat_id().")
        default_chat_id = get_default_chat_id()
        logger.debug(f"ensure_user_in_default_chat: get_default_chat_id() returned: {default_chat_id} (type: {type(default_chat_id)})")

        # 2. If 'General' chat doesn't exist, log an error and return False.
        #    This function will no longer create the 'General' chat.
        if not default_chat_id:
            logger.error(f"ensure_user_in_default_chat: 'General' chat not found (get_default_chat_id returned None). Cannot ensure participation for user {user_id_str}. The 'General' chat might be missing. Consider running 'python manage.py reset-firebase-chat'.")
            return False # Indicate that the operation could not be completed as the default chat is missing.

        logger.info(f"ensure_user_in_default_chat: Found existing 'General' chat with ID: {default_chat_id}.")

        # 3. Ensure user is a participant in the 'General' chat
        if not is_chat_participant(default_chat_id, user_id_str):
            logger.info(f"ensure_user_in_default_chat: User {user_id_str} not in 'General' chat ({default_chat_id}). Adding participant.")
            join_success = join_chat(default_chat_id, user_id_str)
            if not join_success:
                logger.error(f"ensure_user_in_default_chat: Failed to add user {user_id_str} to 'General' chat {default_chat_id}.")
                return False
            logger.info(f"ensure_user_in_default_chat: Successfully added user {user_id_str} to 'General' chat {default_chat_id}.")
        else:
            logger.info(f"ensure_user_in_default_chat: User {user_id_str} is already a participant in 'General' chat {default_chat_id}.")
            
        return True # User is in General chat
        
    except Exception as e:
        logger.error(f"Error ensuring user in default chat in Firebase: {e}")
        # Fallback to SQLite if Firebase operation fails critically
        import chat_db_handler
        return chat_db_handler.ensure_user_in_default_chat(user_id)

def get_default_chat_id():
    """Find the ID of the default General chat"""
    logger.debug("get_default_chat_id: Attempting to find 'General' chat ID.")
    if not can_use_firebase():
        logger.warning("get_default_chat_id: Firebase not usable, falling back to chat_db_handler.")
        import chat_db_handler
        # Ensure the fallback also has a similar function or returns None
        return chat_db_handler.get_default_chat_id() if hasattr(chat_db_handler, 'get_default_chat_id') else None
    
    db_ref = initialize_firebase_db()
    if not db_ref:
        logger.error("get_default_chat_id: Failed to initialize Firebase DB.")
        return None

    try:
        # NEUE STRATEGIE: Direkt die bekannte Chat-ID prüfen
        known_general_chat_id = "-OPvLBJqVopKLHfHGPFF"  # ID des bereits bekannten "General"-Chats
        logger.info(f"get_default_chat_id: Directly checking known General chat ID: {known_general_chat_id}")
        
        # Prüfen, ob dieser Chat existiert
        known_chat_ref = db_ref.child(f"chats/{known_general_chat_id}")
        known_chat_data = known_chat_ref.get()
        
        if known_chat_data:
            logger.info(f"get_default_chat_id: Successfully found known General chat with ID: {known_general_chat_id}")
            return known_general_chat_id
        else:
            logger.warning(f"get_default_chat_id: Known General chat ID {known_general_chat_id} does not exist anymore.")
        
        # VERBESSERT: Direkte einfache Abfrage aller Chats als Fallback
        chats_ref = db_ref.child("chats")
        chats_data = chats_ref.get() or {}
        
        # Debug-Log für die gefundenen Daten
        logger.info(f"get_default_chat_id: Found {len(chats_data) if isinstance(chats_data, dict) else '0'} chats")
        
        # VEREINFACHT: Prüfung mit Fallbacks für robusten Vergleich
        if isinstance(chats_data, dict):
            # Erste Strategie: Exakten Namen "General" suchen
            for chat_id, chat_info in chats_data.items():
                if isinstance(chat_info, dict) and chat_info.get("name") == "General":
                    logger.info(f"get_default_chat_id: Found exact match 'General' with ID: {chat_id}")
                    return chat_id
            
            # Zweite Strategie: Fallback auf "general" oder Namen mit dem Wort "general" 
            for chat_id, chat_info in chats_data.items():
                name = chat_info.get("name", "") if isinstance(chat_info, dict) else ""
                if name and isinstance(name, str):
                    if name.lower() == "general":
                        logger.info(f"get_default_chat_id: Found case-insensitive 'general' with ID: {chat_id}")
                        return chat_id
            
            # Dritte Strategie: Beliebigen Chat als Fallback nehmen
            # Nur wenn genau ein Chat existiert (um Verwirrung zu vermeiden)
            if len(chats_data) == 1:
                only_chat_id = next(iter(chats_data))
                logger.info(f"get_default_chat_id: Only one chat exists, using it as default: {only_chat_id}")
                return only_chat_id
        
        logger.warning("get_default_chat_id: No 'General' chat found after all strategies.")
        return None
    except Exception as e:
        logger.error(f"Error getting default chat ID from Firebase: {e}", exc_info=True)
        return None

# Utility function to migrate data from SQLite to Firebase
def migrate_chat_data_from_sqlite_to_firebase():
    """Migrate all chat data from SQLite to Firebase"""
    logger.info("Starting chat data migration from SQLite to Firebase")
    
    if not initialize_firebase_db():
        logger.error("Failed to initialize Firebase. Migration aborted.")
        return False
    
    conn = None
    try:
        # Connect to SQLite
        conn = sqlite3.connect('/Users/julianstosse/Developer/BuyHigh.io/database/database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Migrate chat rooms
        logger.info("Migrating chat rooms...")
        cursor.execute("SELECT * FROM chat_rooms")
        chat_rooms = cursor.fetchall()
        
        chats_ref = db.reference("/chats")
        
        for chat in chat_rooms:
            chat_dict = dict(chat)
            chat_id = str(chat_dict["id"])
            
            # Convert timestamps
            created_at_str_val = chat_dict.get("created_at")
            if created_at_str_val:
                created_at_dt = datetime.strptime(created_at_str_val, '%Y-%m-%d %H:%M:%S')
                created_at_ms = int(created_at_dt.timestamp() * 1000)
            else:
                created_at_ms = int(time.time() * 1000)
            
            created_by_val = chat_dict.get("created_by")
            
            # Set chat data in Firebase
            chat_ref = db.reference(f"/chats/{chat_id}")
            chat_ref.set({
                "name": chat_dict.get("name"),
                "created_at": created_at_ms,
                "created_by": str(created_by_val) if created_by_val is not None else None, # Konvertiere zu String
                "members_can_invite": chat_dict.get("members_can_invite", False)
            })
        
        # Migrate participants
        logger.info("Migrating chat participants...")
        cursor.execute("SELECT * FROM chat_room_participants")
        participants = cursor.fetchall()
        
        for participant in participants:
            part_dict = dict(participant)
            chat_id_str_val = str(part_dict["chat_room_id"])
            user_id_str_val = str(part_dict["user_id"]) # user_id für Pfad als String
            
            # Convert timestamp
            joined_at_str_val = part_dict.get("joined_at")
            if joined_at_str_val:
                joined_at_dt = datetime.strptime(joined_at_str_val, '%Y-%m-%d %H:%M:%S')
                joined_at_ms = int(joined_at_dt.timestamp() * 1000)
            else:
                joined_at_ms = int(time.time() * 1000)
            
            # Set participant data in Firebase
            participant_ref = db.reference(f"/chat_participants/{chat_id_str_val}/{user_id_str_val}")
            participant_ref.set({
                "chat_name": part_dict.get("chat_name"),
                "joined_at": joined_at_ms
            })
        
        # Migrate messages
        logger.info("Migrating messages...")
        cursor.execute("SELECT * FROM messages ORDER BY sent_at ASC")
        messages_data_sqlite = cursor.fetchall() # Umbenannt, um Konflikt zu vermeiden
        
        for message_sqlite in messages_data_sqlite: # Umbenannt
            msg_dict = dict(message_sqlite) # Umbenannt
            chat_id_str_val = str(msg_dict["chat_room_id"])
            user_id_val = msg_dict.get("user_id")
            
            # Convert timestamp
            sent_at_str_val = msg_dict.get("sent_at")
            if sent_at_str_val:
                sent_at_dt = datetime.strptime(sent_at_str_val, '%Y-%m-%d %H:%M:%S')
                sent_at_ms = int(sent_at_dt.timestamp() * 1000)
            else:
                sent_at_ms = int(time.time() * 1000)
            
            # Add message to Firebase
            messages_ref = db.reference(f"/messages/{chat_id_str_val}")
            new_message_ref = messages_ref.push()
            new_message_ref.set({
                "user_id": str(user_id_val) if user_id_val is not None else None, # Konvertiere zu String
                "message_text": msg_dict.get("message_text"),
                "sent_at": sent_at_ms
            })
        
        logger.info("Migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_all_firebase_chat_data():
    """Deletes all chat-related data (/chats, /chat_participants, /messages) from Firebase."""
    if not can_use_firebase():
        logger.error("Firebase is not usable. Cannot delete chat data.")
        return False
    
    db_ref = initialize_firebase_db()
    if not db_ref:
        logger.error("Failed to initialize Firebase DB. Deletion aborted.")
        return False
        
    try:
        logger.info("Deleting /chats data from Firebase...")
        db_ref.child("chats").delete()
        logger.info("/chats data deleted.")
        
        logger.info("Deleting /chat_participants data from Firebase...")
        db_ref.child("chat_participants").delete()
        logger.info("/chat_participants data deleted.")
        
        logger.info("Deleting /messages data from Firebase...")
        db_ref.child("messages").delete()
        logger.info("/messages data deleted.")
        
        logger.info("All Firebase chat data successfully deleted.")
        return True
    except Exception as e:
        logger.error(f"Error deleting Firebase chat data: {e}", exc_info=True)
        return False

def setup_initial_firebase_chat_structure():
    """Creates the initial default 'General' chat room in Firebase if it doesn't exist."""
    logger.info("setup_initial_firebase_chat_structure: Setting up initial Firebase chat structure")
    if not can_use_firebase():
        logger.error("Firebase is not usable. Cannot set up initial chat structure.")
        return False

    db_ref = initialize_firebase_db()
    if not db_ref:
        logger.error("setup_initial_firebase_chat_structure: Failed to initialize Firebase DB. Setup aborted.")
        return False

    try:
        # Prüfen, ob ein "General" Chat bereits existiert
        general_chat_id = get_default_chat_id()
        
        if general_chat_id:
            logger.info(f"setup_initial_firebase_chat_structure: 'General' chat already exists with ID: {general_chat_id}")
            return general_chat_id
        
        # Wenn kein Chat gefunden wurde, erstellen wir einen neuen mit genau dem Namen "General"
        logger.info("setup_initial_firebase_chat_structure: No 'General' chat found, creating a new one...")
        
        # WICHTIG: Das ist der exakte Name, der auch in get_default_chat_id gesucht wird
        exact_name = "General"
        
        # Neuen Chat erstellen
        chats_ref = db_ref.child("chats")
        new_chat_ref = chats_ref.push()
        default_chat_id = new_chat_ref.key
        
        if not default_chat_id:
            logger.error("setup_initial_firebase_chat_structure: Failed to get ID for new chat")
            return None
            
        # Chat mit dem eindeutigen Namen erstellen
        new_chat_ref.set({
            "name": exact_name,
            "created_at": int(time.time() * 1000),
            "created_by": None,
            "members_can_invite": False
        })
        
        logger.info(f"setup_initial_firebase_chat_structure: Created new 'General' chat with ID: {default_chat_id}")
        
        # Direkte Bestätigung des erstellten Chats
        created_chat = new_chat_ref.get()
        if created_chat and created_chat.get("name") == exact_name:
            logger.info(f"setup_initial_firebase_chat_structure: Successfully verified the new chat creation with name '{exact_name}'")
        else:
            logger.error(f"setup_initial_firebase_chat_structure: Chat creation could not be verified! got: {created_chat}")
        
        return default_chat_id
    except Exception as e:
        logger.error(f"Error setting up initial Firebase chat structure: {e}")
        return None
