INSERT INTO daily_quiz (date, question, possible_answer_1, possible_answer_2, possible_answer_3, correct_answer)
VALUES
('2025-06-05', 'What is the role of market makers?', 'To provide liquidity by buying and selling securities', 'To regulate the stock market', 'To issue loans', 'To provide liquidity by buying and selling securities'),
('2025-06-06', 'What does the term "short selling" mean?', 'Selling borrowed stocks to buy them back later', 'Selling stocks at a loss', 'Selling stocks to a broker', 'Selling borrowed stocks to buy them back later'),
('2025-06-07', 'What is the purpose of technical analysis?', 'To analyze price trends and patterns', 'To evaluate company fundamentals', 'To assess market regulations', 'To analyze price trends and patterns'),
('2025-06-08', 'What is the difference between a limit order and a market order?', 'Limit sets a price, market executes immediately', 'Market sets a price, limit executes immediately', 'They are the same', 'Limit sets a price, market executes immediately'),
('2025-06-09', 'What is the VIX index?', 'A measure of market volatility', 'A stock index', 'A bond index', 'A measure of market volatility'),
('2025-06-10', 'What does the term "margin trading" mean?', 'Borrowing money to invest in stocks', 'Trading stocks without fees', 'Investing only in bonds', 'Borrowing money to invest in stocks'),
('2025-06-11', 'What is the role of an exchange-traded fund (ETF)?', 'To track the performance of a specific index or sector', 'To issue loans', 'To manage company finances', 'To track the performance of a specific index or sector'),
('2025-06-12', 'What is the difference between active and passive investing?', 'Active involves frequent trades, passive tracks indexes', 'Passive involves frequent trades, active tracks indexes', 'They are the same', 'Active involves frequent trades, passive tracks indexes'),
('2025-06-13', 'What is the purpose of a stop-loss order?', 'To limit losses by selling at a predefined price', 'To maximize profits', 'To buy stocks at a lower price', 'To limit losses by selling at a predefined price'),
('2025-06-14', 'What is the role of the Securities and Exchange Commission (SEC)?', 'To regulate and enforce securities laws', 'To issue stocks', 'To provide loans', 'To regulate and enforce securities laws')
ON CONFLICT (date) DO NOTHING;
