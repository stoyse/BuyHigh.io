-- USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT,
    firebase_uid TEXT UNIQUE,
    firebase_provider TEXT DEFAULT 'password',
    balance REAL DEFAULT 10000.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    mood_pet TEXT DEFAULT 'bull',
    pet_energy INTEGER DEFAULT 100,
    is_meme_mode BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    theme TEXT DEFAULT 'light',
    total_trades INTEGER DEFAULT 0,
    profit_loss REAL DEFAULT 0.0
);

-- ASSET TYPES TABLE
CREATE TABLE IF NOT EXISTS asset_types (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- TRANSACTIONS TABLE
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    asset_type_id INTEGER,
    asset_symbol TEXT NOT NULL,
    quantity REAL NOT NULL,
    price_per_unit REAL NOT NULL,
    total_value REAL GENERATED ALWAYS AS (quantity * price_per_unit) STORED,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('buy', 'sell')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (asset_type_id) REFERENCES asset_types(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_symbol ON transactions(asset_symbol);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);

-- CHAT ROOMS TABLE
CREATE TABLE IF NOT EXISTS chat_rooms (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    members_can_invite BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

INSERT INTO chat_rooms (id, name)
VALUES (1, 'General')
ON CONFLICT (id) DO NOTHING;

-- CHAT ROOM PARTICIPANTS TABLE
CREATE TABLE IF NOT EXISTS chat_room_participants (
    chat_room_id INTEGER,
    user_id INTEGER,
    chat_name TEXT,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_room_id, user_id),
    FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- MESSAGES TABLE
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    chat_room_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    message_text TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_chat_room ON messages(chat_room_id);
CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_sent_at ON messages(sent_at);

CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,          -- e.g., AAPL, TSLA, BTC
    name TEXT NOT NULL,                   -- e.g., Apple Inc., Tesla Inc.
    asset_type TEXT NOT NULL,             -- e.g., stock, crypto, forex
    exchange TEXT,                        -- e.g., NASDAQ, NYSE
    currency TEXT DEFAULT 'USD',          -- e.g., USD, EUR
    sector TEXT,                          -- Optional: e.g., Technology, Energy
    industry TEXT,                        -- Optional: e.g., Auto Manufacturers
    logo_url TEXT,                        -- Optional: For UI
    description TEXT,                     -- Optional: Company summary
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO assets (symbol, name, asset_type, exchange, sector, industry, default_price)
VALUES 
('AAPL', 'Apple Inc.', 'stock', 'NASDAQ', 'Technology', 'Consumer Electronics', 170),
('TSLA', 'Tesla Inc.', 'stock', 'NASDAQ', 'Automotive', 'Auto Manufacturers', 250),
('GOOGL', 'Alphabet Inc.', 'stock', 'NASDAQ', 'Technology', 'Internet Content', 140),
('BTC', 'Bitcoin', 'crypto', 'Binance', NULL, NULL, 30000),
('ETH', 'Ethereum', 'crypto', 'Binance', NULL, NULL, 2000)
ON CONFLICT (symbol) DO UPDATE SET default_price = EXCLUDED.default_price;

-- Assets-Tabelle mit default_price, last_price und last_price_updated Feldern erweitern

-- Überprüfen, ob die Spalten bereits existieren, falls nicht, füge sie hinzu
DO $$
BEGIN
    -- Überprüfen ob default_price Spalte existiert
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'assets' AND column_name = 'default_price'
    ) THEN
        ALTER TABLE assets ADD COLUMN default_price REAL;
    END IF;

    -- Überprüfen ob last_price Spalte existiert
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'assets' AND column_name = 'last_price'
    ) THEN
        ALTER TABLE assets ADD COLUMN last_price REAL;
    END IF;

    -- Überprüfen ob last_price_updated Spalte existiert
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'assets' AND column_name = 'last_price_updated'
    ) THEN
        ALTER TABLE assets ADD COLUMN last_price_updated TIMESTAMP;
    END IF;
END
$$;

-- Beispielhafte Default-Preise für bestehende Assets setzen (nur falls noch nicht gesetzt)
UPDATE assets SET default_price = 170 WHERE symbol = 'AAPL' AND default_price IS NULL;
UPDATE assets SET default_price = 250 WHERE symbol = 'TSLA' AND default_price IS NULL;
UPDATE assets SET default_price = 140 WHERE symbol = 'GOOGL' AND default_price IS NULL;
UPDATE assets SET default_price = 30000 WHERE symbol = 'BTC' AND default_price IS NULL;
UPDATE assets SET default_price = 2000 WHERE symbol = 'ETH' AND default_price IS NULL;

CREATE TABLE IF NOT EXISTS portfolio (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    quantity REAL NOT NULL DEFAULT 0,               -- total amount held
    average_buy_price REAL NOT NULL DEFAULT 0,      -- average cost per unit
    total_invested REAL GENERATED ALWAYS AS (quantity * average_buy_price) STORED,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, asset_id)  -- one row per asset per user
);