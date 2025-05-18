-- Add at the end of the file

-- Easter eggs tracking
CREATE TABLE IF NOT EXISTS easter_eggs_redeemed (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    code VARCHAR(50) NOT NULL,
    redeemed_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT unique_egg_redemption UNIQUE (user_id, code)
);
