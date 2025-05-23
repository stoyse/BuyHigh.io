"""
Router for Easter egg and code redemption functions.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request as FastAPIRequest
from typing import Optional
from datetime import datetime
import logging
import database.handler.postgres.postgres_db_handler as db_handler
from ..auth_utils import get_current_user, AuthenticatedUser
from ..pydantic_models import EasterEggRedeemRequest, RedeemCodeRequest, RedeemCodeResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/easter-egg/redeem")
async def redeem_easter_egg(
    payload: EasterEggRedeemRequest,
    fastapi_req: FastAPIRequest
):
    logger.info("FastAPI Easter egg redemption endpoint called")
    code = payload.code.upper()
    
    # Strongly simplified version without user authentication
    user_id: Optional[int] = None
    current_balance: float = 0.0
    
    reward = 0
    message = ""
    reload_page = False

    if code == "SECRETLAMBO":
        reward = 5000
        message = "You won a virtual Lamborghini and 5000 credits!"
    elif code == "TOTHEMOON":
        reward = 1000
        message = "Your investments are going TO THE MOON! +1000 credits"
    elif code == "1337":
        reward = 1337
        message = "Retro gaming mode activated! +1337 credits"
        reload_page = True
    else:
        logger.warning(f"Invalid easter egg code: {code}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
    
    return {
        "success": True,
        "message": message,
        "reload": reload_page,
        "reward": reward,
    }

@router.post("/redeem-code", response_model=RedeemCodeResponse)
async def api_redeem_code(
    payload: RedeemCodeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    user_id = current_user.id
    
    code = payload.code.upper()

    user_data = db_handler.get_user_by_id(user_id)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    current_balance = user_data.get('balance', 0.0)

    reward = 0
    message = ""
    reload_page = False

    # Code logic as in the original
    if code == "SECRETLAMBO":
        reward = 5000; message = "You won a virtual Lamborghini and 5000 credits!"
    elif code == "TOTHEMOON":
        reward = 1000; message = "Your investments are going TO THE MOON! +1000 credits"
    elif code == "HODLGANG":
        reward = 2500; message = "HODL! HODL! HODL! You received 2500 credits for your diamond hands!"
    elif code == "STONKS":
        today = datetime.now()
        if today.month == 4 and today.day == 20:
            reward = 4200; message = "STONKS! You found the special 4/20 code! +4200 credits"
        else:
            reward = 420; message = "STONKS! But it's not the right day for the full bonus! +420 credits"
    elif code == "1337":
        reward = 1337; message = "Retro gaming mode activated! +1337 credits"; reload_page = True
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
        
    new_balance = current_balance + reward
    
    update_success = db_handler.update_user_balance(user_id, new_balance)
    if not update_success:
        logger.error(f"Failed to update balance for user {user_id} after redeeming code {code}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating balance.")

    return RedeemCodeResponse(
        success=True, message=message, reload=reload_page, reward=reward, new_balance=new_balance
    )
