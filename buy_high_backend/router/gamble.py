from fastapi import APIRouter

router = APIRouter()

@router.get("/gamble/test", tags=["Gamble"])
async def test_gamble_route():
    return {"message": "Gamble router test successful"}