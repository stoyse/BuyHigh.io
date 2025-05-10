import finnhub
from datetime import datetime, timedelta
import os
import dotenv
# Load environment variables from .env file
dotenv.load_dotenv()
# Set up the API key
API_KEY = os.getenv("FINNHUB_API_KEY")


# Initialize the Finnhub client with your API key
finnhub_client = finnhub.Client(api_key=API_KEY)

def fetch_company_news(symbol, from_date, to_date):
    """
    Fetch company news from Finnhub API.
    
    :param symbol: Stock symbol of the company
    :param from_date: Start date for fetching news (YYYY-MM-DD)
    :param to_date: End date for fetching news (YYYY-MM-DD)
    :return: List of news articles
    """
    news = finnhub_client.company_news(symbol, _from=from_date, to=to_date)
    print(news)
    return news

def fetch_general_news(category="general"):
    """
    Fetch general news from Finnhub API.
    
    :param category: Category of news (e.g., "general", "forex", "crypto", etc.)
    :return: List of news articles
    """
    news = finnhub_client.general_news(category=category)
    for article in news:
        if article.get('image') == 'https://static2.finnhub.io/file/publicdatany/finnhubimage/market_watch_logo.png':
            article['image'] = None
    print(news)
    return news