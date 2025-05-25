from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import logging
from ..auth_utils import get_current_user, AuthenticatedUser
from ..pydantic_models import AssetResponse, AssetsListResponse, Asset
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
    news_data = fetch_general_news()
    
    # --- Temporäres Logging zur Überprüfung der Datenstruktur ---
    logger.info(f"Raw news data from fetch_general_news: {news_data[:5] if news_data else 'No data'}") # Loggt die ersten 5 Elemente
    # --- Ende temporäres Logging ---

    if not news_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No news found for any assets.")
    
    transformed_assets = []
    if isinstance(news_data, list): # Sicherstellen, dass news_data eine Liste ist
        for index, item in enumerate(news_data):
            if isinstance(item, dict): # Sicherstellen, dass jedes Element ein Dictionary ist
                # Passe die folgenden .get()-Aufrufe an die tatsächlichen Schlüssel in deinen News-Daten an
                # Es ist unwahrscheinlich, dass allgemeine Nachrichten eine 'id' oder einen 'symbol' im Sinne eines Assets haben.
                # Du musst entscheiden, welche Werte hier sinnvoll sind.
                asset = Asset(
                    id=item.get("id", index),  # Verwende Index als Fallback-ID oder einen eindeutigen Schlüssel aus item
                    symbol=item.get("symbol", item.get("source", "GENERAL")), # Beispiel: 'source' oder ein Standardwert
                    name=item.get("headline", item.get("title", "General News")), # Beispiel: 'headline' oder 'title'
                    asset_type=item.get("category", "news"), # Beispiel: 'category' oder ein Standardwert
                    default_price=item.get("price") # Falls vorhanden
                )
                transformed_assets.append(asset)
            else:
                logger.warning(f"Item in news_data is not a dictionary: {item}")
    else:
        logger.error(f"news_data is not a list as expected: {type(news_data)}")
        # Du könntest hier auch eine HTTPException auslösen, wenn das Format unerwartet ist
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected format for news data.")
            
    return AssetsListResponse(success=True, assets=transformed_assets)

