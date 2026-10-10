import os
import sys
import httpx
from pydantic_settings import BaseSettings

# Load config to get variables safely
sys.path.insert(0, os.path.abspath("."))
from app.core.config import settings

def diagnose():
    print("--- Groq Diagnosis ---")
    provider = settings.AI_PROVIDER
    model = settings.GROQ_MODEL
    key = settings.GROQ_API_KEY
    
    print(f"AI_PROVIDER: {provider}")
    print(f"GROQ_MODEL Configured: {model}")
    print(f"GROQ_API_KEY Configured: {'Yes (Length: ' + str(len(key)) + ')' if key else 'No'}")
    
    # Verify the groq client targets official API by default
    import groq
    client = groq.Groq(api_key=key)
    print(f"Groq SDK Base URL: {client.base_url}")
    
    # Query models
    print("\n--- Querying Models Endpoint ---")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Use httpx for manual query to get raw status
        response = httpx.get("https://api.groq.com/openai/v1/models", headers=headers)
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = [m.get("id") for m in data.get("data", [])]
            print(f"Total models available: {len(models)}")
            if "openai/gpt-oss-20b" in models:
                print("Model 'openai/gpt-oss-20b' is AVAILABLE.")
            else:
                print("Model 'openai/gpt-oss-20b' is NOT in the list.")
                # Print a few available models for context
                print(f"Available models (first 5): {models[:5]}")
        else:
            print(f"Error querying models: {response.text}")
    except Exception as e:
        print(f"Network error querying models: {str(e)}")

if __name__ == "__main__":
    diagnose()
