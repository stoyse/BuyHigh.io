from fastapi import APIRouter, Depends
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from database.handler.postgres.postgres_db_handler import update_user_balance, get_user_by_id
from ..auth_utils import get_current_user, AuthenticatedUser

class CoinFlipResult(BaseModel):
    Success: bool
    bet: int
    profit: int

router = APIRouter()

@router.get("/gamble/test", tags=["Gamble"])
async def test_gamble_route():
    return {"message": "Gamble router test successful"}

@router.post("/gamble/coinflip", tags=["Gamble"])
async def record_coin_flip_result(result: CoinFlipResult, current_user: AuthenticatedUser = Depends(get_current_user)):
    success = result.Success
    bet = result.bet
    profit = result.profit
    
    # Hole die aktuelle Balance aus der Datenbank
    user_data = get_user_by_id(current_user.id)
    if not user_data:
        return {
            "status": "error",
            "message": "User not found",
            "balance_updated": False
        }
    
    current_balance = user_data.get('balance', 0) if user_data else 0
    
    # Berechne neuen Balance basierend auf dem Ergebnis
    if success:
        new_balance = current_balance + profit
    else:
        new_balance = current_balance - bet
    
    # Verhindere negative Balance
    if new_balance < 0:
        return {
            "status": "error",
            "message": "Insufficient balance for bet",
            "current_balance": current_balance,
            "balance_updated": False
        }
    
    # Aktualisiere die Balance in der Datenbank
    update_success = update_user_balance(current_user.id, new_balance)
    
    if update_success:
        return {
            "status": "success", 
            "received_data": result,
            "old_balance": current_balance,
            "new_balance": new_balance,
            "balance_updated": True
        }
    else:
        return {
            "status": "error",
            "message": "Failed to update user balance",
            "balance_updated": False
        }

