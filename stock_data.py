import requests
import pandas as pd
from datetime import datetime, timedelta
import dotenv
import os
import time

# Load environment variables from .env file
dotenv.load_dotenv()
# Set up API keys and URLs  
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')


# Function to get Stock Data (using Alpha Vantage)
def get_stock_data(symbol: str, start_date: str = None, end_date: str = None):
    """
    Get stock data for a given symbol between start_date and end_date.
    If dates are not provided, fetches the most recent 100 days of data.
    """
    if not ALPHA_VANTAGE_API_KEY:
        print("Warning: Alpha Vantage API key not found. Please set ALPHA_VANTAGE_API_KEY environment variable.")
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    
    stock_url = f"https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "full",  # To get more data
        "apikey": ALPHA_VANTAGE_API_KEY
    }
    
    try:
        print(f"Fetching data for {symbol}...")
        response = requests.get(stock_url, params=params)
        data = response.json()
        
        # Debug response
        if "Error Message" in data:
            print(f"API Error: {data['Error Message']}")
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
            
        if "Note" in data:
            print(f"API Note: {data['Note']}")  # This often indicates API call limits
            
        # Parse data into a DataFrame
        if "Time Series (Daily)" in data:
            time_series = data["Time Series (Daily)"]
            df = pd.DataFrame.from_dict(time_series, orient="index")
            df = df.rename(columns={
                "1. open": "Open",
                "2. high": "High",
                "3. low": "Low",
                "4. close": "Close",
                "5. volume": "Volume"
            })

            # Convert all columns to numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col])

            # Convert index to datetime and sort it
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()

            # Filter by date range if provided
            if start_date and end_date:
                start = pd.to_datetime(start_date)
                end = pd.to_datetime(end_date)
                mask = (df.index >= start) & (df.index <= end)
                df = df[mask]

            return df
        else:
            print(f"No time series data found. API response keys: {data.keys()}")
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])


# Demo function that can work without API key
def get_demo_stock_data(symbol: str = "DEMO", days: int = 30):
    """
    Generate demo stock data when API is not available
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
    
    # Start price
    start_price = 100.0 if symbol == "DEMO" else 150.0 if symbol == "AAPL" else 200.0
    
    # Create synthetic data with some randomness
    import numpy as np
    np.random.seed(42)  # For reproducibility
    
    # Generate a random walk for close prices
    changes = np.random.normal(0, 0.02, len(dates))  # Mean 0, std 2%
    close_prices = start_price * (1 + np.cumsum(changes))
    
    # Generate other columns based on close prices
    data = {
        "Open": close_prices * np.random.uniform(0.99, 1.01, len(dates)),
        "High": close_prices * np.random.uniform(1.01, 1.03, len(dates)),
        "Low": close_prices * np.random.uniform(0.97, 0.99, len(dates)),
        "Close": close_prices,
        "Volume": np.random.randint(100000, 1000000, len(dates))
    }
    
    df = pd.DataFrame(data, index=dates)
    return df


# Example usage:
if __name__ == "__main__":
    # Try the real API first
    api_data = get_stock_data("AAPL", "2023-01-01", "2023-12-31")
    
    # If no data returned, use demo data instead
    if api_data.empty:
        print("No data from API, using demo data instead.")
        api_data = get_demo_stock_data("AAPL", 365)
    
    print(f"Stock Data: Retrieved {len(api_data)} rows")
    print(api_data.head())