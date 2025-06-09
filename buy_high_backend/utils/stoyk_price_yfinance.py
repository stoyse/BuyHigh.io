#!/usr/bin/env python3
"""
Einfache Stock Price Funktion
Gibt den aktuellen Preis für ein Stock Symbol zurück
"""

import yfinance as yf

def get_stock_price(symbol):
    """
    Holt den aktuellen Aktienkurs für ein gegebenes Symbol
    
    Args:
        symbol (str): Stock Symbol (z.B. 'AAPL', 'GOOGL', 'TSLA')
        
    Returns:
        float: Aktueller Preis in USD, oder None bei Fehler
    """
    try:
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period="1d")
        
        if hist.empty:
            print(f"Keine Daten für {symbol} gefunden")
            return None
            
        current_price = hist['Close'].iloc[-1]
        return round(current_price, 2)
        
    except Exception as e:
        print(f"Fehler beim Abrufen von {symbol}: {e}")
        return None

# Beispiel Verwendung
if __name__ == "__main__":
    # Test der Funktion
    symbol = "AAPL"
    price = get_stock_price(symbol)
    
    if price:
        print(f"{symbol}: ${price}")
    else:
        print("Preis konnte nicht abgerufen werden")
    
    # Weitere Beispiele
    stocks = ["GOOGL", "TSLA", "MSFT"]
    for stock in stocks:
        price = get_stock_price(stock)
        if price:
            print(f"{stock}: ${price}")
