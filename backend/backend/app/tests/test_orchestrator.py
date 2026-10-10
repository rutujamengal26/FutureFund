import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.analysis import ProfileSchema, DecisionSchema, AssumptionsSchema
from app.schemas.auto_pivot import UserConstraints
from app.schemas.ai import DecisionParseResult

client = TestClient(app)

from app.core.config import settings

@pytest.fixture(autouse=True)
def mock_gemini_env():
    old_provider = settings.AI_PROVIDER
    old_key = settings.GEMINI_API_KEY
    settings.AI_PROVIDER = "gemini"
    settings.GEMINI_API_KEY = "test_key"
    yield
    settings.AI_PROVIDER = old_provider
    settings.GEMINI_API_KEY = old_key

@pytest.fixture
def valid_profile():
    return {
        "monthly_income_inr": 100000.0,
        "other_income_inr": 10000.0,
        "monthly_rent_inr": 25000.0,
        "essential_expenses_excluding_rent_inr": 15000.0,
        "variable_expenses_inr": 10000.0,
        "current_savings_inr": 500000.0,
        "existing_monthly_emi_inr": 5000.0
    }

@pytest.fixture
def valid_decision():
    return {
        "type": "home_purchase",
        "amount_inr": 5000000.0,
        "annual_interest_rate": 8.5,
        "tenure_months": 240,
        "upfront_cash_outflow_inr": 1000000.0
    }

@pytest.fixture
def valid_assumptions():
    return {
        "annual_rent_inflation_pct": 5.0,
        "annual_essential_expense_inflation_pct": 6.0,
        "annual_variable_expense_inflation_pct": 4.0,
        "annual_income_growth_pct": 10.0,
        "simulation_horizon_months": 36
    }

def test_analyze_full_workflow(mock_gemini_env, valid_profile, valid_decision, valid_assumptions):
    # Mocking Gemini SDK response for Second Opinion only, since we don't send text
    with patch("app.ai.client.genai.Client") as mock_client_cls:
        mock_response = MagicMock()
        mock_response.text = '{"summary": "Test Summary", "key_findings": [], "universe_comparison": "", "financial_trade_offs": [], "important_assumptions": [], "suggested_next_steps": [], "disclaimer": "Test"}'
        mock_response.parsed = None
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        req = {
            "profile": valid_profile,
            "decision": valid_decision,
            "assumptions": valid_assumptions,
            "stress_scenario_id": "emergency_expense",
            "auto_pivot_constraints": {
                "maximum_monthly_emi_inr": 50000.0
            }
        }
        
        response = client.post("/api/v1/decisions/analyze", json=req)
        assert response.status_code == 200, response.json()
        data = response.json()
        print("WARNINGS:", data.get("warnings"))
        assert data["status"] == "READY"
        assert len(data["universes"]) == 3
        assert "act_now" in data["ml_estimates"]
        assert "emergency_expense" in data["stress_tests"]["act_now"]["summary"]["stress_scenario_id"]
        assert data["auto_pivot"]["recommended_candidate_id"] is not None
        assert data["second_opinion"]["summary"] == "Test Summary"

def test_analyze_clarification_required_when_missing_profile(mock_gemini_env):
    req = {
        "text": "I want a loan of 5 lakhs",
        "assumptions": {
            "annual_rent_inflation_pct": 5.0,
            "annual_essential_expense_inflation_pct": 6.0,
            "annual_variable_expense_inflation_pct": 4.0,
            "annual_income_growth_pct": 10.0,
            "simulation_horizon_months": 36
        }
    }
    
    with patch("app.ai.client.genai.Client") as mock_client_cls:
        # Mock decision parser to return CLARIFICATION_REQUIRED
        mock_response = MagicMock()
        mock_response.text = '{"status": "CLARIFICATION_REQUIRED", "missing_fields": ["profile"], "ambiguous_fields": [], "assumptions_made": [], "decision": {}}'
        mock_response.parsed = None
        mock_client_cls.return_value.models.generate_content.return_value = mock_response
        
        response = client.post("/api/v1/decisions/analyze", json=req)
        data = response.json()
        print("TEST 2 WARNINGS:", data.get("detail") if response.status_code == 422 else data.get("warnings"))
        assert response.status_code == 200, response.json()
        assert data["status"] == "CLARIFICATION_REQUIRED"
        assert "universes" in data and len(data["universes"]) == 0

def test_analyze_without_text(valid_profile, valid_decision, valid_assumptions):
    req = {
        "profile": valid_profile,
        "decision": valid_decision,
        "assumptions": valid_assumptions
    }
    with patch("app.ai.client.genai.Client") as mock_client_cls:
        mock_response = MagicMock()
        mock_response.text = '{"summary": "Test Summary", "key_findings": [], "universe_comparison": "", "financial_trade_offs": [], "important_assumptions": [], "suggested_next_steps": [], "disclaimer": "Test"}'
        mock_response.parsed = None
        mock_client_cls.return_value.models.generate_content.return_value = mock_response
        
        response = client.post("/api/v1/decisions/analyze", json=req)
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READY"
    assert len(data["universes"]) == 3

def test_health_check_still_works():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
