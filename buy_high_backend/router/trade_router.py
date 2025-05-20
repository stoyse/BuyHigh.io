"""
Router für Handelsfunktionalität (Kaufen/Verkaufen).
"""

from fastapi import APIRouter, Depends, HTTPException, status
import logging
import database.handler.postgres.postgre_transactions_handler as transactions_handler
from database.handler.postgres.postgres_db_handler import add_analytics
from ..auth_utils import get_current_user, AuthenticatedUser
from ..pydantic_models import TradeRequest

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/trade/buy")
async def api_buy_stock(trade_data: TradeRequest, current_user: AuthenticatedUser = Depends(get_current_user)):
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

@router.get("/trade/{symbol}/")
async def api_stock_data_symbol_dummy(symbol: str, current_user: AuthenticatedUser = Depends(get_current_user)):
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_stock_data_symbol_dummy", f"api_routes:api_stock_data_symbol:symbol={symbol}")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Data for symbol {symbol} not yet implemented.")
