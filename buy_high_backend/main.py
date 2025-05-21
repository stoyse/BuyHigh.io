import os
import logging


_setup_logger = logging.getLogger("buyhigh_setup")
if not _setup_logger.hasHandlers(): # Handler nur einmal hinzufügen
    _ch = logging.StreamHandler() # Loggt auf die Konsole
    _formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    _ch.setFormatter(_formatter)
    _setup_logger.addHandler(_ch)
    _setup_logger.setLevel(logging.INFO)

# Korrekter Pfad zur Firebase-Konfigurationsdatei
# Annahme: main.py ist in buy_high_backend, utils-Ordner ist auf gleicher Ebene wie buy_high_backend
project_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # BuyHigh.io Verzeichnis
firebase_config_path = os.path.join(project_root_dir, "utils", "buyhighio-firebase-adminsdk-fbsvc-df9d657bec.json")

_setup_logger.info(f"MAIN.PY: Versuchter Pfad für Firebase-Konfig: {firebase_config_path}")

if os.path.exists(firebase_config_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = firebase_config_path
    _setup_logger.info(f"MAIN.PY: GOOGLE_APPLICATION_CREDENTIALS gesetzt auf: {firebase_config_path}")
else:
    _setup_logger.error(f"MAIN.PY: Firebase-Konfigurationsdatei NICHT gefunden unter: {firebase_config_path}")


from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Importiere den kombinierten Router und die Middleware aus dem router-Paket.
# Das debug_logger Objekt wird jetzt direkt aus dem router-Modul importiert.
from .router import router as api_router, RequestLoggingMiddleware, debug_logger as router_debug_logger

# FastAPI-Anwendung mit Metadaten initialisieren
app = FastAPI(
    title="BuyHigh.io API",
    description="Backend API für die BuyHigh.io Trading-Plattform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Definiere die erlaubten Ursprünge
allowed_origins = [
    "https://buy-high-io.vercel.app/"
]

# CORS-Middleware hinzufügen, um Cross-Origin-Anfragen zu ermöglichen
# Diese sollte vor anderen Middlewares stehen, die Antworten modifizieren oder generieren könnten.
#app.add_middleware(
#    CORSMiddleware,
#    allow_origins=[
#    "https://buy-high-io.vercel.app",
#    "https://buy-high-io.vercel.app/",], 
#    allow_credentials=True,
#    allow_methods=["*"],
#    allow_headers=["*"],
#    expose_headers=["Authorization", "Content-Disposition"],
#    max_age=600,  # Cache die CORS-Antwort für 10 Minuten
#)

# Füge die Request-Logging-Middleware hinzu
#app.add_middleware(RequestLoggingMiddleware)

# API-Routen ohne Präfix einbinden (leerer String statt "")
app.include_router(api_router, prefix="")

# Statische Dateien für Profilbilder usw.
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
os.makedirs(static_dir, exist_ok=True)  # Verzeichnis erstellen, falls es nicht existiert
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Logging-Ordner und Datei für Frontend-Logs
frontend_log_dir = os.path.join(project_root_dir, "frontend_logs")
os.makedirs(frontend_log_dir, exist_ok=True)
frontend_log_file = os.path.join(frontend_log_dir, "frontend.log")

class FrontendLogEntry(BaseModel):
    level: str
    message: str
    context: dict = {}

@app.post("/frontend-log")
async def frontend_log(entry: FrontendLogEntry, request: Request):
    client_ip = request.client.host
    log_line = f"{entry.level.upper()} | {client_ip} | {entry.message} | {entry.context}\n"
    with open(frontend_log_file, "a", encoding="utf-8") as f:
        f.write(log_line)
    return JSONResponse({"status": "ok"})

# Root-Route für Gesundheitscheck
@app.get("/")
async def root():
    """Einfache Root-Route für API-Statusprüfung"""
    router_debug_logger.debug("Root endpoint accessed")
    return {
        "message": "Willkommen bei der BuyHigh.io API",
        "status": "online",
        "version": "1.0.0"
    }


@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return Response(status_code=200)
# Um die App mit uvicorn zu starten:
# uvicorn buy_high_backend.main:app --reload
