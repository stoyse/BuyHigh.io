"""
Router-Paket für die BuyHigh.io FastAPI-Anwendung.
Kombiniert alle API-Router in einer einzigen Schnittstelle.
"""

from fastapi import APIRouter
from .auth_router import router as auth_router
from .stock_router import router as stock_router
from .trade_router import router as trade_router
from .asset_router import router as asset_router
from .user_router import router as user_router
from .education_router import router as education_router
from .misc_router import router as misc_router
from .easter_egg_router import router as easter_egg_router

# Hauptrouter, der alle Sub-Router kombiniert
router = APIRouter()

# Sub-Router einbinden
router.include_router(auth_router)
router.include_router(stock_router)
router.include_router(trade_router)
router.include_router(asset_router)
router.include_router(user_router)
router.include_router(education_router)
router.include_router(misc_router)
router.include_router(easter_egg_router)
