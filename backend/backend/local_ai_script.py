import sys
import os
sys.path.insert(0, os.path.abspath("."))
from app.ai.decision_parser import parse_decision_text
from app.ai.second_opinion import generate_second_opinion

def test_local():
    try:
        print("Testing Parser...")
        res = parse_decision_text("I earn 50000 INR per month, rent is 10000 INR, savings 200000 INR. I want a home loan of 1000000 INR for 10 years.")
        print("Parser output:")
        print(res.model_dump_json(indent=2))

        print("\nTesting Second Opinion...")
        evidence = {
            "analysis_id": "test-123",
            "universe_act_now": {
                "loan_amount": 1000000,
                "monthly_emi": 15000,
                "minimum_balance_projected": 50000
            }
        }
        so = generate_second_opinion(evidence)
        print("Second Opinion output:")
        print(so.model_dump_json(indent=2))
        print("\nTESTS SUCCESSFUL")
    except Exception as e:
        print(f"\nTESTS FAILED: {e}")

if __name__ == "__main__":
    test_local()
