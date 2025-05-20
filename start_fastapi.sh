#!/bin/bash

# Farben für Ausgabe
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# API-Konfiguration
API_MODULE="buy_high_backend.main:app"
HOST="127.0.0.1"  # 0.0.0.0 erlaubt Zugriff von allen Netzwerkschnittstellen
PORT="9877"
WORKERS=2       # Anzahl der Worker-Prozesse (üblicherweise (2*CPU)+1)
RELOAD="--reload"  # Automatisches Neuladen bei Codeänderungen (für Entwicklung)

echo -e "${GREEN}=== BuyHigh.io API Server ===${NC}"

source venv/bin/activate

# Prüfen, ob Python und pip installiert sind
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Fehler: Python3 ist nicht installiert.${NC}"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo -e "${RED}Fehler: pip ist nicht installiert.${NC}"
    exit 1
fi

# Prüfen, ob uvicorn installiert ist
if ! command -v uvicorn &> /dev/null; then
    echo -e "${RED}Fehler: uvicorn ist nicht installiert.${NC}"
    echo -e "${YELLOW}Installiere mit: pip install uvicorn${NC}"
    pip install uvicorn
fi

# Installiere Python-Abhängigkeiten aus requirements.txt
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}Installiere Abhängigkeiten aus requirements.txt...${NC}"
    pip install -r requirements.txt
else
    echo -e "${RED}Fehler: requirements.txt nicht gefunden.${NC}"
    exit 1
fi

# Alle Prozesse beenden, die bereits den Port verwenden
echo -e "${YELLOW}Beende laufende Prozesse auf Port $PORT...${NC}"
if command -v lsof &> /dev/null; then
    lsof -ti:$PORT | xargs -r kill -9
elif command -v netstat &> /dev/null; then
    # Alternative für Systeme ohne lsof
    pid=$(netstat -tulpn 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1)
    if [ -n "$pid" ]; then
        kill -9 $pid 2>/dev/null
    fi
fi

# Umgebungsvariablen laden
echo -e "${YELLOW}Lade Umgebungsvariablen aus .env-Datei...${NC}"
if [ -f ".env" ]; then
    source .env
else
    echo -e "${YELLOW}Warnung: .env-Datei nicht gefunden. Fahre ohne Umgebungsvariablen fort.${NC}"
fi

# Verzeichnisstruktur prüfen
if [ ! -d "buy_high_backend" ]; then
    echo -e "${RED}Fehler: Verzeichnis 'buy_high_backend' nicht gefunden.${NC}"
    echo -e "${YELLOW}Stellen Sie sicher, dass Sie das Skript im Hauptverzeichnis des Projekts ausführen.${NC}"
    exit 1
fi

# Starte API-Server
echo -e "${GREEN}Starte FastAPI-Server auf http://$HOST:$PORT ...${NC}"
echo -e "${YELLOW}Drücken Sie STRG+C, um den Server zu beenden.${NC}"

# Wenn PRODUCTION gesetzt ist, deaktiviere auto-reload
if [ "$ENVIRONMENT" = "production" ]; then
    RELOAD=""
    echo -e "${YELLOW}Produktionsmodus: Auto-Reload deaktiviert${NC}"
fi

# API starten
uvicorn $API_MODULE --host $HOST --port $PORT --workers $WORKERS $RELOAD --log-level info

# Wenn der Server beendet wird, zeige eine Meldung
echo -e "${RED}Server wurde beendet.${NC}"
exit 0
