import requests
import json

# Base URL of the API
API_BASE_URL = "https://api.stoyse.hackclub.app"

def get_auth_token(email="julianfaitdugaming@gmail.com", password="srbxrK5KpfxMG6u"):
    """Authenticate with the API to get a token."""
    login_url = f"{API_BASE_URL}/auth/login"
    credentials = {"email": email, "password": password}
    
    try:
        response = requests.post(login_url, json=credentials)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        login_data = response.json()
        
        # Add detailed logging
        print("Login API Response:")
        print(json.dumps(login_data, indent=2))

        # The login response returns an 'id_token' which should be used for auth
        if "id_token" in login_data:
            return login_data.get("id_token")

        print("Error: 'id_token' not found in the response.")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error during authentication: {e}")
        if e.response:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response content: {e.response.text}")
        return None

def get_all_users(token: str):
    """Fetch all users from the API using the provided token."""
    users_url = f"{API_BASE_URL}/users/all"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(users_url, headers=headers)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching all users: {e}")
        if e.response:
            print(f"Response content: {e.response.text}")
        return None

if __name__ == "__main__":
    print("Attempting to authenticate and fetch all users...")
    
    # 1. Get the authentication token
    auth_token = get_auth_token()
    
    if auth_token:
        print("Authentication successful. Token received.")
        
        # 2. Call the /users/all endpoint with the token
        all_users_data = get_all_users(auth_token)
        
        if all_users_data:
            print("\n--- All Users API Response ---")
            print(json.dumps(all_users_data, indent=2))
            print("----------------------------")
        else:
            print("Failed to retrieve all users.")
    else:
        print("Authentication failed. Cannot proceed to fetch users.")
