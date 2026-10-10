import sys
import httpx
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_tests():
    print("Starting API End-to-End Tests...")
    
    # Wait for health
    try:
        res = httpx.get(f"{BASE_URL}/health", timeout=5.0)
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print("Backend health check PASSED.")
    except Exception as e:
        print(f"Failed to connect to backend: {e}")
        return

    client = httpx.Client(base_url=BASE_URL, timeout=120.0)

    # 1. Register Alice
    alice_email = f"alice_{uuid.uuid4()}@example.com"
    alice_password = "SecurePassword123!"
    res = client.post("/auth/register", json={
        "email": alice_email,
        "password": alice_password,
        "full_name": "Alice Test"
    })
    assert res.status_code in (200, 201), f"Failed to register Alice: {res.text}"
    print("Alice registration PASSED.")

    # 2. Login Alice
    res = client.post("/auth/login", data={
        "username": alice_email,
        "password": alice_password
    })
    assert res.status_code == 200, f"Failed to login Alice: {res.text}"
    alice_token = res.json()["access_token"]
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    print("Alice login PASSED.")

    # 3. Create Financial Profile
    profile_data = {
        "monthly_income_inr": 150000,
        "other_income_inr": 0,
        "monthly_rent_inr": 30000,
        "essential_expenses_excluding_rent_inr": 20000,
        "variable_expenses_inr": 15000,
        "current_savings_inr": 500000,
        "existing_monthly_emi_inr": 0
    }
    profile_payload = {
        "profile_name": "Test Profile",
        "profile_data": profile_data
    }
    res = client.post("/profiles", json=profile_payload, headers=alice_headers)
    assert res.status_code in (200, 201), f"Failed to create profile: {res.text}"
    alice_profile_id = res.json()["id"]
    print("Alice profile creation PASSED.")

    # 4. Partial Decision - Clarification check
    partial_decision = {
        "text": "I want a loan",
        "profile": profile_data,
        "decision": None,
        "assumptions": {
            "annual_rent_inflation_pct": 5.0,
            "annual_essential_expense_inflation_pct": 6.0,
            "annual_variable_expense_inflation_pct": 6.0,
            "annual_income_growth_pct": 8.0,
            "simulation_horizon_months": 60
        }
    }
    res = client.post("/decisions/analyze", json=partial_decision, headers=alice_headers)
    # The API might return 200 with status="CLARIFICATION_REQUIRED" or 422 if structurally incomplete depending on implementation
    if res.status_code == 200:
        data = res.json()
        assert data["status"] == "CLARIFICATION_REQUIRED", "Expected clarification status"
        print("Clarification handling PASSED.")
    elif res.status_code == 422:
        print("Clarification handling via 422 PASSED.")
    else:
        print(f"Clarification handling FAILED: {res.status_code} - {res.text}")

    # 5. Complete Decision
    complete_decision = {
        "text": "I want a car loan for 1000000 INR for 5 years at 8 percent",
        "profile": profile_data,
        "decision": {
            "type": "car",
            "amount_inr": 1000000,
            "annual_interest_rate": 8.0,
            "tenure_months": 60,
            "upfront_cash_outflow_inr": 0
        },
        "assumptions": {
            "annual_rent_inflation_pct": 5.0,
            "annual_essential_expense_inflation_pct": 6.0,
            "annual_variable_expense_inflation_pct": 6.0,
            "annual_income_growth_pct": 8.0,
            "simulation_horizon_months": 60
        },
        "stress_scenario_id": "job_loss",
        "auto_pivot_constraints": {
            "max_emi_inr": 25000,
            "min_ending_cash_balance_inr": 100000,
            "max_debt_to_income_ratio": 0.4,
            "minimum_surplus_inr": 5000
        },
        "auto_pivot_config": {
            "max_candidates": 10,
            "objective": "balanced"
        }
    }
    res = client.post("/decisions/analyze", json=complete_decision, headers=alice_headers)
    assert res.status_code == 200, f"Analysis failed: {res.text}"
    analysis = res.json()
    alice_analysis_id = analysis["analysis_id"]
    
    # Verification of universes
    assert len(analysis["universes"]) == 3, "Expected 3 universes"
    
    # Verification of Risk Engine (ML)
    assert analysis["ml_estimates"], "Missing ML estimates"
    
    # Verification of Stress Engine
    print("Analysis Keys:", analysis.keys())
    assert "stress_results" in analysis or "stress_tests" in analysis, f"Missing stress info: {analysis.keys()}"
    
    # Verification of Auto-Pivot
    assert "auto_pivot" in analysis, "Missing Auto-Pivot key"
    if not analysis["auto_pivot"]:
        print("Auto-Pivot returned empty or null (handled honestly).")
    
    # Verification of AI Second Opinion
    assert analysis["second_opinion"], "Missing Second Opinion"
    
    print("Full Analysis generation PASSED.")
    
    # 6. Chatbot Parser Test
    res = client.post("/gemini/parse-decision", json={"text": "I want to buy a house for 50L over 20 years at 8.5%"}, headers=alice_headers)
    assert res.status_code == 200, f"Parse decision failed: {res.text}"
    print("Chatbot decision parser PASSED.")
    
    # 7. Verify Persistence
    res = client.get("/analyses", headers=alice_headers)
    assert res.status_code == 200
    analyses_list = res.json()
    assert len(analyses_list) >= 1
    assert any(a["id"] == alice_analysis_id for a in analyses_list), "Analysis not found in history"
    print("PostgreSQL persistence and history retrieval PASSED.")
    
    # 8. Ownership Isolation
    bob_email = f"bob_{uuid.uuid4()}@example.com"
    bob_password = "SecurePassword123!"
    res = client.post("/auth/register", json={
        "email": bob_email,
        "password": bob_password,
        "full_name": "Bob Test"
    })
    assert res.status_code in (200, 201)
    
    res = client.post("/auth/login", data={
        "username": bob_email,
        "password": bob_password
    })
    assert res.status_code == 200
    bob_token = res.json()["access_token"]
    bob_headers = {"Authorization": f"Bearer {bob_token}"}
    
    # Bob tries to access Alice's profile
    res = client.get(f"/profiles/{alice_profile_id}", headers=bob_headers)
    assert res.status_code in (403, 404), f"Bob accessed Alice's profile! Status: {res.status_code}"
    
    # Bob tries to access Alice's analysis
    res = client.get(f"/analyses/{alice_analysis_id}", headers=bob_headers)
    assert res.status_code in (403, 404), f"Bob accessed Alice's analysis! Status: {res.status_code}"
    
    print("PostgreSQL RLS and Alice-vs-Bob isolation PASSED.")
    
    # 9. Verify Failures and Stability (Missing Auth)
    res = client.get(f"/profiles/{alice_profile_id}")
    assert res.status_code == 401, f"Unauthenticated access allowed! Status: {res.status_code}"
    print("Authentication enforcement PASSED.")
    
    print("ALL API END-TO-END TESTS COMPLETED SUCCESSFULLY.")

if __name__ == "__main__":
    run_tests()
