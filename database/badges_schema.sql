-- BADGES TABLE
CREATE TABLE IF NOT EXISTS badges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,  -- z.B. experience, performance, specialization, account_status, community
    icon_name VARCHAR(100),         -- Für Symbolreferenz (z.B. SVG-Pfad oder Symbolklasse)
    color VARCHAR(50),              -- Für Badge-Farbstil (z.B. 'neo-blue', 'neo-amber')
    level INTEGER DEFAULT 1,        -- Für Badges mit mehreren Stufen (z.B. 1, 2, 3)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- USER_BADGES TABLE (für die Zuweisung von Badges zu Benutzern)
CREATE TABLE IF NOT EXISTS user_badges (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id INTEGER NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, badge_id)
);

-- Einige Standard-Badges einfügen
INSERT INTO badges (name, description, category, icon_name, color, level)
VALUES 
-- Erfahrungsstufen-Badges
('Anfänger', 'Weniger als 6 Monate Handelserfahrung', 'experience', 'briefcase', 'neo-emerald', 1),
('Fortgeschritten', '6-24 Monate Handelserfahrung', 'experience', 'document', 'neo-blue', 2),
('Erfahren', '2-5 Jahre Handelserfahrung', 'experience', 'building', 'neo-purple', 3),
('Experte', 'Mehr als 5 Jahre Handelserfahrung', 'experience', 'scale', 'neo-amber', 4),
('Veteran', 'Über 10 Jahre Handelserfahrung', 'experience', 'star', 'neo-red', 5),

-- Performance-Badges
('Top Performer', 'Top 5% Rendite im letzten Monat', 'performance', 'trending-up', 'neo-emerald', 1),
('Risiko-Trader', 'Handel mit hoher Volatilität', 'performance', 'warning', 'neo-red', 1),
('Konstante Rendite', 'Positive Rendite über 3+ Monate', 'performance', 'chart-bar', 'neo-amber', 1),
('Diversifizierer', 'Portfolio über mehrere Anlageklassen', 'performance', 'switch-horizontal', 'neo-blue', 1),

-- Spezialisierungs-Badges
('Krypto-Händler', 'Spezialisiert auf Kryptowährungen', 'specialization', 'currency-dollar', 'neo-purple', 1),
('Aktien-Profi', 'Fokus auf Aktienmärkte', 'specialization', 'chart-bar', 'neo-emerald', 1),
('ETF-Stratege', 'ETF-basierte Anlagestrategien', 'specialization', 'template', 'neo-amber', 1),
('Forex-Händler', 'Devisenhandel-Spezialist', 'specialization', 'scale', 'neo-blue', 1),
('Rohstoff-Investor', 'Fokus auf Rohstoffmärkte', 'specialization', 'cube', 'neo-purple', 1),

-- Kontostatus-Badges
('Verifiziert', 'Vollständig verifiziertes Konto', 'account_status', 'shield-check', 'neo-emerald', 1),
('Premium', 'Premium-Mitglied', 'account_status', 'gift', 'neo-amber', 1),
('VIP', 'VIP-Kontoinhaber', 'account_status', 'star', 'neo-red', 1),
('Gründungsmitglied', 'Mit BuyHigh.io von Anfang an', 'account_status', 'building', 'neo-purple', 1),

-- Community-Badges
('Mentor', 'Hilft aktiv neuen Händlern', 'community', 'chat-alt', 'neo-blue', 1),
('Strategie-Autor', 'Teilt wertvolle Trading-Strategien', 'community', 'document', 'neo-purple', 1),
('Analytiker', 'Erstellt qualitativ hochwertige Analysen', 'community', 'chart', 'neo-emerald', 1)
ON CONFLICT DO NOTHING;

-- Beispielhafte Badge-Zuweisungen für Testzwecke (optional)
-- Dies kann in einer Testumgebung verwendet werden, um Badges für Benutzer zu erstellen
-- Ersetze 1 durch die tatsächliche Benutzer-ID
-- INSERT INTO user_badges (user_id, badge_id) VALUES 
-- (1, 1),  -- Benutzer 1 erhält Anfänger-Badge
-- (1, 7);  -- Benutzer 1 erhält Top Performer-Badge
