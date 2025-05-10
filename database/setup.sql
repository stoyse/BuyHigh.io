-- Create a table to store users (optional, if multi-user)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT, -- Made optional as Firebase handles passwords
    firebase_uid TEXT UNIQUE, -- Added for Firebase integration
    firebase_provider TEXT DEFAULT 'password', -- Hinzugefügt: Authentifizierungsanbieter ('password', 'google', etc.)
    balance REAL DEFAULT 10000.0,  -- starting demo balance
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    
    -- Fun/quirky stuff
    mood_pet TEXT DEFAULT 'bull',     -- bull, bear, sloth, etc.
    pet_energy INTEGER DEFAULT 100,   -- gamified stat
    is_meme_mode BOOLEAN DEFAULT 0,   -- toggle for meme stocks only

    -- Optional settings
    email_verified BOOLEAN DEFAULT 0,
    theme TEXT DEFAULT 'light',
    
    -- Social / leaderboard
    total_trades INTEGER DEFAULT 0,
    profit_loss REAL DEFAULT 0.0
);

-- Create a table to store different asset types
CREATE TABLE IF NOT EXISTS asset_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL -- e.g., 'stock', 'crypto', 'forex'
);

-- Main transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    asset_type_id INTEGER,
    asset_symbol TEXT NOT NULL,         -- e.g., 'BTC', 'AAPL', 'EUR/USD'
    quantity REAL NOT NULL,             -- Amount of asset
    price_per_unit REAL NOT NULL,       -- Price at transaction time
    total_value REAL GENERATED ALWAYS AS (quantity * price_per_unit) STORED,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('buy', 'sell')),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (asset_type_id) REFERENCES asset_types(id) ON DELETE SET NULL
);

-- Optional: Add indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_symbol ON transactions(asset_symbol);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);

-- --- Chat-specific schema --- 

-- Table to store chat rooms or conversations
CREATE TABLE IF NOT EXISTS chat_rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,                         -- Name of the chat room (e.g., 'General', 'Stock Talk', etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,                       -- User-ID des Erstellers
    members_can_invite BOOLEAN DEFAULT 0,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Insert a default chat room if it doesn't exist
INSERT INTO chat_rooms (id, name) VALUES (1, 'General') ON CONFLICT(id) DO NOTHING;

-- Table to store users' participation in chat rooms
CREATE TABLE IF NOT EXISTS chat_room_participants (
    chat_room_id INTEGER,
    user_id INTEGER,
    chat_name TEXT,  -- Nickname or alias used in the chat
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_room_id, user_id),
    FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table to store chat messages
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_room_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    message_text TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Optional: Indexes for faster query access on chat data
CREATE INDEX IF NOT EXISTS idx_messages_chat_room ON messages(chat_room_id);
CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_sent_at ON messages(sent_at);