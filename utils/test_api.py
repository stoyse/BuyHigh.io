#!/usr/bin/env python3
"""
Python script for testing FastAPI API endpoints.
Compatible with the modular router structure.
"""

import os
import time
import json
import requests
import sys
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List, Tuple

# Constants
BASE_URL = "https://api.stoyse.hackclub.app/"  # Remote API URL
#BASE_URL = "http://localhost:9876/"

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BLUE = "\033[94m"
BOLD = "\033[1m"

def print_color(message: str, color: str = RESET):
    """Prints a colored message."""
    print(f"{color}{message}{RESET}")

def print_section(title: str):
    """Prints a section title."""
    print_color(f"\n{BOLD}{'='*30}{RESET}")
    print_color(f"{BOLD}{BLUE}{title}{RESET}")
    print_color(f"{BOLD}{'='*30}{RESET}\n")

def load_env_vars() -> Dict[str, str]:
    """Loads environment variables from the .env file."""
    load_dotenv()
    return {
        "Username": os.getenv("Username"),
        "Password": os.getenv("Password")
    }

def test_route(method: str, route: str, expected_status: int, data: Optional[Dict] = None, 
               token: Optional[str] = None, detailed: bool = True) -> Dict:
    """
    Tests an API route and returns the response.
    
    :param method: HTTP method (GET, POST)
    :param route: API route (e.g., "/api/health")
    :param expected_status: Expected HTTP status code
    :param data: JSON data for the request (optional)
    :param token: Auth token for protected routes (optional)
    :param detailed: If True, details of the API request and response are displayed
    :return: Dictionary with response data
    """
    url = f"{BASE_URL}{route}"
    print_color(f"Testing {method} {url}", BLUE)
    
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
            raise ValueError(f"Unknown method: {method}")
        
        request_time = time.time() - start_time
        
        # Check the status code
        if response.status_code == expected_status:
            print_color(f"✅ {method} {route} returned expected status {expected_status} in {request_time:.2f}s", GREEN)
        else:
            print_color(f"❌ {method} {route} returned status {response.status_code} (expected: {expected_status}) in {request_time:.2f}s", RED)
        
        # Try to parse the response as JSON
        try:
            response_data = response.json()
            if detailed:
                print_color("Received data:", YELLOW)
                # For large JSON structures, only display a part
                response_str = json.dumps(response_data, indent=2)
                if len(response_str) > 1000:
                    # Display only the first 1000 characters
                    response_str = response_str[:1000] + "...\n(truncated)"
                print_color(response_str, RESET)
            return response_data
        except json.JSONDecodeError:
            print_color("Response is not valid JSON.", YELLOW)
            if detailed:
                text_response = response.text
                if len(text_response) > 1000:
                    text_response = text_response[:1000] + "...\n(truncated)"
                print_color(f"Received data (text): {text_response}", RESET)
            return {"text": response.text}
            
    except requests.exceptions.RequestException as e:
        print_color(f"❌ Error during {method} {route}: {e}", RED)
        return {"error": str(e)}

def run_tests() -> List[Tuple[str, bool]]:
    """Runs all tests and returns a list of test results."""
    test_results = []
    
    # Load environment variables
    env_vars = load_env_vars()
    if not env_vars["Username"] or not env_vars["Password"]:
        print_color("Warning: Username or Password missing in the .env file.", YELLOW)
    
    id_token = None
    
    # --- Basic Tests ---
    print_section("Basic Tests")
    
    # Test the root route
    root_response = test_route("GET", "/", 200)
    test_results.append(("Root Route", "status" in root_response))
    
    # Test the health check
    health_response = test_route("GET", "/health", 200)
    test_results.append(("Health Check", "status" in health_response))
    
    # --- Login Test ---
    print_section("Login Test")
    
    # Test with valid login credentials
    print_color(f"Attempting login with credentials from .env: {env_vars['Username']}", BLUE)
    login_data = {
        "email": env_vars["Username"],
        "password": env_vars["Password"]
    }
    login_response = test_route("POST", "/login", 200, login_data)
    login_success = login_response.get("success", False)
    test_results.append(("Login", login_success))
    
    # Extract token from the login response
    if login_success:
        for token_field in ['id_token', 'firebase_token', 'access_token']:
            if token_field in login_response:
                id_token = login_response[token_field]
                break
    
    # --- Tests for Protected Routes ---
    print_section("Tests for Protected Routes")
    
    if id_token:
        stock_data_response = test_route("GET", "/stock-data?symbol=AAPL&timeframe=3M", 200, token=id_token)
        test_results.append(("Stock Data", isinstance(stock_data_response, list)))
        
        funny_tips_response = test_route("GET", "/funny-tips", 200, token=id_token)
        funny_tips_success = isinstance(funny_tips_response, dict) and funny_tips_response.get("success", False)
        test_results.append(("Funny Tips", funny_tips_success))
    else:
        print_color("⚠️ No token extracted, skipping tests for protected routes.", YELLOW)
        test_results.append(("Stock Data", None))
        test_results.append(("Funny Tips", None))
    
    # --- Test for Failed Login ---
    print_section("Test for Failed Login")
    
    invalid_login_data = {
        "email": "invalid@example.com", 
        "password": "wrongpassword123"
    }
    invalid_login_response = test_route("POST", "/login", 401, invalid_login_data)
    invalid_login_expected = "success" not in invalid_login_response or not invalid_login_response["success"]
    test_results.append(("Invalid Login", invalid_login_expected))
    
    return test_results

def main():
    """Main function for testing the API."""
    print_section("API Tests")
    
    try:
        test_results = run_tests()
        
        # Display test summary
        print_section("Test Results")
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for name, result in test_results:
            if result is None:
                print_color(f"⚠️ {name}: SKIPPED", YELLOW)
                skip_count += 1
            elif result:
                print_color(f"✅ {name}: SUCCESSFUL", GREEN)
                success_count += 1
            else:
                print_color(f"❌ {name}: FAILED", RED)
                fail_count += 1
        
        print_section("Summary")
        print_color(f"Tests conducted: {len(test_results)}", BLUE)
        print_color(f"✅ Successful: {success_count}", GREEN)
        print_color(f"⚠️ Skipped: {skip_count}", YELLOW)
        print_color(f"❌ Failed: {fail_count}", RED)
        
        if fail_count > 0:
            sys.exit(1)  # Exit with error code if tests failed
        
    except KeyboardInterrupt:
        print_color("\nTests aborted by user.", YELLOW)
        sys.exit(130)  # Standard exit code for SIGINT (Ctrl+C)
    except Exception as e:
        print_color(f"\nUnexpected error: {str(e)}", RED)
        sys.exit(1)
    
    print_color("\nTest completed.", GREEN)

if __name__ == "__main__":
    main()
