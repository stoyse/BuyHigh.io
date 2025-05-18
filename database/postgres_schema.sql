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
    name TEXT NOT NULL UNIQUE, -- Name des Szenarios (z. B. "Flash Crash", "Positive News")
    description TEXT, -- Beschreibung des Szenarios
    stock_price_change REAL, -- Preisänderung in Prozent
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
    title TEXT NOT NULL, -- Titel der Roadmap
    description TEXT, -- Beschreibung der Roadmap
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
    step_number INTEGER NOT NULL, -- Reihenfolge der Schritte
    title TEXT NOT NULL, -- Titel des Schritts
    description TEXT, -- Beschreibung des Schritts
    page_layout INTEGER[], -- Liste von Zahlen, z.B. ARRAY[1,2,3]
    explain TEXT, -- Erklärung des konzepts
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(roadmap_id, step_number) -- Sicherstellen, dass die Schritt-Reihenfolge eindeutig ist
);

-- Example steps for the roadmap
INSERT INTO roadmap_steps (roadmap_id, step_number, title, description, page_layout, explain)
VALUES 
(1, 1, 'What are financial markets?', 'Learn what financial markets are and how they work.', ARRAY[1,2,3], 
'Finanzmärkte sind organisierte Plattformen oder Systeme, auf denen Käufer und Verkäufer Finanzinstrumente wie Aktien, Anleihen, Währungen und Derivate handeln. Sie erfüllen mehrere wichtige Funktionen: Sie ermöglichen Unternehmen und Regierungen die Kapitalaufnahme, bieten Investoren die Möglichkeit, ihr Geld anzulegen, sorgen für Liquidität (d.h. die Möglichkeit, Vermögenswerte schnell zu kaufen oder zu verkaufen), und helfen, Preise für Finanzprodukte durch Angebot und Nachfrage zu bestimmen. Ohne Finanzmärkte wäre es für Unternehmen schwieriger, zu wachsen, und für Investoren schwerer, ihr Geld zu investieren oder zu diversifizieren.'),

(1, 2, 'Stocks and Bonds', 'Understand the difference between stocks and bonds.', ARRAY[1,2,3], 
'Aktien und Anleihen sind zwei der wichtigsten Arten von Finanzinstrumenten. Eine Aktie steht für einen Eigentumsanteil an einem Unternehmen. Wer eine Aktie besitzt, ist Miteigentümer und kann von Gewinnen (Dividenden) profitieren, trägt aber auch das Risiko von Verlusten. Eine Anleihe hingegen ist ein Schuldtitel: Der Käufer leiht einem Unternehmen oder Staat Geld und erhält dafür regelmäßige Zinszahlungen sowie die Rückzahlung des Nennwerts am Ende der Laufzeit. Während Aktien mehr Renditechancen, aber auch höhere Risiken bieten, gelten Anleihen als sicherer, bringen aber meist geringere Erträge.'),

(1, 3, 'Market Mechanisms', 'Understand how supply and demand influence the markets.', ARRAY[1,2,3], 
'Marktmechanismen beschreiben, wie Preise auf Finanzmärkten durch das Zusammenspiel von Angebot und Nachfrage entstehen. Wenn viele Investoren ein bestimmtes Wertpapier kaufen wollen (hohe Nachfrage), aber nur wenige verkaufen möchten (geringes Angebot), steigt der Preis. Umgekehrt sinkt der Preis, wenn das Angebot das Interesse der Käufer übersteigt. Diese Dynamik sorgt dafür, dass Preise ständig angepasst werden und spiegelt die Einschätzungen und Erwartungen aller Marktteilnehmer wider.')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS roadmap_quizzes (
    id SERIAL PRIMARY KEY,
    roadmap_id INTEGER NOT NULL REFERENCES roadmap(id) ON DELETE CASCADE, -- Verknüpfung mit der Roadmap
    step_id INTEGER NOT NULL REFERENCES roadmap_steps(id) ON DELETE CASCADE, -- Verknüpfung mit einem Roadmap-Schritt
    question TEXT NOT NULL, -- Die Quizfrage
    possible_answer_1 TEXT NOT NULL, -- Mögliche Antwort 1
    possible_answer_2 TEXT NOT NULL, -- Mögliche Antwort 2
    possible_answer_3 TEXT NOT NULL, -- Mögliche Antwort 3
    correct_answer TEXT NOT NULL, -- Die richtige Antwort
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Beispiel-Quizfragen für die Roadmap-Schritte
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
    is_correct BOOLEAN DEFAULT FALSE, -- Ob die Antwort korrekt war
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Zeitstempel des Versuchs
    UNIQUE(user_id, quiz_id) -- Sicherstellen, dass ein Benutzer dasselbe Quiz nicht mehrfach abschließt
);


-- User Roadmap Progress Table
CREATE TABLE IF NOT EXISTS user_roadmap_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    roadmap_id INTEGER NOT NULL REFERENCES roadmap(id) ON DELETE CASCADE,
    step_id INTEGER NOT NULL REFERENCES roadmap_steps(id) ON DELETE CASCADE,
    is_completed BOOLEAN DEFAULT FALSE, -- Fortschritt des Schritts
    progress_percentage REAL DEFAULT 0.0, -- Fortschritt in Prozent
    completed_at TIMESTAMP, -- Zeitstempel, wann der Schritt abgeschlossen wurde
    UNIQUE(user_id, roadmap_id, step_id) -- Sicherstellen, dass ein Benutzer denselben Schritt nicht mehrfach abschließt
);

CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NULL, 
    action TEXT NOT NULL, -- Die Aktion des Benutzers (z. B. 'login', 'trade', 'view_asset')
    source_details TEXT, -- Details zur Quelle der Aktion (z. B. 'web', 'mobile')
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Zeitstempel der Aktion
    details JSONB -- Zusätzliche Details zur Aktion (z. B. Asset-Symbol, Preis)
);