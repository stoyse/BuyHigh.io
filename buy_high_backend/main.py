from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

# Importiere den kombinierten Router aus dem router-Paket
from .router import router as api_router

# FastAPI-Anwendung mit Metadaten initialisieren
app = FastAPI(
    title="BuyHigh.io API",
    description="Backend API für die BuyHigh.io Trading-Plattform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS-Middleware hinzufügen, um Cross-Origin-Anfragen zu ermöglichen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion sollten spezifische Domains verwendet werden
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API-Routen unter dem Präfix /api einbinden
app.include_router(api_router, prefix="/api")

# Statische Dateien für Profilbilder usw.
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
os.makedirs(static_dir, exist_ok=True)  # Verzeichnis erstellen, falls es nicht existiert
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Root-Route für Gesundheitscheck
@app.get("/")
async def root():
    """Einfache Root-Route für API-Statusprüfung"""
    return {
        "message": "Willkommen bei der BuyHigh.io API",
        "status": "online",
        "version": "1.0.0"
    }

# Um die App mit uvicorn zu starten:
# uvicorn buy_high_backend.main:app --reload
