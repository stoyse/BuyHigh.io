"""
API Router für BuyHigh.io
Enthält alle benötigten API-Routen basierend auf apiService.ts
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body, Request as FastAPIRequest
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import logging
import pandas as pd

# Externe Module
import stock_data_api as stock_data
import database.handler.postgres.postgre_transactions_handler as transactions_handler
from database.handler.postgres.postgres_db_handler import add_analytics
import auth as auth_module
import database.handler.postgres.postgres_db_handler as db_handler
import database.handler.postgres.postgre_education_handler as education_handler

# Lokale Module
from ..auth_utils import get_current_user, AuthenticatedUser
from ..pydantic_models import (
    LoginRequest, TradeRequest, ProfilePictureUploadResponse, EasterEggRedeemRequest,
    StockDataPoint, AssetResponse, FunnyTip, FunnyTipsResponse,
    StatusResponse, DailyQuizResponse, UserDataResponse, TransactionsListResponse, PortfolioResponse,
    RedeemCodeRequest, RedeemCodeResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Helper für den Root-Pfad
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Authentication ---
@router.post("/login")
async def api_login(login_data: LoginRequest):
    """API-Route für die Benutzeranmeldung"""
    logger.info(f"Login attempt for email: {login_data.email}")
    try:
        firebase_uid, id_token = auth_module.login_firebase_user_rest(login_data.email, login_data.password)
        logger.info(f"Firebase authentication successful for email: {login_data.email}, UID: {firebase_uid}")

        if not firebase_uid or not id_token:
            logger.warning(f"Firebase authentication returned empty UID or token for email: {login_data.email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

        local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
        if not local_user:
            logger.info(f"No local user found with Firebase UID: {firebase_uid}, checking by email")
            local_user = db_handler.get_user_by_email(login_data.email)
            if not local_user:
                logger.info(f"Creating new local user for email: {login_data.email}")
                username = login_data.email.split('@')[0]
                if db_handler.add_user(username, login_data.email, firebase_uid):
                    local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
                else:
                    logger.error(f"Failed to create local user for email: {login_data.email}")
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user account.")
            else:
                db_handler.update_firebase_uid(local_user['id'], firebase_uid)
                local_user['firebase_uid'] = firebase_uid
        
        if not local_user:
            logger.error(f"Critical error: Could not find or create local user for email: {login_data.email}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in the local database.")

        try:
            db_handler.update_last_login(local_user['id'])
        except Exception as e:
            logger.warning(f"Failed to update last login timestamp: {e}")

        return {
            "success": True,
            "message": "Login successful.",
            "userId": local_user['id'],
            "firebase_uid": firebase_uid,
            "id_token": id_token
        }
    except ValueError as ve:
        logger.warning(f"Firebase authentication failed for email {login_data.email}: {ve}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during API login: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during login.")

# --- Stock Data ---
@router.get("/stock-data", response_model=List[StockDataPoint])
async def api_stock_data(
    symbol: str = 'AAPL',
    timeframe: str = '3M',
    fresh: bool = False,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """API-Route zum Abrufen von Aktiendaten"""
    user_id_for_analytics = current_user.id
    logger.info(f"Accessing /stock-data for user: {user_id_for_analytics}. Symbol: {symbol}, Timeframe: {timeframe}, Fresh: {fresh}")
    add_analytics(user_id_for_analytics, "api_get_stock_data", f"api_routes:api_stock_data:symbol={symbol},tf={timeframe},fresh={fresh}")

    # Zeitparameter vorbereiten
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
        # Daten abrufen
        if fresh:
            logger.info(f"Force fresh data for {symbol}, timeframe: {timeframe}")
            df = stock_data.get_stock_data(symbol, period=period_param_for_1min, interval=interval_param, 
                                         start_date=start_date_str, end_date=end_date_str)
        else:
            logger.info(f"Getting cached or live data for {symbol}, timeframe: {timeframe}")
            df = stock_data.get_cached_or_live_data(symbol, timeframe)
        
        is_demo_data = getattr(df, 'is_demo', True)
        logger.info(f"Data received for {symbol}: Demo = {is_demo_data}, Points = {len(df) if df is not None and not df.empty else 0}")

        # Fallback zu Demo-Daten falls nötig
        if df is None or df.empty:
            logger.warning(f"DataFrame for {symbol} is None or empty. Generating explicit demo data.")
            is_minutes_demo = timeframe == '1MIN'
            demo_days = (end_date_dt - start_date_dt).days if start_date_dt is not None else 90
            demo_units = 240 if is_minutes_demo else demo_days
            df = stock_data.get_demo_stock_data(symbol, demo_units, is_minutes=is_minutes_demo)
            is_demo_data = True
            
            if df is None or df.empty:
                logger.error(f"No data (including fallback demo) found for {symbol}. Returning empty list.")
                add_analytics(user_id_for_analytics, "api_get_stock_data_no_data", f"api_routes:api_stock_data:symbol={symbol}")
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={'data': [], 'is_demo': True, 'currency': 'USD', 'demo_reason': 'API key missing' if not stock_data.TWELVE_DATA_API_KEY else 'API request failed or empty data'}
                )

        # Daten konvertieren
        data = []
        if df is not None and not df.empty:
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"Data for {symbol} is missing one or more required columns. Available: {list(df.columns)}")
                add_analytics(user_id_for_analytics, "api_get_stock_data_missing_cols", f"api_routes:api_stock_data:symbol={symbol}")
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
        
        # Asset-Preis in DB aktualisieren
        if not is_demo_data and len(data) > 0 and data[-1].close is not None:
            try:
                update_asset_price_in_db(symbol, float(data[-1].close), user_id_for_analytics)
            except Exception as e:
                logger.error(f"Error updating asset price in database: {e}")
        
        add_analytics(user_id_for_analytics, "api_get_stock_data_success", f"api_routes:api_stock_data:symbol={symbol},count={len(data)}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /api/stock-data for {symbol} timeframe {timeframe}: {e}", exc_info=True)
        add_analytics(user_id_for_analytics, "api_get_stock_data_exception", f"api_routes:api_stock_data:symbol={symbol},error={e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def update_asset_price_in_db(symbol: str, price: float, user_id_for_analytics: Optional[int] = None):
    """Aktualisiert den letzten bekannten Preis eines Assets in der Datenbank"""
    add_analytics(user_id_for_analytics, "update_asset_price_start", f"api_routes:symbol={symbol}")
    try:
        with transactions_handler.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM assets WHERE symbol = %s", (symbol,))
                add_analytics(user_id_for_analytics, "update_asset_price_select_asset", f"api_routes:symbol={symbol}")
                asset_row = cur.fetchone()
                
                if not asset_row:
                    logger.warning(f"Asset mit Symbol '{symbol}' nicht gefunden, kann Preis nicht aktualisieren.")
                    return False
                
                cur.execute("""
                    UPDATE assets SET last_price = %s, last_price_updated = CURRENT_TIMESTAMP
                    WHERE symbol = %s
                """, (price, symbol))
                add_analytics(user_id_for_analytics, "update_asset_price_update_asset", f"api_routes:symbol={symbol}")
                conn.commit()
                add_analytics(user_id_for_analytics, "update_asset_price_commit", f"api_routes:symbol={symbol}")
                return True
    except Exception as e:
        add_analytics(user_id_for_analytics, "update_asset_price_error", f"api_routes:symbol={symbol},error={str(e)}")
        logger.error(f"Error updating asset price in database: {e}", exc_info=True)
        return False

# --- Trade Operations ---
@router.post("/trade/buy")
async def api_buy_stock(trade_data: TradeRequest, current_user: AuthenticatedUser = Depends(get_current_user)):
    """API-Route zum Kaufen von Aktien"""
    user_id = current_user.id
    add_analytics(user_id, "api_trade_buy_attempt", f"api_routes:api_buy_stock:symbol={trade_data.symbol},qty={trade_data.quantity},price={trade_data.price}")

    if trade_data.quantity <= 0 or trade_data.price <= 0:
        add_analytics(user_id, "api_trade_buy_fail_invalid_input", f"api_routes:api_buy_stock:symbol={trade_data.symbol},error=non-positive quantity/price")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity and price must be positive.")

    result = transactions_handler.buy_stock(user_id, trade_data.symbol, trade_data.quantity, trade_data.price)
    if result.get("success"):
        add_analytics(user_id, "api_trade_buy_success", f"api_routes:api_buy_stock:symbol={trade_data.symbol}")
        return result
    else:
        add_analytics(user_id, "api_trade_buy_fail_handler", f"api_routes:api_buy_stock:symbol={trade_data.symbol},msg={result.get('message')}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message", "Buy operation failed."))

@router.post("/trade/sell")
async def api_sell_stock(trade_data: TradeRequest, current_user: AuthenticatedUser = Depends(get_current_user)):
    """API-Route zum Verkaufen von Aktien"""
    user_id = current_user.id
    add_analytics(user_id, "api_trade_sell_attempt", f"api_routes:api_sell_stock:symbol={trade_data.symbol},qty={trade_data.quantity},price={trade_data.price}")

    if trade_data.quantity <= 0 or trade_data.price <= 0:
        add_analytics(user_id, "api_trade_sell_fail_invalid_input", f"api_routes:api_sell_stock:symbol={trade_data.symbol},error=non-positive quantity/price")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity and price must be positive.")
        
    result = transactions_handler.sell_stock(user_id, trade_data.symbol, trade_data.quantity, trade_data.price)
    if result.get("success"):
        add_analytics(user_id, "api_trade_sell_success", f"api_routes:api_sell_stock:symbol={trade_data.symbol}")
        return result
    else:
        add_analytics(user_id, "api_trade_sell_fail_handler", f"api_routes:api_sell_stock:symbol={trade_data.symbol},msg={result.get('message')}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message", "Sell operation failed."))

# --- Assets ---
@router.get("/assets", response_model=AssetResponse)
async def api_get_assets(
    type: Optional[str] = None,
    active_only: bool = True,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """API-Route zum Abrufen aller Assets"""
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_all_assets", f"api_routes:api_get_assets:type={type},active_only={active_only}")
    
    result = transactions_handler.get_all_assets(active_only, type)
    
    if result is None:
        logger.error(f"get_all_assets returned None for type={type}, active_only={active_only}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve assets data.")
    
    if result.get('success', False):
        return result
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Failed to retrieve assets."))

# --- User Data ---
@router.get("/user/{user_id_param}", response_model=UserDataResponse)
async def api_get_user_data(user_id_param: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    """API-Route zum Abrufen von Benutzerdaten"""
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_user_data_attempt", f"api_routes:api_get_user_data:user_id={user_id_param}")
    
    user_data = db_handler.get_user_by_id(user_id=user_id_param)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserDataResponse(success=True, user=user_data)

@router.get("/user/transactions/{user_id_param}", response_model=TransactionsListResponse)
async def api_get_user_last_transactions(user_id_param: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    """API-Route zum Abrufen der letzten Transaktionen eines Benutzers"""
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_user_last_transactions_attempt", f"api_routes:api_get_user_last_transactions:user_id={user_id_param}")

    transactions = transactions_handler.get_recent_transactions(user_id=user_id_param)
    if transactions is not None:
        add_analytics(user_id_for_analytics, "api_get_user_last_transactions_success", f"api_routes:api_get_user_last_transactions:user_id={user_id_param}")
        return TransactionsListResponse(success=True, transactions=transactions)
    else:
        add_analytics(user_id_for_analytics, "api_get_user_last_transactions_fail", f"api_routes:api_get_user_last_transactions:user_id={user_id_param}")
        return TransactionsListResponse(success=False, message="No transactions found or error retrieving them.", transactions=[])

@router.get("/user/portfolio/{user_id_param}", response_model=PortfolioResponse)
async def api_get_portfolio(user_id_param: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    """API-Route zum Abrufen des Portfolios eines Benutzers"""
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_portfolio", f"api_routes:api_get_portfolio:user_id={user_id_param}")

    portfolio_data = transactions_handler.show_user_portfolio(user_id_param)
    if portfolio_data and portfolio_data.get("success"):
        return portfolio_data
    else:
        message = (portfolio_data.get("message") if portfolio_data else
                  "Failed to retrieve portfolio or portfolio is empty.")
        if portfolio_data:
            return portfolio_data 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

# --- Education ---
@router.get("/daily-quiz")
async def api_get_daily_quiz(current_user: AuthenticatedUser = Depends(get_current_user)):
    """API-Route zum Abrufen des täglichen Quiz"""
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_daily_quiz", "api_routes:api_get_daily_quiz")
    today = datetime.today().strftime('%Y-%m-%d')
    return education_handler.get_daily_quiz(date=today)

# --- Funny Tips ---
@router.get("/funny-tips", response_model=FunnyTipsResponse)
async def api_get_funny_tips(current_user: AuthenticatedUser = Depends(get_current_user)):
    """API-Route zum Abrufen lustiger Tipps"""
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_funny_tips", "api_routes:api_get_funny_tips")
    tips_data = [
        {"id": 1, "tip": "Buy high, sell low. The secret to eternal brokerage fees."},
        {"id": 2, "tip": "If you don't know what you're doing, do it with conviction."},
        {"id": 3, "tip": "The market is like a box of chocolates... you never know what you're gonna get, but it's probably nuts."},
        {"id": 4, "tip": "Always diversify your portfolio: buy stocks in different shades of red."}
    ]
    return FunnyTipsResponse(success=True, tips=[FunnyTip(**tip) for tip in tips_data])

# --- Health Check ---
@router.get("/health")
async def api_health_check():
    """API-Endpunkt für den Gesundheitscheck der API"""
    return {"status": "ok", "message": "API is running."}

# --- Profile Picture ---
@router.post("/upload/profile-picture", response_model=ProfilePictureUploadResponse)
async def api_upload_profile_picture(
    file: UploadFile = File(...), 
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """API-Route zum Hochladen eines Profilbildes"""
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_upload_profile_picture_attempt", "api_routes:api_upload_profile_picture")

    if not file:
        add_analytics(user_id_for_analytics, "api_upload_profile_picture_fail_no_file_part", "api_routes:api_upload_profile_picture")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file part in the request.")
    
    if file.filename == '':
        add_analytics(user_id_for_analytics, "api_upload_profile_picture_fail_no_selected_file", "api_routes:api_upload_profile_picture")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No selected file.")

    try:
        upload_folder = os.path.join(PROJECT_ROOT, 'static', 'user_data')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        file_path = os.path.join(user_folder, "profile_picture.png")
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        profile_pic_url_path = f"user_data/{current_user.id}/profile_picture.png"
        
        logger.info(f"User {current_user.id} profile picture path to be saved in DB: {profile_pic_url_path}")
        
        add_analytics(user_id_for_analytics, "api_upload_profile_picture_success", f"api_routes:api_upload_profile_picture,url={profile_pic_url_path}")
        logger.info(f"Profile picture uploaded successfully for user {current_user.id}")
        
        return ProfilePictureUploadResponse(
            success=True, 
            message="File uploaded successfully.", 
            url=f"/static/{profile_pic_url_path}"
        )
    
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}", exc_info=True)
        add_analytics(user_id_for_analytics, "api_upload_profile_picture_exception", f"api_routes:api_upload_profile_picture,error={e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error uploading file: {str(e)}")

@router.get("/get/profile-picture/{user_id_param}")
async def api_get_profile_picture(user_id_param: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    """API-Route zum Abrufen eines Profilbildes"""
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_profile_picture_attempt", f"api_routes:api_get_profile_picture:user_id={user_id_param}")
    
    file_path = os.path.join(PROJECT_ROOT, 'static', 'user_data', str(user_id_param), 'profile_picture.png')
    
    if os.path.exists(file_path):
        add_analytics(user_id_for_analytics, "api_get_profile_picture_success", f"api_routes:api_get_profile_picture:user_id={user_id_param}")
        return FileResponse(file_path)
    else:
        add_analytics(user_id_for_analytics, "api_get_profile_picture_fail_not_found", f"api_routes:api_get_profile_picture:user_id={user_id_param}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile picture not found.")

# --- Easter Egg ---
@router.post("/easter-egg/redeem")
async def redeem_easter_egg(
    payload: EasterEggRedeemRequest,
    fastapi_req: FastAPIRequest
):
    """API-Route zum Einlösen eines Easter Egg Codes"""
    logger.info("FastAPI Easter egg redemption endpoint called")
    code = payload.code.upper()
    
    user_id: Optional[int] = None
    current_balance: float = 0.0

    reward = 0
    message = ""
    reload_page = False

    if code == "SECRETLAMBO":
        reward = 5000
        message = "Du hast einen virtuellen Lamborghini und 5000 Credits gewonnen!"
    elif code == "TOTHEMOON":
        reward = 1000
        message = "Deine Investitionen gehen TO THE MOON! +1000 Credits"
    elif code == "1337":
        reward = 1337
        message = "Retro-Gaming-Modus aktiviert! +1337 Credits"
        reload_page = True
    else:
        logger.warning(f"Invalid easter egg code: {code}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ungültiger Code")

    return {
        "success": True,
        "message": message,
        "reload": reload_page,
        "reward": reward,
    }

# --- Redeem Code ---
@router.post("/redeem-code", response_model=RedeemCodeResponse)
async def api_redeem_code(
    payload: RedeemCodeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """API-Route zum Einlösen eines Codes"""
    user_id = current_user.id
    add_analytics(user_id, "api_redeem_code_attempt", f"api_routes:api_redeem_code:code={payload.code}")
    
    code = payload.code.upper()

    user_data = db_handler.get_user_by_id(user_id)
    if not user_data:
        add_analytics(user_id, "api_redeem_code_user_not_found", f"api_routes:api_redeem_code:code={code}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benutzer nicht gefunden")
    
    current_balance = user_data.get('balance', 0.0)

    reward = 0
    message = ""
    reload_page = False

    if code == "SECRETLAMBO":
        reward = 5000; message = "Du hast einen virtuellen Lamborghini und 5000 Credits gewonnen!"
    elif code == "TOTHEMOON":
        reward = 1000; message = "Deine Investitionen gehen TO THE MOON! +1000 Credits"
    elif code == "HODLGANG":
        reward = 2500; message = "HODL! HODL! HODL! Du hast 2500 Credits für deine Diamond Hands erhalten!"
    elif code == "STONKS":
        today = datetime.now()
        if today.month == 4 and today.day == 20:
            reward = 4200; message = "STONKS! Du hast den speziellen 4/20 Code gefunden! +4200 Credits"
        else:
            reward = 420; message = "STONKS! Aber es ist nicht der richtige Tag für den vollen Bonus! +420 Credits"
    elif code == "1337":
        reward = 1337; message = "Retro-Gaming-Modus aktiviert! +1337 Credits"; reload_page = True
    else:
        add_analytics(user_id, "api_redeem_code_invalid", f"api_routes:api_redeem_code:code={code}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ungültiger Code")
        
    new_balance = current_balance + reward
    
    update_success = db_handler.update_user_balance(user_id, new_balance)
    if not update_success:
        logger.error(f"Failed to update balance for user {user_id} after redeeming code {code}")
        add_analytics(user_id, "api_redeem_code_balance_update_fail", f"api_routes:api_redeem_code:code={code}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Fehler beim Aktualisieren des Guthabens.")

    add_analytics(user_id, "api_redeem_code_success", f"api_routes:api_redeem_code:code={code},reward={reward}")
    return RedeemCodeResponse(
        success=True, message=message, reload=reload_page, reward=reward, new_balance=new_balance
    )

# Dummy route from original, can be kept or removed
@router.get("/trade/{symbol}/")
async def api_stock_data_symbol_dummy(symbol: str, current_user: AuthenticatedUser = Depends(get_current_user)):
    """Dummy-Route für Aktien-Daten"""
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_stock_data_symbol_dummy", f"api_routes:api_stock_data_symbol:symbol={symbol}")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Data for symbol {symbol} not yet implemented.")
