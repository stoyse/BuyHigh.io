import requests
import pandas as pd
from datetime import datetime, timedelta
import dotenv
import os
import time
import logging
from rich import print
from flask import g

from database.handler.postgres.postgres_db_handler import app_api_request
from database.handler.postgres.postgre_market_mayhem_handler import check_if_mayhem

# Load environment variables from .env file
dotenv.load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Twelve Data API Key - einfacher Zugriff ohne Key-Rotation
TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY')

# Demo function that can work without API key
def get_demo_stock_data(symbol: str = "DEMO", days: int = 30, is_minutes: bool = False):
    """
    Generate demo stock data when API is not available
    
    Note: All price values are in USD ($).
    """
    end_date = datetime.now()
    
    if is_minutes:
        # For 1MIN demo, generate for a shorter period, e.g., last few hours
        # 'days' here might represent number of 1-minute intervals if not careful.
        # Let's aim for 'days' worth of trading hours if 'days' is small, or cap it.
        # Assuming 8 trading hours a day.
        num_points = min(days * 60 * 8 if days <=2 else 2 * 60 * 8, 240) # Max 240 points (e.g. 4 hours of 1-min data)
        if num_points <=0: num_points = 60 # at least 1 hour
        start_time_for_minutes = end_date - timedelta(minutes=num_points)
        # Ensure start_time is not too far in the past if num_points is large due to 'days'
        actual_start_date = max(start_time_for_minutes, end_date - timedelta(days=2)) # Limit to last 2 days for minute data
        dates = pd.date_range(start=actual_start_date, end=end_date, freq='1min')
        if len(dates) > num_points : # if date_range generated too many due to full days, trim
            dates = dates[-num_points:]
    else:
        start_date = end_date - timedelta(days=days)
        freq = 'B' # Business days
        dates = pd.date_range(start=start_date, end=end_date, freq=freq)
    
    if dates.empty: # Ensure dates is not empty
        if is_minutes:
            dates = pd.date_range(end=end_date, periods=60, freq='1min') # Default to 60 points for minutes
        else:
            dates = pd.date_range(end=end_date, periods=1, freq='B')

    # Start price (in USD)
    start_price = 100.0 if symbol == "DEMO" else 150.0 if symbol == "AAPL" else 200.0
    
    # Create synthetic data with some randomness
    import numpy as np
    np.random.seed(42)  # For reproducibility
    
    # Generate a random walk for close prices (in USD)
    changes = np.random.normal(0, 0.02, len(dates))  # Mean 0, std 2%
    close_prices = start_price * (1 + np.cumsum(changes))
    close_prices = np.maximum(close_prices, 1.0) # Ensure prices don't go below 1.0
    
    # Generate other columns based on close prices (all in USD)
    data = {
        "Open": close_prices * np.random.uniform(0.99, 1.01, len(dates)),
        "High": np.maximum(close_prices * np.random.uniform(1.00, 1.03, len(dates)), close_prices), # High >= Close
        "Low": np.minimum(close_prices * np.random.uniform(0.97, 1.00, len(dates)), close_prices),   # Low <= Close
        "Close": close_prices,
        "Volume": np.random.randint(100000, 1000000, len(dates))
    }
    # Ensure High is max of Open/Close, Low is min of Open/Close
    df_temp = pd.DataFrame(data, index=dates)
    df_temp["High"] = df_temp[["Open", "Close", "High"]].max(axis=1)
    df_temp["Low"] = df_temp[["Open", "Close", "Low"]].min(axis=1)

    df = df_temp
    df.is_demo = True 

    # Mayhem-Effekt auf Demo-Daten anwenden
    df = apply_mayhem_effect(df)
    return df

def _map_interval_to_twelve_data(custom_interval: str):
    """Maps common interval strings to Twelve Data format."""
    if not custom_interval:
        return '1day' # Default
    
    custom_interval = custom_interval.lower()
    mapping = {
        '1m': '1min', '5m': '5min', '15m': '15min',
        '30m': '30min', '60m': '1h',
        'daily': '1day', '1d': '1day',
        '1wk': '1week', '1w': '1week',
        '1mo': '1month', '1m_month': '1month' # distinguish from 1minute
    }
    return mapping.get(custom_interval, '1day')

def get_stock_data(symbol: str, period: str = None, interval: str = None, start_date: str = None, end_date: str = None):
    """
    Get stock data for a given symbol using Twelve Data API.
    
    Args:
        symbol: The stock symbol (e.g., 'AAPL')
        period: Optional. E.g., '1d', '5d'. Used to calculate start_date if start_date is None for intraday.
        interval: Data interval (e.g., '1m' for 1 minute, 'daily'). Will be mapped to Twelve Data format.
        start_date: Start date for data in YYYY-MM-DD format.
        end_date: End date for data in YYYY-MM-DD format.
    
    Returns:
        DataFrame with Open, High, Low, Close, Volume columns and an 'is_demo' attribute.
    """
    # Prüfen, ob API-Key verfügbar ist
    if not TWELVE_DATA_API_KEY:
        logger.warning("No Twelve Data API key available. Cannot fetch live data.")
        return None # get_cached_or_live_data wird zu Demo-Daten zurückfallen
        
    td_interval = _map_interval_to_twelve_data(interval)

    # Determine start_date and end_date if not provided
    now = datetime.now()
    if end_date is None:
        end_date = now.strftime('%Y-%m-%d')
    
    if start_date is None:
        if td_interval in ['1min', '5min', '15min', '30min', '1h']: # Intraday
            days_to_subtract = 1
            if period:
                try:
                    if period.endswith('d'):
                        days_to_subtract = int(period[:-1])
                except ValueError:
                    pass # Keep default 1 day
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=days_to_subtract)).strftime('%Y-%m-%d')
        else: # Daily, weekly, monthly
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')

    # Parameter für den API-Aufruf
    params = {
        "symbol": symbol,
        "interval": td_interval,
        "apikey": TWELVE_DATA_API_KEY,
        "start_date": start_date,
        "end_date": end_date,
        "outputsize": 5000  # Maximale Datenpunkte anfordern
    }
    
    try:
        logger.info(f"Fetching Twelve Data for {symbol}, interval: {td_interval}, start: {start_date}, end: {end_date}")
        print(f"Fetching Twelve Data for {symbol} (interval: {td_interval}, from: {start_date} to: {end_date})...")
        
        response = requests.get("https://api.twelvedata.com/time_series", params=params)
        app_api_request(user_id=g.user['id'], source="Twelve Data")
        print(f"[red]API request to Twelve Data completed for {symbol}.")
        # Fehlerbehandlung für HTTP-Fehler
        if response.status_code == 429:  # Rate limit exceeded
            logger.warning(f"Rate limit exceeded for Twelve Data API key.")
            return None
            
        response.raise_for_status()  # Andere HTTP-Fehler auslösen
        
        data = response.json()

        # API-Fehler überprüfen
        if data.get("status") == "error" or "values" not in data:
            error_message = data.get("message", "Unknown API error")
            logger.error(f"Twelve Data API Error for {symbol}: {error_message}")
            return None
        
        # Prüfen, ob Daten zurückgegeben wurden
        if not data["values"]:
            logger.warning(f"No data values returned by Twelve Data for {symbol}")
            return pd.DataFrame()  # Leeren DataFrame zurückgeben

        # DataFrame erstellen und formatieren
        df = pd.DataFrame(data["values"])
        
        # Spalten umbenennen
        column_mapping = {
            "datetime": "Datetime",  # Wird Index
            "open": "Open",
            "high": "High",
            "low": "Low", 
            "close": "Close",
            "volume": "Volume"
        }
        df = df.rename(columns=column_mapping)
        
        # Datetime als Index setzen
        df["Datetime"] = pd.to_datetime(df["Datetime"])
        df = df.set_index("Datetime")
        
        # Spalten in numerische Werte konvertieren
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Sortieren nach Datum
        df = df.sort_index()
        
        logger.info(f"Successfully fetched {len(df)} data points for {symbol}")
        df.is_demo = False  # Als echte API-Daten markieren
        return df
            
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred with Twelve Data: {http_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error occurred with Twelve Data: {req_err}")
        return None
    except Exception as e:
        logger.error(f"Error fetching stock data from Twelve Data: {e}")
        import traceback
        traceback.print_exc()
        return None

def apply_mayhem_effect(df: pd.DataFrame):
    """
    Überprüft auf Marktereignisse und passt die Preise im DataFrame entsprechend an.
    """
    mayhem_data = check_if_mayhem()
    if mayhem_data:
        print(f"[red]Market Mayhem detected: {mayhem_data}")
        for event_id, event_data in mayhem_data.items():
            if 'mayhem_scenarios' in event_data and 'stock_price_change' in event_data['mayhem_scenarios']:
                price_change_percentage = event_data['mayhem_scenarios']['stock_price_change']
                logger.info(f"Applying price change of {price_change_percentage}% due to market mayhem.")
                # Preise anpassen
                df['Open'] *= (1 + price_change_percentage / 100)
                df['High'] *= (1 + price_change_percentage / 100)
                df['Low'] *= (1 + price_change_percentage / 100)
                df['Close'] *= (1 + price_change_percentage / 100)
            else:
                logger.warning(f"Mayhem event {event_id} missing 'stock_price_change'.")
    else:
        print("[green]No market mayhem detected.")
    return df

def get_cached_or_live_data(symbol, timeframe):
    """
    Get stock data using Twelve Data API, with fallback to demo data.
    
    Args:
        symbol: Stock symbol
        timeframe: One of '1MIN', '1W', '1M', '3M', '6M', '1Y', 'ALL'
    
    Returns:
        DataFrame with stock data and an 'is_demo' attribute.
    """
    interval_param = None
    start_date_param = None
    end_date_param = datetime.now()
    
    # Configure parameters based on timeframe
    if timeframe == '1MIN':
        interval_param = '1m'  # Mapped to '1min' bei Twelve Data
        start_date_param = end_date_param - timedelta(days=2)  # 2 Tage für 1-Minuten-Daten
    elif timeframe == '1W':
        interval_param = '1d'
        start_date_param = end_date_param - timedelta(days=7)
    elif timeframe == '1M':
        interval_param = '1d'
        start_date_param = end_date_param - timedelta(days=30)
    elif timeframe == '3M':
        interval_param = '1d'
        start_date_param = end_date_param - timedelta(days=90)
    elif timeframe == '6M':
        interval_param = '1d'
        start_date_param = end_date_param - timedelta(days=180)
    elif timeframe == '1Y':
        interval_param = '1d'
        start_date_param = end_date_param - timedelta(days=365)
    elif timeframe == 'ALL':
        interval_param = '1d'
        start_date_param = end_date_param - timedelta(days=5*365)  # Ca. 5 Jahre
    else:  # Standard auf 3 Monate
        interval_param = '1d'
        start_date_param = end_date_param - timedelta(days=90)
    
    start_date_str = start_date_param.strftime('%Y-%m-%d')
    end_date_str = end_date_param.strftime('%Y-%m-%d')
    
    # Versuche Live-Daten zu holen
    df = get_stock_data(symbol, interval=interval_param, start_date=start_date_str, end_date=end_date_str)
    
    if df is None or df.empty:
        print(f"No live data for {symbol} (timeframe {timeframe}), using demo data.")
        days_for_demo = 2 if timeframe == '1MIN' else \
                        7 if timeframe == '1W' else \
                        30 if timeframe == '1M' else \
                        90 if timeframe == '3M' else \
                        180 if timeframe == '6M' else \
                        365 if timeframe == '1Y' else 1825  # 5 Jahre für ALL
        
        is_minutes_demo = timeframe == '1MIN'
        demo_data = get_demo_stock_data(symbol, days_for_demo, is_minutes=is_minutes_demo)
        print(f"Generated demo data for {symbol}: {len(demo_data)} points. Demo flag: {getattr(demo_data, 'is_demo', True)}")
        return demo_data
    else:
        print(f"✅ Live API data received for {symbol} (timeframe {timeframe}): {len(df)} datapoints. Demo flag: {getattr(df, 'is_demo', True)}")
    
    # Mayhem-Effekt anwenden
    df = apply_mayhem_effect(df)
    
    if not hasattr(df, 'is_demo'):  # Sollte von get_stock_data gesetzt worden sein
        df.is_demo = False
    return df

# Example usage:
if __name__ == "__main__":
    print("Testing Twelve Data API stock data retrieval")
    
    # Test with a common symbol
    api_data = get_cached_or_live_data("AAPL", "1M")
    
    if api_data is not None and not api_data.empty:
        print(f"Stock Data ({'DEMO' if api_data.is_demo else 'LIVE'}): Retrieved {len(api_data)} rows for AAPL")
        print(api_data.head())
        print("---")
        print(api_data.tail())
    else:
        print("Failed to retrieve any data for AAPL.")

    # Test with minute data
    minute_data = get_cached_or_live_data("MSFT", "1MIN")
    if minute_data is not None and not minute_data.empty:
        print(f"Stock Data ({'DEMO' if minute_data.is_demo else 'LIVE'}): Retrieved {len(minute_data)} rows for MSFT (1MIN)")
        print(minute_data.head())
        print("---")
        print(minute_data.tail())
    else:
        print("Failed to retrieve any 1MIN data for MSFT.")
