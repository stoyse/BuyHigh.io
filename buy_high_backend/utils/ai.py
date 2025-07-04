import requests
import json
from typing import Optional, Dict, Any

def generate_finance_response(prompt: str) -> Optional[str]:
    """
    Generate a finance-focused AI response using the Hack Club AI API.
    
    Args:
        prompt (str): The user's financial query
        
    Returns:
        Optional[str]: The AI-generated response or None if the request failed
    """
    endpoint = "https://ai.hackclub.com/chat/completions"
    
    # Finance-focused system message
    system_message = {
        "role": "system",
        "content": (
            "You are a financial analysis assistant. Provide accurate and helpful information "
            "only on finance-related topics such as investing, trading, markets, economics, "
            "cryptocurrencies, stocks, and personal finance. If asked about non-financial topics, "
            "politely redirect to financial matters. Keep responses concise, data-driven, and "
            "educational. Never provide investment advice that could be interpreted as financial "
            "advice. Always maintain a professional tone."
        )
    }
    
    # Prepare request payload
    payload = {
        "messages": [
            system_message,
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        # Make API request
        response = requests.post(
            endpoint,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        # Check for successful response
        response.raise_for_status()
        response_data = response.json()
        
        # Extract the content from response
        if "choices" in response_data and response_data["choices"]:
            if "message" in response_data["choices"][0]:
                return response_data["choices"][0]["message"].get("content")
        
        print(f"Unexpected response format: {response_data}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Failed to parse API response")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    

def test_finance_ai():
    """Test the finance AI response function with a sample query."""
    test_prompt = "What are the key factors to consider when evaluating a stock's fundamentals?"
    
    print("Testing finance AI response...")
    print(f"Prompt: {test_prompt}")
    print("-" * 50)
    
    response = generate_finance_response(test_prompt)
    
    if response:
        print("Response:")
        print(response)
    else:
        print("Failed to get a response from the AI API")


if __name__ == "__main__":
    test_finance_ai()