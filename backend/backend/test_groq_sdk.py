import os
import sys
import groq

sys.path.insert(0, os.path.abspath("."))
from app.core.config import settings

def test_sdk():
    key = settings.GROQ_API_KEY
    model = settings.GROQ_MODEL
    
    print(f"Testing Groq SDK directly with model: {model}")
    client = groq.Groq(api_key=key)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hello"}],
            temperature=0.0
        )
        print("Success! Output:")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sdk()
