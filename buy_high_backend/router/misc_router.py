"""
Router for various smaller features.
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import logging
import utils.stock_data_api as stock_data
from ..auth_utils import get_current_user, AuthenticatedUser
from ..pydantic_models import FunnyTip, FunnyTipsResponse, StatusResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/funny-tips", response_model=FunnyTipsResponse)
async def api_get_funny_tips(current_user: AuthenticatedUser = Depends(get_current_user)):
    tips_data = [
        {"id": 1, "tip": "Buy high, sell low. The secret to eternal brokerage fees."},
        {"id": 2, "tip": "If you don't know what you're doing, do it with conviction."},
        {"id": 3, "tip": "The market is like a box of chocolates... you never know what you're gonna get, but it's probably nuts."},
        {"id": 4, "tip": "Always diversify your portfolio: buy stocks in different shades of red."}
    ]
    return FunnyTipsResponse(success=True, tips=[FunnyTip(**tip) for tip in tips_data])

@router.get("/status", response_model=StatusResponse)
async def api_status(current_user: AuthenticatedUser = Depends(get_current_user)):
    return StatusResponse(
        api_key_configured=bool(stock_data.TWELVE_DATA_API_KEY),
        timestamp=datetime.now().isoformat()
    )

@router.get("/health")
async def api_health_check():
    return {"status": "ok", "message": "API is running."}
