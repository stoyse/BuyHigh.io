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
        password_hash TEXT NOT NULL,
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
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asset_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        asset_type_id INTEGER NOT NULL,
        asset_symbol TEXT NOT NULL,
        quantity REAL NOT NULL,
        price_per_unit REAL NOT NULL,
        transaction_type TEXT NOT NULL CHECK(transaction_type IN ('buy', 'sell')),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (asset_type_id) REFERENCES asset_types(id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_room_participants (
        chat_room_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        PRIMARY KEY (chat_room_id, user_id),
        FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)
    
    conn.commit()
    conn.close()
    print("Database initialized with users, asset_types, transactions, and chat_room_participants tables.")

def add_user(username, email, password_hash):
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash),
        )
        conn.commit()
        user_id = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if user_id:
            user_id = user_id[0]  # Extract the actual ID value
            DEFAULT_CHAT_ROOM_ID = int(1)
            # Check if the chat_room_participants entry already exists
            existing_entry = conn.execute(
                "SELECT 1 FROM chat_room_participants WHERE chat_room_id = ? AND user_id = ? AND chat_name = ?",
                (DEFAULT_CHAT_ROOM_ID, user_id, "General"),
            ).fetchone()
            if not existing_entry:
                conn.execute(
                    "INSERT INTO chat_room_participants (chat_room_id, user_id, chat_name) VALUES (?, ?, ?)",
                    (DEFAULT_CHAT_ROOM_ID, user_id, "General"),
                )
                conn.commit()
            else:
                return False  # Entry already exists
    except sqlite3.IntegrityError:
        return False  # Username or email already exists
    finally:
        conn.close()
    return True

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return _parse_user_timestamps(user)

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return _parse_user_timestamps(user)

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return _parse_user_timestamps(user)

def update_last_login(user_id):
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET last_login = ? WHERE id = ?", (datetime.utcnow(), user_id)
    )
    conn.commit()
    conn.close()

def update_user_theme(user_id, theme):
    """Updates the theme for a given user."""
    conn = get_db_connection()
    try:
        conn.execute("UPDATE users SET theme = ? WHERE id = ?", (theme, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error updating theme: {e}")
        return False
    finally:
        conn.close()

def update_user_password(user_id, new_password_hash):
    """Updates the password hash for a given user."""
    conn = get_db_connection()
    try:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error updating password: {e}")
        return False
    finally:
        conn.close()

def delete_user(user_id):
    """Deletes a user and all their associated data."""
    conn = get_db_connection()
    try:
        conn.execute("BEGIN TRANSACTION")
        # Delete associated transactions first due to potential FK constraints
        conn.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        
        # Delete the user
        cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        return cursor.rowcount > 0  # Returns True if a row was deleted
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        print(f"Database error deleting user: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_chat_room(chat_id):
    conn = get_db_connection()
    chat = conn.execute("SELECT * FROM chat_rooms WHERE id = ?", (chat_id,)).fetchone()
    conn.close()
    return chat

def get_chat_members(chat_id):
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT u.id, u.username FROM chat_room_participants crp
        JOIN users u ON crp.user_id = u.id
        WHERE crp.chat_room_id = ?
    """, (chat_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_chat_member(chat_id, user_id):
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO chat_room_participants (chat_room_id, user_id, chat_name) VALUES (?, ?, ?)",
            (chat_id, user_id, "General"),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding chat member: {e}")
        return False
    finally:
        conn.close()

def remove_chat_member(chat_id, user_id):
    conn = get_db_connection()
    try:
        conn.execute(
            "DELETE FROM chat_room_participants WHERE chat_room_id = ? AND user_id = ?",
            (chat_id, user_id),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error removing chat member: {e}")
        return False
    finally:
        conn.close()

def set_members_can_invite(chat_id, value):
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE chat_rooms SET members_can_invite = ? WHERE id = ?",
            (1 if value else 0, chat_id),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating members_can_invite: {e}")
        return False
    finally:
        conn.close()

def get_all_users():
    conn = get_db_connection()
    users = conn.execute("SELECT id, username FROM users").fetchall()
    conn.close()
    return [dict(row) for row in users]

# Initialize the database if the script is run directly (optional, app.py can handle it)
if __name__ == '__main__':
    init_db()
    print("Database initialized.")
