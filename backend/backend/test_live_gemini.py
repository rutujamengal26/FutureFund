"""Live integration smoke test for the Gemini provider."""

import asyncio
from app.ai.decision_parser import parse_decision_text
from app.ai.second_opinion import generate_second_opinion
from app.schemas.analysis import DecisionSchema, ProfileSchema
from app.core.config import settings

async def run_live_tests():
    settings.AI_PROVIDER = "gemini"
    
    print("Testing live Gemini...")
    
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
        profile = ProfileSchema(
            monthly_income_inr=100000,
            other_income_inr=0,
            monthly_rent_inr=20000,
            essential_expenses_excluding_rent_inr=15000,
            variable_expenses_inr=10000,
            current_savings_inr=500000,
            existing_monthly_emi_inr=0
        )
        decision = DecisionSchema(
            type="LOAN",
            amount_inr=500000,
            annual_interest_rate=9.0,
            tenure_months=24,
            upfront_cash_outflow_inr=0
        )
        opinion = await asyncio.to_thread(generate_second_opinion, {
            "profile": profile.model_dump(),
            "decision": decision.model_dump(),
            "simulations": {},
            "assumptions": [],
        })
        print(f"SUCCESS: {opinion}")
    except Exception as e:
        print(f"FAILURE generate_second_opinion: {e}")

if __name__ == "__main__":
    asyncio.run(run_live_tests())
