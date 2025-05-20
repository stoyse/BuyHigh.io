#!/usr/bin/env python3
"""
Python-Script zum Testen der FastAPI-API-Endpunkte.
Kompatibel mit der modularen Router-Struktur.
"""

import os
import time
import json
import subprocess
import requests
import sys
import signal
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List, Tuple

# Konstanten
APP_MODULE = "buy_high_backend.main:app"
HOST = "127.0.0.1"
PORT = 8000
BASE_URL = f"http://{HOST}:{PORT}"

# Farben für die Ausgabe
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BLUE = "\033[94m"
BOLD = "\033[1m"

def print_color(message: str, color: str = RESET):
    """Gibt eine farbige Nachricht aus."""
    print(f"{color}{message}{RESET}")

def print_section(title: str):
    """Gibt einen Abschnittstitel aus."""
    print_color(f"\n{BOLD}{'='*30}{RESET}")
    print_color(f"{BOLD}{BLUE}{title}{RESET}")
    print_color(f"{BOLD}{'='*30}{RESET}\n")

def load_env_vars() -> Dict[str, str]:
    """Lädt die Umgebungsvariablen aus der .env-Datei."""
    load_dotenv()
    return {
        "Username": os.getenv("Username"),
        "Password": os.getenv("Password")
    }

def start_server() -> subprocess.Popen:
    """Startet den Uvicorn-Server in einem separaten Prozess."""
    print_color(f"Starte FastAPI-Anwendung auf {BASE_URL}...", BLUE)
    
    # Setze Umgebungsvariable für den Fall dass DEBUG-Logging aktiviert werden soll
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    server = subprocess.Popen([
        sys.executable, "-m", "uvicorn", APP_MODULE, 
        "--host", HOST, "--port", str(PORT), "--reload"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    
    # Warte, bis der Server gestartet ist
    print_color("Warte auf Serverstart...", BLUE)
    
    # Ping the server until it's ready
    ready = False
    for _ in range(10):  # Try for 10 seconds
        time.sleep(1)
        try:
            # Try to access the health endpoint to check if server is running
            response = requests.get(f"{BASE_URL}/api/health", timeout=1)
            if response.status_code == 200:
                print_color("Server ist gestartet und antwortet auf Anfragen.", GREEN)
                ready = True
                break
        except requests.exceptions.RequestException:
            print_color("Server noch nicht bereit, warte weiter...", YELLOW)
    
    if not ready:
        print_color("Server konnte nicht innerhalb der Zeitbegrenzung gestartet werden.", RED)
        # Optional: Show stderr to help diagnose startup issues
        stderr_output = server.stderr.read().decode('utf-8') if server.stderr else "No stderr output"
        print_color(f"Server stderr output:\n{stderr_output}", RED)
        server.terminate()
        sys.exit(1)
    
    return server

def test_route(method: str, route: str, expected_status: int, data: Optional[Dict] = None, 
               token: Optional[str] = None, detailed: bool = True) -> Dict:
    """
    Testet eine API-Route und gibt die Antwort zurück.
    
    :param method: HTTP-Methode (GET, POST)
    :param route: API-Route (z.B. "/api/health")
    :param expected_status: Erwarteter HTTP-Statuscode
    :param data: JSON-Daten für die Anfrage (optional)
    :param token: Auth-Token für geschützte Routen (optional)
    :param detailed: Wenn True, werden Details der API-Anfrage und -Antwort ausgegeben
    :return: Dictionary mit Antwortdaten
    """
    url = f"{BASE_URL}{route}"
    print_color(f"Teste {method} {url}", BLUE)
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    start_time = time.time()
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            raise ValueError(f"Unbekannte Methode: {method}")
        
        request_time = time.time() - start_time
        
        # Prüfe den Statuscode
        if response.status_code == expected_status:
            print_color(f"✅ {method} {route} lieferte erwarteten Status {expected_status} in {request_time:.2f}s", GREEN)
        else:
            print_color(f"❌ {method} {route} lieferte Status {response.status_code} (erwartet: {expected_status}) in {request_time:.2f}s", RED)
        
        # Versuche, die Antwort als JSON zu parsen
        try:
            response_data = response.json()
            if detailed:
                print_color("Empfangene Daten:", YELLOW)
                # Für große JSON-Strukturen nur einen Teil anzeigen
                response_str = json.dumps(response_data, indent=2)
                if len(response_str) > 1000:
                    # Zeige nur die ersten 1000 Zeichen
                    response_str = response_str[:1000] + "...\n(gekürzt)"
                print_color(response_str, RESET)
            return response_data
        except json.JSONDecodeError:
            print_color("Antwort ist kein gültiges JSON.", YELLOW)
            if detailed:
                text_response = response.text
                if len(text_response) > 1000:
                    text_response = text_response[:1000] + "...\n(gekürzt)"
                print_color(f"Empfangene Daten (Text): {text_response}", RESET)
            return {"text": response.text}
            
    except requests.exceptions.RequestException as e:
        print_color(f"❌ Fehler bei {method} {route}: {e}", RED)
        return {"error": str(e)}

def run_tests() -> List[Tuple[str, bool]]:
    """Führt alle Tests aus und gibt eine Liste mit Testergebnissen zurück"""
    test_results = []
    
    # Lade Umgebungsvariablen
    env_vars = load_env_vars()
    if not env_vars["Username"] or not env_vars["Password"]:
        print_color("Warnung: Username oder Password fehlen in der .env-Datei.", YELLOW)
    
    # Starte den Server
    server = start_server()
    id_token = None
    
    try:
        # --- Basistests ---
        print_section("Basis-Tests")
        
        # Test der Root-Route
        root_response = test_route("GET", "/", 200)
        test_results.append(("Root Route", "status" in root_response))
        
        # Test des Gesundheitschecks
        health_response = test_route("GET", "/api/health", 200)
        test_results.append(("Health Check", "status" in health_response))
        
        # --- Login-Test ---
        print_section("Login-Test")
        
        # Test mit gültigen Anmeldedaten
        print_color(f"Versuche Login mit Anmeldedaten aus .env: {env_vars['Username']}", BLUE)
        login_data = {
            "email": env_vars["Username"],
            "password": env_vars["Password"]
        }
        login_response = test_route("POST", "/api/login", 200, login_data)
        login_success = login_response.get("success", False)
        test_results.append(("Login", login_success))
        
        # Extrahiere Token aus der Login-Antwort
        if login_success:
            print_color("Verfügbare Felder in der Login-Antwort:", BLUE)
            print_color(json.dumps(list(login_response.keys()), indent=2), RESET)
            
            # Versuche verschiedene Felder für das Token
            for token_field in ['id_token', 'firebase_token', 'access_token']:
                if token_field in login_response:
                    id_token = login_response[token_field]
                    print_color(f"🔑 Token aus Feld '{token_field}' extrahiert: {id_token[:15]}... (gekürzt)", GREEN)
                    break
        
        # --- Tests für geschützte Routen ---
        print_section("Tests für geschützte Routen")
        
        if id_token:
            print_color("Teste geschützte Routen mit Token...", BLUE)
            
            # Teste Stock Data
            stock_data_response = test_route("GET", "/api/stock-data?symbol=AAPL&timeframe=3M", 200, token=id_token)
            test_results.append(("Stock Data", isinstance(stock_data_response, list)))
            
            # Teste Funny Tips
            funny_tips_response = test_route("GET", "/api/funny-tips", 200, token=id_token)
            funny_tips_success = isinstance(funny_tips_response, dict) and funny_tips_response.get("success", False)
            test_results.append(("Funny Tips", funny_tips_success))
        else:
            print_color("⚠️ Kein Token extrahiert, überspringe Tests für geschützte Routen.", YELLOW)
            test_results.append(("Stock Data", None))
            test_results.append(("Funny Tips", None))
        
        # --- Test für fehlschlagenden Login ---
        print_section("Test für fehlschlagenden Login")
        
        invalid_login_data = {
            "email": "ungueltig@example.com", 
            "password": "falschespasswort123"
        }
        invalid_login_response = test_route("POST", "/api/login", 401, invalid_login_data)
        invalid_login_expected = "success" not in invalid_login_response or not invalid_login_response["success"]
        test_results.append(("Invalid Login", invalid_login_expected))
        
    finally:
        # Beende den Server
        print_color("\nBeende den Server...", BLUE)
        try:
            # Send SIGTERM for graceful shutdown
            server.send_signal(signal.SIGTERM)
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If server doesn't terminate gracefully, force kill
            server.kill()
            server.wait()
        print_color("Server gestoppt.", GREEN)
    
    return test_results

def main():
    """Hauptfunktion zum Testen der API."""
    print_section("API-Tests")
    
    try:
        test_results = run_tests()
        
        # Zusammenfassung der Tests ausgeben
        print_section("Testergebnisse")
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for name, result in test_results:
            if result is None:
                print_color(f"⚠️ {name}: ÜBERSPRUNGEN", YELLOW)
                skip_count += 1
            elif result:
                print_color(f"✅ {name}: ERFOLGREICH", GREEN)
                success_count += 1
            else:
                print_color(f"❌ {name}: FEHLGESCHLAGEN", RED)
                fail_count += 1
        
        print_section("Zusammenfassung")
        print_color(f"Durchgeführte Tests: {len(test_results)}", BLUE)
        print_color(f"✅ Erfolgreich: {success_count}", GREEN)
        print_color(f"⚠️ Übersprungen: {skip_count}", YELLOW)
        print_color(f"❌ Fehlgeschlagen: {fail_count}", RED)
        
        if fail_count > 0:
            sys.exit(1)  # Beende mit Fehlercode, wenn Tests fehlgeschlagen sind
        
    except KeyboardInterrupt:
        print_color("\nTests durch Benutzer abgebrochen.", YELLOW)
        sys.exit(130)  # Standard-Exit-Code für SIGINT (Ctrl+C)
    except Exception as e:
        print_color(f"\nUnerwarteter Fehler: {str(e)}", RED)
        sys.exit(1)
    
    print_color("\nTest abgeschlossen.", GREEN)

if __name__ == "__main__":
    main()
