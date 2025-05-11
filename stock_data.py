import requests
import pandas as pd
from datetime import datetime, timedelta
import dotenv
import os
import time
import json
import logging

# Load environment variables from .env file
dotenv.load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Key Management
class ApiKeyManager:
    def __init__(self, key_prefix='ALPHA_VANTAGE_API_KEY', keys_file='.api_key_status.json'):
        self.key_prefix = key_prefix
        self.keys_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), keys_file)
        self.keys = self._load_keys_from_env()
        self.key_status = self._load_key_status()
        self.current_key_index = self._get_valid_key_index()
        logger.info(f"API Key Manager initialized with {len(self.keys)} keys")
    
    def _load_keys_from_env(self):
        """Lädt alle API Keys aus den Umgebungsvariablen"""
        keys = []
        # Der Hauptschlüssel wird immer hinzugefügt
        main_key = os.getenv(self.key_prefix)
        if main_key:
            keys.append(main_key)
        
        # Zusätzliche Keys mit _1, _2, etc.
        i = 1
        while True:
            key = os.getenv(f"{self.key_prefix}_{i}")
            if not key:
                break
            keys.append(key)
            i += 1
        
        return keys
    
    def _load_key_status(self):
        """Lädt den Status der API-Keys"""
        if not os.path.exists(self.keys_file):
            # Standardstatus für alle Keys erstellen
            return {key: {"limited": False, "limited_since": None} for key in self.keys}
        
        try:
            with open(self.keys_file, 'r') as f:
                status = json.load(f)
                
            # Konvertiere Zeitstempel zurück in datetime-Objekte
            for key, info in status.items():
                if info["limited_since"]:
                    info["limited_since"] = datetime.fromisoformat(info["limited_since"])
            
            # Prüfe, ob Keys zurückgesetzt werden sollten (24h seit Limitierung)
            for key, info in status.items():
                if info["limited"] and info["limited_since"]:
                    if datetime.now() - info["limited_since"] > timedelta(hours=24):
                        logger.info(f"Resetting API key that was limited since {info['limited_since']}")
                        info["limited"] = False
                        info["limited_since"] = None
            
            # Füge neue Keys hinzu, falls welche fehlen
            for key in self.keys:
                if key not in status:
                    status[key] = {"limited": False, "limited_since": None}
            
            return status
        except Exception as e:
            logger.error(f"Error loading key status: {e}")
            return {key: {"limited": False, "limited_since": None} for key in self.keys}
    
    def _save_key_status(self):
        """Speichert den aktuellen Status der API-Keys"""
        try:
            # Konvertiere datetime-Objekte in ISO-Format-Strings für JSON-Serialisierung
            status_copy = {}
            for key, info in self.key_status.items():
                status_copy[key] = {
                    "limited": info["limited"],
                    "limited_since": info["limited_since"].isoformat() if info["limited_since"] else None
                }
            
            with open(self.keys_file, 'w') as f:
                json.dump(status_copy, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving key status: {e}")
    
    def _get_valid_key_index(self):
        """Gibt den Index eines gültigen API-Keys zurück"""
        for i, key in enumerate(self.keys):
            if key in self.key_status and not self.key_status[key]["limited"]:
                return i
        
        # Wenn alle Keys limitiert sind, setze den ältesten zurück
        if not self.keys:
            return -1
        
        # Finde den am längsten limitierten Key
        oldest_limited = None
        oldest_index = 0
        
        for i, key in enumerate(self.keys):
            if key in self.key_status and self.key_status[key]["limited_since"]:
                if not oldest_limited or self.key_status[key]["limited_since"] < oldest_limited:
                    oldest_limited = self.key_status[key]["limited_since"]
                    oldest_index = i
        
        # Setze den Status zurück
        if oldest_limited:
            self.key_status[self.keys[oldest_index]] = {"limited": False, "limited_since": None}
            logger.warning(f"All keys were limited. Resetting the oldest limited key.")
            self._save_key_status()
            return oldest_index
        
        # Wenn keine Keys limitiert waren (was seltsam wäre), nehme den ersten
        return 0 if self.keys else -1
    
    def get_current_key(self):
        """Gibt den aktuellen API-Key zurück"""
        if not self.keys:
            logger.error("No API keys available!")
            return None
        
        if self.current_key_index < 0 or self.current_key_index >= len(self.keys):
            self.current_key_index = self._get_valid_key_index()
        
        return self.keys[self.current_key_index]
    
    def mark_key_as_limited(self):
        """Markiert den aktuellen Key als limitiert und wechselt zum nächsten"""
        if not self.keys:
            return None
        
        current_key = self.keys[self.current_key_index]
        self.key_status[current_key] = {
            "limited": True, 
            "limited_since": datetime.now()
        }
        logger.warning(f"API key {self.current_key_index+1} has reached its limit and will be marked as limited for 24 hours.")
        
        # Wechsle zum nächsten gültigen Key
        self.current_key_index = self._get_valid_key_index()
        self._save_key_status()
        
        return self.get_current_key()

# Initialisiere den API-Key-Manager
api_key_manager = ApiKeyManager()

# Function to get Stock Data (using Alpha Vantage)
def get_stock_data(symbol: str, period: str = None, interval: str = None, start_date: str = None, end_date: str = None):
    """
    Get stock data for a given symbol with various parameters.
    
    Args:
        symbol: The stock symbol (e.g., 'AAPL')
        period: Only for intraday data, e.g., '1d', '5d', etc.
        interval: Data interval (e.g., '1m' for 1 minute, '5m', '15m', '30m', '60m', 'daily')
        start_date: Start date for data in YYYY-MM-DD format
        end_date: End date for data in YYYY-MM-DD format
    
    Returns:
        DataFrame with Open, High, Low, Close, Volume columns and an 'is_demo' attribute.
        
    Note: All price values are in USD ($).
    """
    # Mit Key-Rotation: Versuche mit allen verfügbaren Keys
    max_retries = len(api_key_manager.keys)
    retries = 0
    
    while retries < max_retries:
        # Get current API key
        ALPHA_VANTAGE_API_KEY = api_key_manager.get_current_key()
        
        if not ALPHA_VANTAGE_API_KEY:
            logger.warning("No API keys available. Using demo data instead.")
            return None
        
        # Determine the function type based on interval
        function_type = "TIME_SERIES_DAILY" if not interval or interval.endswith('d') else "TIME_SERIES_INTRADAY"
        
        # API endpoint parameters
        params = {
            "function": function_type,
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        # Add additional parameters based on function type
        if function_type == "TIME_SERIES_INTRADAY":
            # For intraday data, we need interval and optional period
            params["interval"] = interval
            params["outputsize"] = "full"
            if period:
                # Some intraday periods require extended history
                if period == '1d' or period == '2d':
                    params["outputsize"] = "full"
        else:
            # For daily data
            params["outputsize"] = "full"  # To get more historical data
        
        # Make request
        try:
            logger.info(f"Fetching {function_type} data for {symbol} with key #{api_key_manager.current_key_index+1}")
            print(f"Fetching {function_type} data for {symbol} {'with interval ' + interval if interval else ''}...")
            print(f"Request URL: https://www.alphavantage.co/query with params: {params}")
            response = requests.get("https://www.alphavantage.co/query", params=params)
            
            # Check for HTTP errors
            response.raise_for_status()
            
            data = response.json()
            
            # Print full API response for debugging
            print(f"API Response Keys: {list(data.keys())}")
            
            # Check for API errors
            if "Error Message" in data:
                print(f"API Error: {data['Error Message']}")
                return None
                
            if "Note" in data:
                print(f"API Note: {data['Note']}") # API call limits warning
                if "API call limit" in data["Note"]:
                    # API-Key ist limitiert, wechsle zum nächsten
                    api_key_manager.mark_key_as_limited()
                    retries += 1
                    continue
            
            if "Information" in data:
                print(f"API Information: {data['Information']}")
                # API-Key ist limitiert, wechsle zum nächsten
                if "API key" in data["Information"] and "rate limit" in data["Information"]:
                    api_key_manager.mark_key_as_limited()
                    retries += 1
                    continue
                return None
                
            # Process data based on the function type
            if function_type == "TIME_SERIES_INTRADAY":
                time_series_key = f"Time Series ({interval})"
            else:
                time_series_key = "Time Series (Daily)"
                
            if time_series_key not in data:
                print(f"No data found for key: {time_series_key}")
                print(f"Available keys: {list(data.keys())}")
                # Fallback versuchen: Sometimes Alpha Vantage sends data with different key names
                alternative_keys = ["Time Series (Daily)", "Weekly Time Series", "Monthly Time Series"]
                found = False
                for alt_key in alternative_keys:
                    if alt_key in data:
                        print(f"Found alternative key: {alt_key}")
                        time_series_key = alt_key
                        found = True
                        break
                
                if not found:
                    print(f"Full API Response (first 500 chars): {str(data)[:500]}...")
                    return None
                
            # Parse the time series data
            time_series = data[time_series_key]
            df = pd.DataFrame.from_dict(time_series, orient="index")
            
            # Rename columns
            column_mapping = {
                "1. open": "Open",
                "2. high": "High",
                "3. low": "Low", 
                "4. close": "Close",
                "5. volume": "Volume"
            }
            df = df.rename(columns=column_mapping)
            
            # Convert all columns to numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            # Convert index to datetime and sort
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Filter by date range if provided
            if start_date and end_date:
                start = pd.to_datetime(start_date)
                end = pd.to_datetime(end_date)
                mask = (df.index >= start) & (df.index <= end)
                df = df[mask]
            
            # For minute data, typically only need recent data
            if interval and 'm' in interval:
                # For 1-minute data, limit to last trading day(s)
                if interval == '1m' and period:
                    days = int(period[0]) if period[0].isdigit() else 1
                    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
                    df = df[df.index > cutoff]
            
            print(f"Successfully fetched {len(df)} data points for {symbol}")
            df.is_demo = False # Mark as real API data
            return df
                
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            return None
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
            return None
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
            return None
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
            return None
        except Exception as e:
            print(f"Error fetching stock data: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            return None


def get_cached_or_live_data(symbol, timeframe):
    """
    Get stock data with caching strategy to work around API limits.
    First tries to get live data, falls back to demo if needed.
    
    Args:
        symbol: Stock symbol
        timeframe: One of '1MIN', '1W', '1M', '3M', '6M', '1Y', 'ALL'
    
    Returns:
        DataFrame with stock data and an 'is_demo' attribute.
    """
    period = None
    interval = None
    start_date = None
    end_date = None
    
    now = datetime.now()
    
    # Configure parameters based on timeframe
    if timeframe == '1MIN':
        period = '2d'
        interval = '1m'
    elif timeframe == '1W':
        interval = 'daily'
        start_date = (now - timedelta(days=7)).strftime('%Y-%m-%d')
    elif timeframe == '1M':
        interval = 'daily'
        start_date = (now - timedelta(days=30)).strftime('%Y-%m-%d')
    elif timeframe == '3M':
        interval = 'daily'
        start_date = (now - timedelta(days=90)).strftime('%Y-%m-%d')
    elif timeframe == '6M':
        interval = 'daily'
        start_date = (now - timedelta(days=180)).strftime('%Y-%m-%d')
    elif timeframe == '1Y':
        interval = 'daily'
        start_date = (now - timedelta(days=365)).strftime('%Y-%m-%d')
    elif timeframe == 'ALL':
        interval = 'daily'
        start_date = (now - timedelta(days=1825)).strftime('%Y-%m-%d')
    else:
        # Default to 3 months of daily data
        interval = 'daily'
        start_date = (now - timedelta(days=90)).strftime('%Y-%m-%d')
    
    end_date = now.strftime('%Y-%m-%d')
    
    # Try to get live data first
    df = get_stock_data(symbol, period, interval, start_date, end_date)
    
    # If no data returned or it's empty, use demo data
    if df is None or df.empty:
        print(f"No live data available for {symbol} with timeframe {timeframe}, using demo data for chart.")
        days = 5 if timeframe == '1MIN' else 7 if timeframe == '1W' else 30 if timeframe == '1M' else \
              90 if timeframe == '3M' else 180 if timeframe == '6M' else 365 if timeframe == '1Y' else 1825
        
        # Demo data for 1MIN should also be short
        if timeframe == '1MIN':
             return get_demo_stock_data(symbol, days, is_minutes=True) # Pass is_minutes for 1MIN
        return get_demo_stock_data(symbol, days)
    
    # Ensure is_demo attribute is set (should be False if we got here from get_stock_data)
    if not hasattr(df, 'is_demo'):
        df.is_demo = False
    return df


# Demo function that can work without API key
def get_demo_stock_data(symbol: str = "DEMO", days: int = 30, is_minutes: bool = False):
    """
    Generate demo stock data when API is not available
    
    Note: All price values are in USD ($).
    """
    end_date = datetime.now()
    
    if is_minutes:
        # For 1MIN demo, generate for a shorter period, e.g., last few hours
        start_date = end_date - timedelta(hours=max(1, days / 24)) # Approx 'days' worth of minutes if days is small
        freq = '1min'
        # Ensure we don't generate too many points for minute data
        num_points = min(days * 60 * 8, 240) # Max 240 points (4 hours of 1-min data) or less
        dates = pd.date_range(end=end_date, periods=num_points, freq=freq)

    else:
        start_date = end_date - timedelta(days=days)
        freq = 'B' # Business days
        dates = pd.date_range(start=start_date, end=end_date, freq=freq)
    
    if dates.empty: # Ensure dates is not empty
        dates = pd.date_range(end=end_date, periods=1, freq=freq)

    # Start price (in USD)
    start_price = 100.0 if symbol == "DEMO" else 150.0 if symbol == "AAPL" else 200.0
    
    # Create synthetic data with some randomness
    import numpy as np
    np.random.seed(42)  # For reproducibility
    
    # Generate a random walk for close prices (in USD)
    changes = np.random.normal(0, 0.02, len(dates))  # Mean 0, std 2%
    close_prices = start_price * (1 + np.cumsum(changes))
    
    # Generate other columns based on close prices (all in USD)
    data = {
        "Open": close_prices * np.random.uniform(0.99, 1.01, len(dates)),
        "High": close_prices * np.random.uniform(1.01, 1.03, len(dates)),
        "Low": close_prices * np.random.uniform(0.97, 0.99, len(dates)),
        "Close": close_prices,
        "Volume": np.random.randint(100000, 1000000, len(dates))
    }
    
    df = pd.DataFrame(data, index=dates)
    df.is_demo = True # Mark as demo data
    return df


# Example usage:
if __name__ == "__main__":
    # Try the real API first
    api_data = get_cached_or_live_data("AAPL", "1Y")
    
    # If no data returned, use demo data instead
    if api_data.empty:
        print("No data from API, using demo data instead.")
        api_data = get_demo_stock_data("AAPL", 365)
    
    print(f"Stock Data: Retrieved {len(api_data)} rows")
    print(api_data.head())