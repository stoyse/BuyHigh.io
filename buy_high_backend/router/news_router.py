from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import logging
from ..auth_utils import get_current_user, AuthenticatedUser
from ..pydantic_models import AssetResponse, AssetsListResponse
from utils.stock_news import fetch_company_news, fetch_general_news


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/news/{symbol}/")
async def api_news_for_asset(
    symbol: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AssetResponse:
    """API route to get news for a specific asset by symbol."""
    user_id = current_user.id
    news = fetch_company_news(symbol, from_date, to_date)
    
    if not news:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No news found for asset {symbol}.")
    
    return AssetResponse(symbol=symbol, news=news)

@router.get("/news/")
async def api_news():
    """API route to get news for all assets."""
    news = fetch_general_news()
    
    if not news:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No news found for any assets.")
    
    return AssetsListResponse(assets=news)

