"""
Router für Asset-Verwaltung.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import logging
import database.handler.postgres.postgre_transactions_handler as transactions_handler
from database.handler.postgres.postgres_db_handler import add_analytics
from ..auth_utils import get_current_user, AuthenticatedUser
from ..pydantic_models import AssetResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/assets", response_model=AssetResponse)
async def api_get_assets(
    type: Optional[str] = None,
    active_only: bool = True,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_all_assets", f"api_routes:api_get_assets:type={type},active_only={active_only}")
    
    result = transactions_handler.get_all_assets(active_only, type)
    
    if result is None:
        logger.error(f"get_all_assets returned None for type={type}, active_only={active_only}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve assets data.")
    
    if result.get('success', False):
        return result  # FastAPI wird die Antwort gegen AssetResponse validieren
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Failed to retrieve assets."))

@router.get("/assets/{symbol}", response_model=AssetResponse)
async def api_get_asset(symbol: str, current_user: AuthenticatedUser = Depends(get_current_user)):
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_asset_by_symbol", f"api_routes:api_get_asset:symbol={symbol}")
    result = transactions_handler.get_asset_by_symbol(symbol)
    
    if result and result.get('success') and 'asset' in result and result['asset']:
        # Original logic to remove certain fields and set default_price
        if 'last_price' in result['asset']:
            del result['asset']['last_price']
        if 'last_price_updated' in result['asset']:
            del result['asset']['last_price_updated']
        if 'default_price' not in result['asset'] or result['asset']['default_price'] is None:
            logger.warning(f"Asset {symbol} has no default_price set! Using fallback.")
            result['asset']['default_price'] = 100.0
        return result # FastAPI validates against AssetResponse
    elif result and not result.get('success'):
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("message", "Asset not found."))
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
