import asyncio
import os
import sys

# Ensure app is in path
sys.path.insert(0, os.path.abspath("."))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
from app.ai.decision_parser import parse_decision_text
from app.ai.second_opinion import generate_second_opinion
from app.schemas.analysis import DecisionSchema, ProfileSchema
from app.core.config import settings

async def run_live_tests():
    # Make sure we use the groq configuration
    os.environ["AI_PROVIDER"] = "groq"
    
    print("Testing live Groq...")
    
    if not settings.GROQ_API_KEY:
        print("SKIPPING: GROQ_API_KEY is not set.")
        return

    print("\n--- Testing parse_decision_text ---")
    try:
        parsed = await asyncio.to_thread(
            parse_decision_text,
            "I want to buy a car for 500k over 2 years at 9% interest."
        )
        print(f"SUCCESS: {parsed}")
    except Exception as e:
        print(f"FAILURE parse_decision_text: {e}")
        
    print("\n--- Testing generate_second_opinion ---")
    try:
        # Mock inputs
        evidence = {
            "analysis_id": "test-123",
            "universe_act_now": {
                "loan_amount": 500000,
                "monthly_emi": 22842,
                "minimum_balance_projected": 50000
            },
            "ml_estimates": {
                "stress_probability": 0.1
            }
        }
        opinion = await asyncio.to_thread(
            generate_second_opinion,
            evidence
        )
        print(f"SUCCESS: {opinion}")
    except Exception as e:
        print(f"FAILURE generate_second_opinion: {e}")

if __name__ == "__main__":
    asyncio.run(run_live_tests())
