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
    profit_loss REAL DEFAULT 0.0,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1
);

-- ASSET TYPES TABLE
CREATE TABLE IF NOT EXISTS asset_types (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- TRANSACTIONS TABLE
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    asset_type_id INTEGER REFERENCES asset_types(id) ON DELETE SET NULL,
    asset_symbol TEXT NOT NULL,
    quantity REAL NOT NULL,
    price_per_unit REAL NOT NULL,
    total_value REAL GENERATED ALWAYS AS (quantity * price_per_unit) STORED,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('buy', 'sell')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_symbol ON transactions(asset_symbol);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);

-- CHAT ROOMS TABLE
CREATE TABLE IF NOT EXISTS chat_rooms (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    members_can_invite BOOLEAN DEFAULT FALSE
);


-- CHAT ROOM PARTICIPANTS TABLE
CREATE TABLE IF NOT EXISTS chat_room_participants (
    chat_room_id INTEGER REFERENCES chat_rooms(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    chat_name TEXT,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_room_id, user_id)
);

INSERT INTO chat_rooms (id, name)
VALUES (1, 'General')
ON CONFLICT (id) DO NOTHING;

-- MESSAGES TABLE
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    chat_room_id INTEGER NOT NULL REFERENCES chat_rooms(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_text TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_chat_room ON messages(chat_room_id);
CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_sent_at ON messages(sent_at);

-- ASSETS TABLE
CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    exchange TEXT,
    currency TEXT DEFAULT 'USD',
    sector TEXT,
    industry TEXT,
    logo_url TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    default_price REAL,
    last_price REAL,
    last_price_updated TIMESTAMP
);

INSERT INTO assets (symbol, name, asset_type, exchange, sector, industry, default_price)
VALUES 
('AAPL', 'Apple Inc.', 'stock', 'NASDAQ', 'Technology', 'Consumer Electronics', 170),
('TSLA', 'Tesla Inc.', 'stock', 'NASDAQ', 'Automotive', 'Auto Manufacturers', 250),
('GOOGL', 'Alphabet Inc.', 'stock', 'NASDAQ', 'Technology', 'Internet Content', 140),
('NVDA', 'NVIDIA Corporation', 'stock', 'NASDAQ', 'Technology', 'Semiconductors', 950),
('NOC', 'Northrop Grumman Corporation', 'stock', 'NYSE', 'Industrials', 'Aerospace & Defense', 470)
ON CONFLICT (symbol) DO UPDATE SET default_price = EXCLUDED.default_price;

-- PORTFOLIO TABLE
CREATE TABLE IF NOT EXISTS portfolio (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    quantity REAL NOT NULL DEFAULT 0,
    average_buy_price REAL NOT NULL DEFAULT 0,
    total_invested REAL GENERATED ALWAYS AS (quantity * average_buy_price) STORED,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, asset_id)
);

CREATE TABLE IF NOT EXISTS xp_levels (
    level INTEGER PRIMARY KEY,
    xp_required INTEGER NOT NULL,
    bonus_percentage REAL NOT NULL
);
INSERT INTO xp_levels (level, xp_required, bonus_percentage)
VALUES 
(1, 0, 0.0),
(2, 100, 5.0),
(3, 300, 10.0),
(4, 600, 15.0),
(5, 1000, 20.0),
(6, 1500, 25.0),
(7, 2100, 30.0),
(8, 2800, 35.0),
(9, 3600, 40.0),
(10, 4500, 50.0)
ON CONFLICT (level) DO NOTHING;

CREATE TABLE IF NOT EXISTS xp_gains (
    id SERIAL PRIMARY KEY,
    action TEXT NOT NULL UNIQUE, -- The action name (e.g., 'buy', 'sell', 'login', 'invite_friend')
    xp_amount INTEGER NOT NULL, -- The amount of XP awarded for the action
    description TEXT, -- Optional description of the action
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Example data for XP gains
INSERT INTO xp_gains (action, xp_amount, description)
VALUES
('buy', 50, 'Awarded for buying an asset'),
('sell', 50, 'Awarded for selling an asset'),
('login', 5, 'Awarded for daily login'),
('invite_friend', 100, 'Awarded for inviting a friend'),
('complete_profile', 50, 'Awarded for completing the user profile'),
('daily_quiz', 100, 'Awarded for completing the daily quiz')
ON CONFLICT (action) DO NOTHING;

CREATE TABLE IF NOT EXISTS daily_quiz (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    question TEXT NOT NULL,
    possible_answer_1 TEXT NOT NULL,
    possible_answer_2 TEXT NOT NULL,
    possible_answer_3 TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_quiz_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quiz_id INTEGER NOT NULL REFERENCES daily_quiz(id) ON DELETE CASCADE,
    selected_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, quiz_id)
);



CREATE TABLE IF NOT EXISTS developers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Insert a developer into the developers table
INSERT INTO developers (user_id, name)
VALUES ('1', 'Julian')
ON CONFLICT (user_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS api_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source TEXT NOT NULL
);