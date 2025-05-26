from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..auth_utils import get_current_user, AuthenticatedUser
from ...database.handler.postgres.postgres_db_handler import update_user_balance

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
    succes = result.Success
    bet = result.bet
    profit = result.profit
    update_user_balance()
    return {"status": "success", "received_data": result}

