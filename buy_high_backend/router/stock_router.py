

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import pandas as pd
import utils.stock_data_api as stock_data
from ..auth_utils import get_current_user, AuthenticatedUser
from ..pydantic_models import StockDataPoint

logger = logging.getLogger(__name__)
router = APIRouter()

def update_asset_price_in_db(symbol: str, price: float, user_id_for_analytics: Optional[int] = None):
    """Updates the last known price of an asset in the database."""
    import database.handler.postgres.postgre_transactions_handler as transactions_handler
    
    try:
        with transactions_handler.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM assets WHERE symbol = %s", (symbol,))
                asset_row = cur.fetchone()
                
                if not asset_row:
                    logger.warning(f"Asset with symbol '{symbol}' not found, cannot update price.")
                    return False
                
                cur.execute("""
                    UPDATE assets SET last_price = %s, last_price_updated = CURRENT_TIMESTAMP
                    WHERE symbol = %s
                """, (price, symbol))
                conn.commit()
                return True
    except Exception as e:
        logger.error(f"Error updating asset price in database: {e}", exc_info=True)
        return False

@router.get("/stock-data", response_model=List[StockDataPoint])
async def api_stock_data(
    symbol: str = 'AAPL',
    timeframe: str = '3M',
    fresh: bool = False,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    user_id_for_analytics = current_user.id if current_user else None
    logger.info(f"Accessing /stock-data for user: {user_id_for_analytics}. Symbol: {symbol}, Timeframe: {timeframe}, Fresh: {fresh}")

    end_date_dt = datetime.now()
    start_date_dt = None
    period_param_for_1min = None
    
    timeframe_map = {
        '1MIN': {'interval': '1m', 'delta': timedelta(days=2), 'period': '2d'},
        '1W': {'interval': '1d', 'delta': timedelta(days=7)},
        '1M': {'interval': '1d', 'delta': timedelta(days=30)},
        '3M': {'interval': '1d', 'delta': timedelta(days=90)},
        '6M': {'interval': '1d', 'delta': timedelta(days=180)},
        '1Y': {'interval': '1d', 'delta': timedelta(days=365)},
        'ALL': {'interval': '1d', 'delta': timedelta(days=1825)} # 5 years
    }
    
    settings = timeframe_map.get(timeframe.upper(), timeframe_map['3M'])
    interval_param = settings['interval']
    start_date_dt = end_date_dt - settings['delta']
    if timeframe.upper() == '1MIN':
        period_param_for_1min = settings['period']

    end_date_str = end_date_dt.strftime('%Y-%m-%d')
    start_date_str = start_date_dt.strftime('%Y-%m-%d') if start_date_dt else None

    try:
        if fresh:
            logger.info(f"Force fresh data for {symbol}, timeframe: {timeframe}")
            df = stock_data.get_stock_data(symbol, period=period_param_for_1min, interval=interval_param, 
                                         start_date=start_date_str, end_date=end_date_str)
        else:
            logger.info(f"Getting cached or live data for {symbol}, timeframe: {timeframe}")
            df = stock_data.get_cached_or_live_data(symbol, timeframe)
        
        is_demo_data = getattr(df, 'is_demo', True)
        logger.info(f"Data received for {symbol}: Demo = {is_demo_data}, Points = {len(df) if df is not None and not df.empty else 0}")

        if df is None or df.empty:
            logger.warning(f"DataFrame for {symbol} is None or empty. Generating explicit demo data.")
            is_minutes_demo = timeframe == '1MIN'
            demo_days = (end_date_dt - start_date_dt).days if start_date_dt is not None else 90
            demo_units = 240 if is_minutes_demo else demo_days
            df = stock_data.get_demo_stock_data(symbol, demo_units, is_minutes=is_minutes_demo)
            is_demo_data = True
            
            if df is None or df.empty:
                logger.error(f"No data (including fallback demo) found for {symbol}. Returning empty list.")
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={'data': [], 'is_demo': True, 'currency': 'USD', 'demo_reason': 'API key missing' if not stock_data.TWELVE_DATA_API_KEY else 'API request failed or empty data'}
                )

        data = []
        if df is not None and not df.empty:
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"Data for {symbol} is missing one or more required columns. Available: {list(df.columns)}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Data processing error: Missing columns for {symbol}')

            for index, row in df.iterrows():
                try:
                    timestamp_to_format = index.tz_localize(None) if index.tzinfo else index
                    
                    open_price = float(row['Open']) if pd.notna(row['Open']) else None
                    high_price = float(row['High']) if pd.notna(row['High']) else None
                    low_price = float(row['Low']) if pd.notna(row['Low']) else None
                    close_price = float(row['Close']) if pd.notna(row['Close']) else None
                    volume = int(row['Volume']) if pd.notna(row['Volume']) else None

                    if any(v is None for v in [open_price, high_price, low_price, close_price, volume]):
                        logger.warning(f"Skipping row for {symbol} at {index} due to missing critical data.")
                        continue

                    data.append(StockDataPoint(
                        date=timestamp_to_format.strftime('%Y-%m-%dT%H:%M:%S'),
                        open=open_price, high=high_price, low=low_price, close=close_price, volume=volume, currency='USD'
                    ))
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting row data for {symbol} at {index}: {e}. Row: {row.to_dict()}")
                    continue
        
        if not is_demo_data and len(data) > 0 and data[-1].close is not None:
            try:
                update_asset_price_in_db(symbol, float(data[-1].close), user_id_for_analytics)
            except Exception as e:
                logger.error(f"Error updating asset price in database: {e}")
        
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /api/stock-data for {symbol} timeframe {timeframe}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))