import os
import asyncio
from dotenv import load_dotenv
from app.ai.decision_parser import parse_decision_text

load_dotenv()

async def run_gemini_test():
    print(f"Current AI_PROVIDER: {os.getenv('AI_PROVIDER')}")
    key = os.getenv("GEMINI_API_KEY", "")
    print(f"GEMINI_API_KEY starts with: {key[:10]}... (Length: {len(key)})")
    
    if not key:
        print("No GEMINI_API_KEY found in environment!")
        return

    print("Testing Gemini connection with a simple request...")
    try:
        parsed = await asyncio.to_thread(
            parse_decision_text,
            "I want to buy a house for 500000 over 30 years at 5% interest."
        )
        print("\nSUCCESS! Gemini API is connected and responding.")
        print(f"Response: {parsed}")
    except Exception as e:
        print(f"\nFAILURE: Could not connect to Gemini API. Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_gemini_test())
