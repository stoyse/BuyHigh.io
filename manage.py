#!/usr/bin/env python3
"""
Management script for BuyHigh.io application.
"""
import argparse
import logging
import os
from dotenv import load_dotenv
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import firebase_db_handler for specific commands
try:
    import firebase_db_handler
except ImportError:
    firebase_db_handler = None
    logger.warning("firebase_db_handler module not found. Some commands may not be available.")

def migrate_to_firebase():
    """Migrate chat data from SQLite to Firebase."""
    logger.info("Starting migration of chat data from SQLite to Firebase...")
    
    if not firebase_db_handler:
        logger.error("firebase_db_handler module is not available. Migration cannot proceed.")
        return

    try:
        # Corrected call to the migration function
        result = firebase_db_handler.migrate_chat_data_from_sqlite_to_firebase()
        
        if result:
            logger.info("Migration completed successfully!")
        else:
            logger.error("Migration failed. Check logs for details.")
    except AttributeError:
        logger.error("Function 'migrate_chat_data_from_sqlite_to_firebase' not found in firebase_db_handler.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during migration: {e}", exc_info=True)

def check_firebase_status():
    """Check Firebase connection and status."""
    logger.info("Checking Firebase connection status...")
    
    try:
        from firebase_db_handler import initialize_firebase_db, can_use_firebase
        
        initialized = initialize_firebase_db()
        if not initialized:
            logger.error("Firebase initialization failed. Check your credentials and environment variables.")
            return
            
        can_use = can_use_firebase()
        if can_use:
            logger.info("✅ Firebase connection successful. System can use Firebase Realtime Database.")
        else:
            logger.warning("⚠️ Firebase connection failed. System will use SQLite fallback.")
            logger.info("Please check your Firebase configuration and network connection.")
    except ImportError:
        logger.error("Could not import Firebase modules. Make sure firebase_db_handler.py exists.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while checking Firebase: {e}")

def setup_database():
    """Initialize the database schema for both SQLite and Firebase."""
    logger.info("Setting up databases...")
    
    # Setup SQLite database
    logger.info("Setting up SQLite database...")
    try:
        import db_handler
        db_handler.init_db()
        logger.info("SQLite database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing SQLite database: {e}")
    
    # Setup Firebase database structure (if enabled)
    logger.info("Setting up Firebase database structure (if enabled)...")
    try:
        firebase_enabled = os.environ.get('USE_FIREBASE', 'true').lower() == 'true'
        if firebase_enabled:
            from firebase_db_handler import initialize_firebase_db
            if initialize_firebase_db():
                logger.info("Firebase database connection initialized successfully.")
            else:
                logger.warning("Firebase database initialization failed. Will use SQLite fallback.")
    except ImportError:
        logger.warning("Firebase modules not available. Skipping Firebase setup.")
    except Exception as e:
        logger.error(f"Error setting up Firebase database: {e}")

def _reset_firebase_chat_data_interactive():
    """Handles the interactive Firebase chat data reset."""
    if not firebase_db_handler:
        logger.error("firebase_db_handler module is not available. Reset cannot proceed.")
        return

    logger.warning("This will delete ALL chat rooms, participants, and messages from Firebase.")
    confirm = input("Are you sure you want to proceed? (yes/no): ")
    if confirm.lower() != 'yes':
        logger.info("Firebase chat data reset aborted by user.")
        return

    logger.info("Proceeding with Firebase chat data deletion...")
    deleted = firebase_db_handler.delete_all_firebase_chat_data()
    if not deleted:
        logger.error("Failed to delete all Firebase chat data. Aborting further setup.")
        return
    
    logger.info("Setting up initial Firebase chat structure (General chat)...")
    general_chat_id = firebase_db_handler.setup_initial_firebase_chat_structure()
    if general_chat_id:
        logger.info(f"Initial Firebase chat structure set up. 'General' chat ID: {general_chat_id}")
    else:
        logger.error("Failed to set up initial Firebase chat structure.")
    
    logger.info("Firebase chat data reset and setup process finished.")
    logger.info("You might want to run the migration if you wish to repopulate from SQLite: ./manage.py migrate")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="BuyHigh.io Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute", required=True)
    
    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Migrate chat data from SQLite to Firebase")
    
    # Check status command
    status_parser = subparsers.add_parser("status", help="Check Firebase connection status")
    
    # Setup database command
    setup_parser = subparsers.add_parser("setup", help="Initialize database schema (SQLite and basic Firebase structure)")

    # Reset Firebase chat data command
    reset_chat_parser = subparsers.add_parser("reset-firebase-chat", help="Delete all chat data from Firebase and set up a default 'General' chat.")
    
    args = parser.parse_args()
    
    if args.command == "migrate":
        migrate_to_firebase()
    elif args.command == "status":
        check_firebase_status()
    elif args.command == "setup":
        setup_database()
    elif args.command == "reset-firebase-chat":
        _reset_firebase_chat_data_interactive()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
