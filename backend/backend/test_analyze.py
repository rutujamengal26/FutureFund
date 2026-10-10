import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_analyze():
    # 1. Register/Login Alice
    email = "alice_test_analyze@test.com"
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": "password",
        "full_name": "Alice"
    })
    
    r = requests.post(f"{BASE_URL}/auth/login", data={
        "username": email,
        "password": "password"
    })
    r.raise_for_status()
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create Profile
    profile_data = {
        "profile_name": "Test Profile",
        "profile_data": {
            "monthly_income_inr": 80000,
            "monthly_rent_inr": 15000,
            "essential_expenses_excluding_rent_inr": 10000,
            "variable_expenses_inr": 5000,
            "current_savings_inr": 200000,
            "existing_monthly_emi_inr": 0,
            "other_income_inr": 0
        },
        "is_default": True
    }
    r = requests.post(f"{BASE_URL}/profiles", json=profile_data, headers=headers)
    r.raise_for_status()
    profile_id = r.json()["id"]
    
    # 3. Analyze Decision
    decision_data = {
        "profile_id": profile_id,
        "text": "I want to buy a car for 500000 rupees and take a loan with EMI 12000 per month.",
        "cost_inr": 500000,
        "monthly_emi_inr": 12000
    }
    r = requests.post(f"{BASE_URL}/decisions/analyze", json=decision_data, headers=headers)
    r.raise_for_status()
    result = r.json()
    print("Analysis Result:")
    print(result.keys())
    print("Status:", result["status"])
    if "data" in result:
        print("Data Keys:", result["data"].keys())
        print("Final Verdict:", result["data"].get("final_verdict"))
        if "xgboost_score" in result["data"]:
            print("XGBoost Score:", result["data"]["xgboost_score"])
    print("SUCCESS!")

if __name__ == "__main__":
    test_analyze()
