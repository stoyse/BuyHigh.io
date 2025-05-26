"""
Router-Paket für die BuyHigh.io FastAPI-Anwendung.
Kombiniert alle API-Router in einer einzigen Schnittstelle.
"""

import os
import logging
from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from .auth_router import router as auth_router
from .stock_router import router as stock_router
from .trade_router import router as trade_router
from .asset_router import router as asset_router
from .user_router import router as user_router
from .education_router import router as education_router
from .misc_router import router as misc_router
from .easter_egg_router import router as easter_egg_router
from .news_router import router as news_router  # Import news_router
from .gamble import router as gamble_router # Import gamble_router

# Umgebungsvariablen laden
load_dotenv()

# Debug-Logger konfigurieren
DEBUG_LOG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG_LOG_FILE = os.path.join(DEBUG_LOG_DIR, "../debug.log")
os.makedirs(os.path.dirname(DEBUG_LOG_FILE), exist_ok=True)

# Logger-Konfiguration
debug_logger = logging.getLogger("buyhigh_debug")
debug_logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(DEBUG_LOG_FILE)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
debug_logger.addHandler(file_handler)

debug_logger.info("Initializing router package (buy_high_backend.router.__init__)")

# Log routes of auth_router before inclusion
debug_logger.info(f"Routes on auth_router (id: {id(auth_router)}) BEFORE inclusion:")
for route in auth_router.routes:
    debug_logger.info(f"  Path: {route.path}, Name: {route.name}, Methods: {getattr(route, 'methods', 'N/A')}")

# Debug-Funktion für die Anwendung
def log_request_response(request: Request, message: str):
    """Loggt Anfrage- und Antwortdetails"""
    debug_logger.debug(f"{message} | Path: {request.url.path} | Method: {request.method}")

# Hauptrouter, der alle Sub-Router kombiniert
router = APIRouter()
debug_logger.info(f"Created main APIRouter instance in router.__init__: {id(router)}")

# Sub-Router einbinden
debug_logger.info(f"Including auth_router ({id(auth_router)}) into main router ({id(router)}) WITH prefix '/auth'.")
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
debug_logger.info(f"Including stock_router ({id(stock_router)}) into main router ({id(router)}) without prefix.")
router.include_router(stock_router)
debug_logger.info(f"Including trade_router ({id(trade_router)}) into main router ({id(router)}) without prefix.")
router.include_router(trade_router)
debug_logger.info(f"Including asset_router ({id(asset_router)}) into main router ({id(router)}) without prefix.")
router.include_router(asset_router)
debug_logger.info(f"Including user_router ({id(user_router)}) into main router ({id(router)}) without prefix.")
router.include_router(user_router)
debug_logger.info(f"Including education_router ({id(education_router)}) into main router ({id(router)}) without prefix.")
router.include_router(education_router)
debug_logger.info(f"Including misc_router ({id(misc_router)}) into main router ({id(router)}) without prefix.")
router.include_router(misc_router)
debug_logger.info(f"Including easter_egg_router ({id(easter_egg_router)}) into main router ({id(router)}) without prefix.")
router.include_router(easter_egg_router)
debug_logger.info(f"Including news_router ({id(news_router)}) into main router ({id(router)}) without prefix.")
router.include_router(news_router)  # Include news_router
debug_logger.info(f"Including gamble_router ({id(gamble_router)}) into main router ({id(router)}) without prefix.") # Log gamble_router
router.include_router(gamble_router) # Include gamble_router

debug_logger.info(f"Finished including sub-routers into main router ({id(router)}) in router.__init__.")

# Log routes of the main combined router (api_router)
debug_logger.info(f"Routes on main api_router (id: {id(router)}) AFTER all inclusions:")
for route in router.routes:
    debug_logger.info(f"  Path: {route.path}, Name: {route.name}, Methods: {getattr(route, 'methods', 'N/A')}")

# Middleware-Klasse (wird in main.py verwendet)
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        debug_logger.debug(f"Request: {request.method} {request.url.path}")
        response = await call_next(request)
        debug_logger.debug(f"Response: {response.status_code} for {request.url.path}")
        return response
