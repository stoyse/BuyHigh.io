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
            if not isinstance(item, dict): # Sicherstellen, dass jedes Element ein Dictionary ist
                logger.warning(f"Item in news_data is not a dictionary and will be skipped: {item}")
                continue

            # ID - Finnhub 'id' ist normalerweise ein Integer. Fallback auf Index.
            asset_id_val = item.get("id")
            asset_id = asset_id_val if isinstance(asset_id_val, int) else index

            # Symbol - aus 'source' von Finnhub, da 'symbol' für allgemeine Nachrichten unwahrscheinlich ist.
            # Sicherstellen, dass es ein String ist und einen robusten Fallback bieten.
            source_val = item.get("source")
            asset_symbol = str(source_val) if source_val is not None and source_val != "" else f"NEWS_SRC_{asset_id}"

            # Name - aus 'headline' von Finnhub.
            # Sicherstellen, dass es ein String ist und einen robusten Fallback bieten.
            headline_val = item.get("headline")
            asset_name = str(headline_val) if headline_val is not None and headline_val != "" else f"Untitled News {asset_id}"

            # Asset Type - aus 'category' von Finnhub.
            # Frontend erwartet Kleinschreibung. Sicherstellen, dass es ein String ist.
            category_val = item.get("category")
            asset_category = str(category_val).lower() if category_val is not None and category_val != "" else "general"
            
            # Default Price (Optional[float])
            price_val = item.get("price") # 'price' ist kein Standardfeld in Finnhub general_news
            asset_default_price = None
            if price_val is not None:
                try:
                    asset_default_price = float(price_val)
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert price '{price_val}' to float for item id {asset_id}.")
                    asset_default_price = None
            
            try:
                asset = Asset(
                    id=asset_id,
                    symbol=asset_symbol,
                    name=asset_name,
                    asset_type=asset_category,
                    default_price=asset_default_price
                )
                transformed_assets.append(asset)
            except Exception as e: # Fängt Pydantic ValidationErrors und andere Fehler bei der Instanzerstellung ab
                logger.error(f"Failed to create Asset instance for item (id/index {asset_id}). Error: {e}")
                logger.error(f"Data used: id={asset_id}, symbol='{asset_symbol}', name='{asset_name}', asset_type='{asset_category}', default_price={asset_default_price}")
                logger.error(f"Original item from Finnhub: {item}")
                # Hier könnten Sie entscheiden, das fehlerhafte Element zu überspringen oder einen Platzhalter hinzuzufügen
    else:
        logger.error(f"news_data is not a list as expected: {type(news_data)}")
        # Du könntest hier auch eine HTTPException auslösen, wenn das Format unerwartet ist
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected format for news data.")
            
    return AssetsListResponse(success=True, assets=transformed_assets)

