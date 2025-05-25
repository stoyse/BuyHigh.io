import os
import sys # Add sys import
import logging

# Calculate project_root_dir
# This should be /Users/julianstosse/Developer/BuyHigh.io
project_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add project_root_dir to sys.path if it's not already there
# This should be done before other project-specific imports if they rely on this path
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)

_setup_logger = logging.getLogger("buyhigh_setup")
if not _setup_logger.hasHandlers(): # Only add handler once
    _ch = logging.StreamHandler() # Logs to console
    _formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    _ch.setFormatter(_formatter)
    _setup_logger.addHandler(_ch)
    _setup_logger.setLevel(logging.INFO)

# Correct path to Firebase config file
# Assumption: main.py is in buy_high_backend, utils folder is at the same level as buy_high_backend
firebase_config_path = os.path.join(project_root_dir, "utils", "buyhighio-firebase-adminsdk-fbsvc-df9d657bec.json")

_setup_logger.info(f"MAIN.PY: Attempted path for Firebase config: {firebase_config_path}")

if os.path.exists(firebase_config_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = firebase_config_path
    _setup_logger.info(f"MAIN.PY: GOOGLE_APPLICATION_CREDENTIALS set to: {firebase_config_path}")
else:
    _setup_logger.error(f"MAIN.PY: Firebase config file NOT found at: {firebase_config_path}")


from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import the combined router and middleware from the router package.
# The debug_logger object is now directly imported from the router module.
from .router import router as api_router, RequestLoggingMiddleware, debug_logger as router_debug_logger

# Initialize FastAPI application with metadata
app = FastAPI(
    title="BuyHigh.io API",
    description="Backend API for the BuyHigh.io trading platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

_setup_logger.info(f"MAIN.PY: FastAPI app instance created: {id(app)}")

# Define allowed origins
allowed_origins = [
    "https://buy-high-io.vercel.app/"
]

# CORS middleware to enable cross-origin requests
# This should be placed before other middlewares that modify or generate responses.
#app.add_middleware(
#    CORSMiddleware,
#    allow_origins=[
#    "https://buy-high-io.vercel.app",
#    "https://buy-high-io.vercel.app/",], 
#    allow_credentials=True,
#    allow_methods=["*"],
#    allow_headers=["*"],
#    expose_headers=["Authorization", "Content-Disposition"],
#    max_age=600,  # Cache the CORS response for 10 minutes
#)

# Add the request logging middleware
#app.add_middleware(RequestLoggingMiddleware)

_setup_logger.info(f"MAIN.PY: Attempting to include api_router (id: {id(api_router)}) from buy_high_backend.router into app (id: {id(app)}) with prefix=''.")
# Include API routes without prefix (empty string instead of "")
app.include_router(api_router, prefix="")
_setup_logger.info(f"MAIN.PY: Successfully included api_router into app.")

# Static files for profile pictures, etc.
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
os.makedirs(static_dir, exist_ok=True)  # Create directory if it doesn't exist
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Logging folder and file for frontend logs
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

# Root route for health check
@app.get("/")
async def root():
    """Simple root route for API status check"""
    router_debug_logger.debug("Root endpoint accessed")
    return {
        "message": "Welcome to the BuyHigh.io API",
        "status": "online",
        "version": "1.0.0"
    }

# Temporarily commented out for debugging POST 405 issue
# @app.options("/{rest_of_path:path}")
# async def preflight_handler(rest_of_path: str):
#     return Response(status_code=200)

# To start the app with uvicorn:
# uvicorn buy_high_backend.main:app --reload
