import sqlite3
import os
from datetime import datetime

DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'database.db')  # Geändert zu database.db

if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _parse_user_timestamps(user_row):
    if user_row is None:
        return None
    
    user_data = dict(user_row)  # Convert to dict for easier manipulation

    # Ensure firebase_uid is included if it exists in the row
    # No specific parsing needed for firebase_uid itself, just ensure it's part of user_data

    for key in ['created_at', 'last_login']:
        timestamp_str = user_data.get(key)
        if timestamp_str and isinstance(timestamp_str, str):
            try:
                # Try parsing with microseconds
                user_data[key] = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                try:
                    # Try parsing without microseconds
                    user_data[key] = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # If parsing fails, keep as string or set to None or log error
                    print(f"Warning: Could not parse timestamp string '{timestamp_str}' for key '{key}'")
                    pass  # Keep original string if both parsing attempts fail
    return user_data

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT, -- Made optional as Firebase handles passwords
        firebase_uid TEXT UNIQUE, -- New column for Firebase User ID
        firebase_provider TEXT DEFAULT 'password', -- Authentifizierungsanbieter ('password', 'google', etc.)
        balance REAL DEFAULT 10000.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        mood_pet TEXT DEFAULT 'bull',
        pet_energy INTEGER DEFAULT 100,
        is_meme_mode BOOLEAN DEFAULT 0,
        email_verified BOOLEAN DEFAULT 0,
        theme TEXT DEFAULT 'light',
        total_trades INTEGER DEFAULT 0,
        profit_loss REAL DEFAULT 0.0
    )
    """)
    
    # Überprüfen, ob die firebase_provider-Spalte für bestehende Benutzer hinzugefügt werden muss
    try:
        cursor.execute("SELECT firebase_provider FROM users LIMIT 1")
    except sqlite3.OperationalError:
        # Spalte existiert nicht, also hinzufügen
        cursor.execute("ALTER TABLE users ADD COLUMN firebase_provider TEXT DEFAULT 'password'")
        print("firebase_provider Spalte zu bestehender users-Tabelle hinzugefügt")
    
    conn.commit()
    conn.close()
    print("Database initialized with users, asset_types, transactions, and chat_room_participants tables.")

def add_user(username, email, firebase_uid, provider='password'):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, firebase_uid, firebase_provider) VALUES (?, ?, ?, ?)",
            (username, email, firebase_uid, provider)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding user to database: {e}")
        return False
    finally:
        conn.close()

def get_user_by_firebase_uid(firebase_uid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE firebase_uid = ?", (firebase_uid,))
    user = cursor.fetchone()
    conn.close()
    return _parse_user_timestamps(user) if user else None

def update_last_login(user_id):
    """Updates the last_login timestamp for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating last login timestamp: {e}")
        return False
    finally:
        conn.close()
