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
    level INTEGER DEFAULT 1,
    mayhem_score INTEGER DEFAULT 0
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

CREATE TABLE IF NOT EXISTS market_mayhem (
    id SERIAL PRIMARY KEY,
    scenario_id INTEGER NOT NULL REFERENCES market_mayhem_scenarios(id) ON DELETE CASCADE,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result TEXT, -- Result of the scenario (e.g., 'success', 'failure')
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Random data for the market_mayhem table
INSERT INTO market_mayhem (scenario_id, start_time, end_time, result)
VALUES
    (1, '2025-05-18', '2025-05-18', 'success'), -- Flash Crash
    (2, '2025-05-19', '2025-05-19', 'failure'), -- Positive News
    (3, '2025-05-20', '2025-05-20', 'success'), -- Interest Rate Hike
    (4, '2025-05-21', '2025-05-21', 'failure'), -- Tech Boom
    (5, '2025-05-22', '2025-05-22', 'success'), -- Earnings Miss
    (1, '2025-05-23', '2025-05-23', 'failure'), -- Flash Crash
    (2, '2025-05-24', '2025-05-24', 'success'), -- Positive News
    (3, '2025-05-25', '2025-05-25', 'failure'), -- Interest Rate Hike
    (4, '2025-05-26', '2025-05-26', 'success'), -- Tech Boom
    (5, '2025-05-27', '2025-05-27', 'failure'); -- Earnings Miss

CREATE TABLE IF NOT EXISTS market_mayhem_scenarios (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE, -- Name of the scenario (e.g., "Flash Crash", "Positive News")
    description TEXT, -- Description of the scenario
    stock_price_change REAL, -- Price change in percentage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);




-- Example data for the market_mayhem_scenarios table
INSERT INTO market_mayhem_scenarios (name, description, stock_price_change)
VALUES
    ('Flash Crash', 
     'A sudden and unexpected market crash triggered by algorithmic trading. Players must react quickly to minimize losses.', 
     -15.0),

    ('Positive News', 
     'A surprisingly positive economic announcement leads to a rapid increase in stock prices. Players must decide whether to buy or take profits.', 
     8.5),

    ('Interest Rate Hike', 
     'The central bank unexpectedly raises interest rates, causing a drop in stock prices. Players must adjust their portfolios accordingly.', 
     -5.0),

    ('Tech Boom', 
     'A breakthrough in the tech industry causes a massive surge in tech stocks. Players must decide whether to ride the hype.', 
     12.0),

    ('Earnings Miss', 
     'A major company misses earnings expectations, leading to a sharp decline in its stock price. Players must react quickly.', 
     -10.0)
ON CONFLICT (name) DO NOTHING;


-- Roadmap Table
CREATE TABLE IF NOT EXISTS roadmap (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL, -- Title of the roadmap
    description TEXT, -- Description of the roadmap
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Example Roadmap
INSERT INTO roadmap (title, description)
VALUES ('Introduction to Financial Markets', 'Learn the basics of financial markets.')
ON CONFLICT DO NOTHING;



-- Roadmap Steps Table
CREATE TABLE IF NOT EXISTS roadmap_steps (
    id SERIAL PRIMARY KEY,
    roadmap_id INTEGER NOT NULL REFERENCES roadmap(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL, -- Order of the steps
    title TEXT NOT NULL, -- Title of the step
    description TEXT, -- Description of the step
    page_layout INTEGER[], -- List of numbers, e.g., ARRAY[1,2,3]
    explain TEXT, -- Explanation of the concept
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(roadmap_id, step_number) -- Ensure the step order is unique
);

-- Example steps for the roadmap
INSERT INTO roadmap_steps (roadmap_id, step_number, title, description, page_layout, explain)
VALUES 
(1, 1, 'What are financial markets?', 'Learn what financial markets are and how they work.', ARRAY[1,2,3], 
'Financial markets are organized platforms or systems where buyers and sellers trade financial instruments such as stocks, bonds, currencies, and derivatives. They serve several important functions: they allow companies and governments to raise capital, provide investors with opportunities to invest their money, ensure liquidity (i.e., the ability to quickly buy or sell assets), and help determine prices for financial products through supply and demand. Without financial markets, it would be harder for companies to grow and for investors to invest or diversify their money.'),

(1, 2, 'Stocks and Bonds', 'Understand the difference between stocks and bonds.', ARRAY[1,2,3], 
'Stocks and bonds are two of the most important types of financial instruments. A stock represents an ownership share in a company. Whoever owns a stock is a co-owner and can benefit from profits (dividends) but also bears the risk of losses. A bond, on the other hand, is a debt security: the buyer lends money to a company or government and receives regular interest payments as well as the repayment of the principal at the end of the term. While stocks offer more return opportunities but also higher risks, bonds are considered safer but usually yield lower returns.'),

(1, 3, 'Market Mechanisms', 'Understand how supply and demand influence the markets.', ARRAY[1,2,3], 
'Market mechanisms describe how prices on financial markets are formed by the interaction of supply and demand. When many investors want to buy a particular security (high demand) but only a few want to sell (low supply), the price rises. Conversely, the price falls when supply exceeds buyer interest. This dynamic ensures that prices are constantly adjusted and reflects the assessments and expectations of all market participants.')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS roadmap_quizzes (
    id SERIAL PRIMARY KEY,
    roadmap_id INTEGER NOT NULL REFERENCES roadmap(id) ON DELETE CASCADE, -- Link to the roadmap
    step_id INTEGER NOT NULL REFERENCES roadmap_steps(id) ON DELETE CASCADE, -- Link to a roadmap step
    question TEXT NOT NULL, -- The quiz question
    possible_answer_1 TEXT NOT NULL, -- Possible answer 1
    possible_answer_2 TEXT NOT NULL, -- Possible answer 2
    possible_answer_3 TEXT NOT NULL, -- Possible answer 3
    correct_answer TEXT NOT NULL, -- The correct answer
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Example quiz questions for the roadmap steps
INSERT INTO roadmap_quizzes (roadmap_id, step_id, question, possible_answer_1, possible_answer_2, possible_answer_3, correct_answer)
VALUES 
(1, 1, 'What is a financial market?', 'A place to buy groceries', 'A platform for trading financial assets', 'A type of bank', 'A platform for trading financial assets'),
(1, 2, 'What is a stock?', 'A type of bond', 'A share in a company', 'A loan to the government', 'A share in a company'),
(1, 3, 'What determines stock prices?', 'Government policies', 'Supply and demand', 'Company logos', 'Supply and demand');

INSERT INTO xp_gains (action, xp_amount, description) 
VALUES ('roadmap_quiz_correct', 75, 'Awarded for correctly answering a roadmap quiz') 
ON CONFLICT (action) DO NOTHING;

CREATE TABLE IF NOT EXISTS user_roadmap_quiz_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quiz_id INTEGER NOT NULL REFERENCES roadmap_quizzes(id) ON DELETE CASCADE,
    is_correct BOOLEAN DEFAULT FALSE, -- Whether the answer was correct
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of the attempt
    UNIQUE(user_id, quiz_id) -- Ensure a user does not complete the same quiz multiple times
);


-- User Roadmap Progress Table
CREATE TABLE IF NOT EXISTS user_roadmap_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    roadmap_id INTEGER NOT NULL REFERENCES roadmap(id) ON DELETE CASCADE,
    step_id INTEGER NOT NULL REFERENCES roadmap_steps(id) ON DELETE CASCADE,
    is_completed BOOLEAN DEFAULT FALSE, -- Progress of the step
    progress_percentage REAL DEFAULT 0.0, -- Progress in percentage
    completed_at TIMESTAMP, -- Timestamp when the step was completed
    UNIQUE(user_id, roadmap_id, step_id) -- Ensure a user does not complete the same step multiple times
);

CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action TEXT,
    source_details TEXT,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optional: Indices for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_action ON analytics(action);
CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics(timestamp);