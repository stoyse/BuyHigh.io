INSERT INTO daily_quiz (date, question, possible_answer_1, possible_answer_2, possible_answer_3, correct_answer)
VALUES
('2025-05-14', 'Was ist ein Bullenmarkt?', 'Ein Markt mit fallenden Kursen', 'Ein Markt mit steigenden Kursen', 'Ein Markt ohne Bewegung', 'Ein Markt mit steigenden Kursen'),
('2025-05-15', 'Welche Börse ist die größte der Welt nach Marktkapitalisierung?', 'NASDAQ', 'New York Stock Exchange', 'London Stock Exchange', 'New York Stock Exchange'),
('2025-05-16', 'Was bedeutet das Kürzel "ETF"?', 'Exchange Traded Fund', 'Equity Trading Fund', 'Electronic Transfer Fund', 'Exchange Traded Fund'),
('2025-05-17', 'Was ist ein Leerverkauf?', 'Kauf von Aktien ohne Geld', 'Verkauf geliehener Aktien', 'Kauf von Anleihen', 'Verkauf geliehener Aktien'),
('2025-05-18', 'Wie nennt man den Zinssatz, zu dem sich Banken untereinander Geld leihen?', 'Leitzins', 'LIBOR', 'Dividende', 'LIBOR'),
('2025-05-19', 'Was misst der DAX?', 'Die Entwicklung der 30 größten deutschen Unternehmen', 'Die Entwicklung aller europäischen Aktien', 'Die Entwicklung der US-Technologiewerte', 'Die Entwicklung der 30 größten deutschen Unternehmen'),
('2025-05-20', 'Was ist eine Anleihe?', 'Ein Anteil an einem Unternehmen', 'Ein verzinsliches Wertpapier', 'Eine Rohstoffoption', 'Ein verzinsliches Wertpapier'),
('2025-05-21', 'Was ist ein IPO?', 'International Portfolio Order', 'Initial Public Offering', 'Interest Payment Option', 'Initial Public Offering'),
('2025-05-22', 'Was ist ein Derivat?', 'Ein Basiswert', 'Ein abgeleitetes Finanzinstrument', 'Eine Aktie', 'Ein abgeleitetes Finanzinstrument'),
('2025-05-23', 'Wer reguliert die US-Börsenaufsicht?', 'SEC', 'FED', 'ECB', 'SEC'),
('2025-05-24', 'Was ist eine Dividende?', 'Ein Kursverlust', 'Eine Gewinnbeteiligung', 'Eine Steuer', 'Eine Gewinnbeteiligung'),
('2025-05-25', 'Was ist der Unterschied zwischen Aktie und Anleihe?', 'Aktie ist Eigenkapital, Anleihe ist Fremdkapital', 'Beides ist Eigenkapital', 'Beides ist Fremdkapital', 'Aktie ist Eigenkapital, Anleihe ist Fremdkapital'),
('2025-05-26', 'Was ist ein Stop-Loss?', 'Eine Order zum Begrenzen von Verlusten', 'Eine Order zum Maximieren von Gewinnen', 'Eine Order zum Kaufen bei Tiefstkurs', 'Eine Order zum Begrenzen von Verlusten'),
('2025-05-27', 'Was ist ein Blue Chip?', 'Eine riskante Aktie', 'Eine Aktie eines etablierten Unternehmens', 'Eine Penny Stock', 'Eine Aktie eines etablierten Unternehmens'),
('2025-05-28', 'Was ist der S&P 500?', 'Ein Index europäischer Aktien', 'Ein Index der 500 größten US-Unternehmen', 'Ein Rohstoffindex', 'Ein Index der 500 größten US-Unternehmen'),
('2025-05-29', 'Was ist ein Spread?', 'Die Differenz zwischen Kauf- und Verkaufskurs', 'Die Anzahl der gehandelten Aktien', 'Die Marktkapitalisierung', 'Die Differenz zwischen Kauf- und Verkaufskurs'),
('2025-05-30', 'Was ist eine Hausse?', 'Ein Markt mit fallenden Kursen', 'Ein Markt mit steigenden Kursen', 'Ein stagnierender Markt', 'Ein Markt mit steigenden Kursen'),
('2025-05-31', 'Was ist ein Margin Call?', 'Aufforderung, Sicherheiten nachzuschießen', 'Aufforderung, Aktien zu verkaufen', 'Aufforderung, Dividenden zu zahlen', 'Aufforderung, Sicherheiten nachzuschießen'),
('2025-06-01', 'Was ist ein Short Squeeze?', 'Ein plötzlicher Kursanstieg bei vielen Leerverkäufen', 'Ein Kursrückgang bei vielen Käufen', 'Eine Dividendenzahlung', 'Ein plötzlicher Kursanstieg bei vielen Leerverkäufen'),
('2025-06-02', 'Was ist ein Volatilitätsindex?', 'Ein Index für Rohstoffe', 'Ein Index für Kursschwankungen', 'Ein Index für Dividenden', 'Ein Index für Kursschwankungen')
ON CONFLICT (date) DO NOTHING;
