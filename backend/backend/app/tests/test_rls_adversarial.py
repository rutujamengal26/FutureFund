import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

import os
# Override BEFORE importing anything that imports settings!
os.environ["DATABASE_URL"] = "postgresql+psycopg://futurefund_api:api_password@localhost:5432/futurefund_test?options=-c%20search_path%3Dfuturefund_schema,public"
os.environ["AI_PROVIDER"] = "gemini"
os.environ["GEMINI_API_KEY"] = "test_key"

from app.main import app
from app.core.config import settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_ai():
    with patch("app.ai.client.genai.Client") as mock_client_cls:
        mock_response = MagicMock()
        mock_response.text = '{"summary": "Test Summary", "key_findings": [], "universe_comparison": "", "financial_trade_offs": [], "important_assumptions": [], "suggested_next_steps": [], "disclaimer": "Test"}'
        mock_response.parsed = None
        mock_client_cls.return_value.models.generate_content.return_value = mock_response
        yield

def test_alice_vs_bob_isolation():
    if "sqlite" in settings.DATABASE_URL:
        pytest.skip("RLS tests require PostgreSQL, but SQLite is configured.")
    
    # Verify settings point to the right DB
    assert "futurefund_api" in settings.DATABASE_URL

    import uuid
    uid = str(uuid.uuid4())[:8]
    alice_email = f"alice_{uid}@example.com"
    bob_email = f"bob_{uid}@example.com"

    # 1. Register Alice
    res = client.post("/api/v1/auth/register", json={"email": alice_email, "password": "password123"})
    assert res.status_code == 200, res.text
    
    # Login Alice
    res = client.post("/api/v1/auth/login", data={"username": alice_email, "password": "password123"})
    assert res.status_code == 200
    alice_token = res.json()["access_token"]
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    
    # 2. Register Bob
    res = client.post("/api/v1/auth/register", json={"email": bob_email, "password": "password123"})
    assert res.status_code == 200
    
    # Login Bob
    res = client.post("/api/v1/auth/login", data={"username": bob_email, "password": "password123"})
    assert res.status_code == 200
    bob_token = res.json()["access_token"]
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    # 3. Alice creates a financial profile
    profile_payload = {
        "profile_name": "Alice Profile",
        "is_default": True,
        "profile_data": {
            "monthly_income_inr": 100000.0,
            "other_income_inr": 0.0,
            "monthly_rent_inr": 25000.0,
            "essential_expenses_excluding_rent_inr": 20000.0,
            "variable_expenses_inr": 10000.0,
            "current_savings_inr": 200000.0,
            "existing_monthly_emi_inr": 0.0
        }
    }
    res = client.post("/api/v1/profiles", json=profile_payload, headers=alice_headers)
    assert res.status_code == 200
    alice_profile_id = res.json()["id"]
    
    # 4. Alice runs an analysis
    req = {
        "text": "",
        "profile": profile_payload["profile_data"],
        "decision": {
            "type": "LOAN",
            "amount_inr": 500000.0,
            "annual_interest_rate": 10.0,
            "tenure_months": 24,
            "upfront_cash_outflow_inr": 0.0
        },
        "assumptions": {
            "simulation_horizon_months": 12,
            "annual_rent_inflation_pct": 5.0,
            "annual_essential_expense_inflation_pct": 6.0,
            "annual_variable_expense_inflation_pct": 4.0,
            "annual_income_growth_pct": 10.0
        },
        "auto_pivot_constraints": {
            "max_monthly_emi_inr": 30000,
            "max_tenure_months": 36,
            "min_tenure_months": 12,
            "max_interest_rate": 12.0
        }
    }
    res = client.post("/api/v1/decisions/analyze", json=req, headers=alice_headers)
    assert res.status_code == 200, res.text
    alice_analysis_id = res.json()["analysis_id"]

    # --- ADVERSARIAL TESTS BY BOB ---

    # A. Bob tries to read Alice's profile
    res = client.get(f"/api/v1/profiles/{alice_profile_id}", headers=bob_headers)
    # RLS makes the row invisible, so the API should return 404 Not Found
    assert res.status_code == 404

    # B. Bob tries to list profiles, should only see his own (none)
    res = client.get("/api/v1/profiles", headers=bob_headers)
    assert res.status_code == 200
    assert len(res.json()) == 0
    


    # D. Bob tries to read Alice's analysis
    res = client.get(f"/api/v1/analyses/{alice_analysis_id}", headers=bob_headers)
    assert res.status_code == 404

    # E. Bob tries to delete Alice's profile
    res = client.delete(f"/api/v1/profiles/{alice_profile_id}", headers=bob_headers)
    assert res.status_code == 404

    print("All Alice-vs-Bob adversarial tests passed!")
