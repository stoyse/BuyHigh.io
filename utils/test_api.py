#!/usr/bin/env python3
"""
Python-Script zum Testen der FastAPI-API-Endpunkte.
Kompatibel mit der modularen Router-Struktur.
"""

import os
import time
import json
import requests
import sys
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List, Tuple

# Konstanten
#BASE_URL = "https://stoyse.hackclub.app/"  # Remote API-URL
BASE_URL = "http://localhost:9876/"

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
    
    id_token = None
    
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
        for token_field in ['id_token', 'firebase_token', 'access_token']:
            if token_field in login_response:
                id_token = login_response[token_field]
                break
    
    # --- Tests für geschützte Routen ---
    print_section("Tests für geschützte Routen")
    
    if id_token:
        stock_data_response = test_route("GET", "/api/stock-data?symbol=AAPL&timeframe=3M", 200, token=id_token)
        test_results.append(("Stock Data", isinstance(stock_data_response, list)))
        
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
