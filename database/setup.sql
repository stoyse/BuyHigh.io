-- Create a table to store users (optional, if multi-user)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
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