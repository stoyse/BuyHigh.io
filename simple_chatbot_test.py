#!/usr/bin/env python3
"""
Simple test script for the BuyHigh.io Chatbot API endpoint.

Usage:
    python simple_chatbot_test.py "Your question here"
    
Example:
    python simple_chatbot_test.py "What are the key factors in stock evaluation?"
"""

import requests
import json
import sys

# Configuration - Update these values
API_BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

def login_and_get_token(email: str, password: str) -> str:
    """Login and return the authentication token."""
    login_url = f"{API_BASE_URL}/auth/login"
    login_data = {"email": email, "password": password}
    
    response = requests.post(login_url, json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('id_token')
    else:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")

def test_chatbot(prompt: str, token: str) -> dict:
    """Send a prompt to the chatbot API and return the response."""
    chatbot_url = f"{API_BASE_URL}/api/chatbot"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"prompt": prompt}
    
    response = requests.post(chatbot_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Chatbot request failed: {response.status_code} - {response.text}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python simple_chatbot_test.py \"Your question here\"")
        print("Example: python simple_chatbot_test.py \"What are the key factors in stock evaluation?\"")
        sys.exit(1)
    
    prompt = sys.argv[1]
    
    try:
        print("🔐 Logging in...")
        token = login_and_get_token(TEST_EMAIL, TEST_PASSWORD)
        print("✅ Login successful!")
        
        print(f"\n🤖 Sending prompt: '{prompt}'")
        result = test_chatbot(prompt, token)
        
        print("\n📋 Response:")
        print(json.dumps(result, indent=2))
        
        if result.get('success') and result.get('response'):
            print(f"\n💬 AI Answer:\n{result['response']}")
        elif result.get('error'):
            print(f"\n❌ Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
