"""
Router für Easter-Egg und Code-Einlösungsfunktionen.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request as FastAPIRequest
from typing import Optional
from datetime import datetime
import logging
import database.handler.postgres.postgres_db_handler as db_handler
from database.handler.postgres.postgres_db_handler import add_analytics
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
    
    # Stark vereinfachte Version ohne Benutzerauthentifizierung
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

@router.post("/redeem-code", response_model=RedeemCodeResponse)
async def api_redeem_code(
    payload: RedeemCodeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
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

    # Code-Logik wie im Original
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
