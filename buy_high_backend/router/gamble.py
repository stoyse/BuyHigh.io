from fastapi import APIRouter, Depends
from pydantic import BaseModel
import sys
import os
import random
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from database.handler.postgres.postgres_db_handler import update_user_balance, get_user_by_id
from ..auth_utils import get_current_user, AuthenticatedUser

class CoinFlipResult(BaseModel):
    Success: bool
    bet: int
    profit: int

class SlotsRequest(BaseModel):
    bet: int

class SlotsResult(BaseModel):
    Success: bool
    bet: int
    profit: int
    symbols: list[str]  # Die drei Symbole des Slots-Ergebnisses
    multiplier: float   # Der Multiplikator für den Gewinn

router = APIRouter()

# Slots symbols and their weights (higher weight = more common)
# Adjusted for higher win probability
SLOTS_SYMBOLS = {
    "🍒": {"weight": 40, "multiplier": 2},   # Cherry - very common, low payout
    "🍋": {"weight": 35, "multiplier": 3},   # Lemon - more common
    "🍊": {"weight": 30, "multiplier": 4},   # Orange - common
    "🍇": {"weight": 25, "multiplier": 5},   # Grapes - fairly common
    "⭐": {"weight": 15, "multiplier": 8},    # Star - less rare, high payout
    "💎": {"weight": 5, "multiplier": 20}     # Diamond - rare but more common, highest payout
}

def get_weighted_symbol():
    """Get a random symbol based on weights"""
    symbols = list(SLOTS_SYMBOLS.keys())
    weights = [SLOTS_SYMBOLS[symbol]["weight"] for symbol in symbols]
    return random.choices(symbols, weights=weights)[0]

def calculate_slots_win(reels: list[str], bet: int) -> tuple[int, int]:
    """Calculate win amount and multiplier for slots result"""
    # Count occurrences of each symbol
    symbol_counts = {}
    for symbol in reels:
        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
    
    # Check for winning combinations
    max_count = max(symbol_counts.values())
    is_win = max_count >= 2  # Win if any symbol appears 2 or more times
    multiplier = 0
    win_amount = 0
    
    if is_win:
        # Find the symbol with the highest count
        for symbol, count in symbol_counts.items():
            if count >= 3:  # 3 matching symbols = full payout
                multiplier = SLOTS_SYMBOLS[symbol]["multiplier"]
                win_amount = bet * multiplier
                break
            elif count == 2:  # 2 matching symbols = half payout
                multiplier = SLOTS_SYMBOLS[symbol]["multiplier"] * 0.5
                win_amount = int(bet * multiplier)
                break
    
    return win_amount, multiplier

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
    
    # Validiere den Einsatz gegen die aktuelle Balance
    if bet > current_balance:
        return {
            "status": "error",
            "message": "Insufficient balance for bet",
            "current_balance": current_balance,
            "balance_updated": False
        }
    
    # Berechne neuen Balance basierend auf dem Ergebnis
    if success:
        new_balance = current_balance + profit
    else:
        new_balance = current_balance - bet
    
    # Verhindere negative Balance (sollte durch vorherige Validierung bereits abgefangen sein)
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

@router.post("/gamble/slots", tags=["Gamble"])
async def record_slots_result(result: SlotsResult, current_user: AuthenticatedUser = Depends(get_current_user)):
    success = result.Success
    bet = result.bet
    profit = result.profit
    symbols = result.symbols
    multiplier = result.multiplier
    
    # Hole die aktuelle Balance aus der Datenbank
    user_data = get_user_by_id(current_user.id)
    if not user_data:
        return {
            "status": "error",
            "message": "User not found",
            "balance_updated": False
        }
    
    current_balance = user_data.get('balance', 0) if user_data else 0
    
    # Validiere den Einsatz gegen die aktuelle Balance
    if bet > current_balance:
        return {
            "status": "error",
            "message": "Insufficient balance for bet",
            "current_balance": current_balance,
            "balance_updated": False
        }
    
    # Berechne neuen Balance basierend auf dem Ergebnis
    if success:
        new_balance = current_balance + profit
    else:
        new_balance = current_balance - bet
    
    # Verhindere negative Balance (sollte durch vorherige Validierung bereits abgefangen sein)
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
            "balance_updated": True,
            "game_result": {
                "symbols": symbols,
                "multiplier": multiplier,
                "won": success,
                "payout": profit if success else 0
            }
        }
    else:
        return {
            "status": "error",
            "message": "Failed to update user balance",
            "balance_updated": False
        }

@router.post("/gamble/slots/play", tags=["Gamble"])
async def play_slots(request: SlotsRequest, current_user: AuthenticatedUser = Depends(get_current_user)):
    """Play slots game - server calculates the result"""
    bet = request.bet
    
    # Hole die aktuelle Balance aus der Datenbank
    user_data = get_user_by_id(current_user.id)
    if not user_data:
        return {
            "status": "error",
            "message": "User not found",
            "balance_updated": False
        }
    
    current_balance = user_data.get('balance', 0) if user_data else 0
    
    # Validiere den Einsatz gegen die aktuelle Balance
    if bet > current_balance:
        return {
            "status": "error",
            "message": "Insufficient balance for bet",
            "current_balance": current_balance,
            "balance_updated": False
        }
    
    if bet <= 0:
        return {
            "status": "error",
            "message": "Bet must be positive",
            "current_balance": current_balance,
            "balance_updated": False
        }
    
    # Generiere 3 zufällige Symbole
    symbols = [get_weighted_symbol() for _ in range(3)]
    
    # Berechne Gewinn
    win_amount, multiplier = calculate_slots_win(symbols, bet)
    is_win = win_amount > 0
    
    # Berechne neue Balance
    if is_win:
        new_balance = current_balance + win_amount
        profit = win_amount
    else:
        new_balance = current_balance - bet
        profit = 0
    
    # Aktualisiere die Balance in der Datenbank
    update_success = update_user_balance(current_user.id, new_balance)
    
    if update_success:
        return {
            "status": "success",
            "old_balance": current_balance,
            "new_balance": new_balance,
            "balance_updated": True,
            "game_result": {
                "symbols": symbols,
                "multiplier": multiplier,
                "won": is_win,
                "bet": bet,
                "profit": profit,
                "payout": win_amount
            }
        }
    else:
        return {
            "status": "error",
            "message": "Failed to update user balance",
            "balance_updated": False
        }

