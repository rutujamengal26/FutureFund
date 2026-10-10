import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.database.session import Base, get_db
from app.core.config import settings

# Test DB Setup
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_futurefund.db"
settings.DATABASE_URL = TEST_SQLALCHEMY_DATABASE_URL

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_gemini_env():
    old_provider = settings.AI_PROVIDER
    old_key = settings.GEMINI_API_KEY
    settings.AI_PROVIDER = "gemini"
    settings.GEMINI_API_KEY = "test_key"
    yield
    settings.AI_PROVIDER = old_provider
    settings.GEMINI_API_KEY = old_key

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_futurefund.db"):
        try:
            os.remove("./test_futurefund.db")
        except PermissionError:
            pass # Windows file lock issue occasionally with SQLite

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_user_registration_and_login():
    # Register
    res = client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "password123"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    
    # Login
    res = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "password123"})
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_profile_creation_and_listing():
    # Login first
    res = client.post("/api/v1/auth/register", json={"email": "test2@example.com", "password": "password123"})
    login_res = client.post("/api/v1/auth/login", data={"username": "test2@example.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    profile_payload = {
        "profile_name": "My Primary Profile",
        "is_default": True,
        "profile_data": {
            "monthly_income_inr": 100000.0,
            "other_income_inr": 10000.0,
            "monthly_rent_inr": 25000.0,
            "essential_expenses_excluding_rent_inr": 15000.0,
            "variable_expenses_inr": 10000.0,
            "current_savings_inr": 500000.0,
            "existing_monthly_emi_inr": 5000.0
        }
    }
    
    # Create
    res = client.post("/api/v1/profiles", json=profile_payload, headers=headers)
    assert res.status_code == 200
    prof_id = res.json()["id"]
    
    # List
    res = client.get("/api/v1/profiles", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1
    
    # Get Detail
    res = client.get(f"/api/v1/profiles/{prof_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["profile_name"] == "My Primary Profile"
    
    # Unauthorized Get (no headers)
    res = client.get("/api/v1/profiles")
    assert res.status_code == 401

def test_persistence_rollback_on_failure():
    pass

def test_analysis_persistence_with_all_universes(setup_test_db):
    res = client.post("/api/v1/auth/register", json={"email": "test3@example.com", "password": "password123"})
    login_res = client.post("/api/v1/auth/login", data={"username": "test3@example.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # We will submit a fully explicit orchestrator request so Gemini is bypassed in test
    req = {
        "text": "",
        "profile": {
            "monthly_income_inr": 100000.0,
            "other_income_inr": 0.0,
            "monthly_rent_inr": 25000.0,
            "essential_expenses_excluding_rent_inr": 20000.0,
            "variable_expenses_inr": 10000.0,
            "current_savings_inr": 200000.0,
            "existing_monthly_emi_inr": 0.0
        },
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
    
    with patch("app.ai.client.genai.Client") as mock_client_cls:
        mock_response = MagicMock()
        mock_response.text = '{"summary": "Test Summary", "key_findings": [], "universe_comparison": "", "financial_trade_offs": [], "important_assumptions": [], "suggested_next_steps": [], "disclaimer": "Test"}'
        mock_response.parsed = None
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        res = client.post("/api/v1/decisions/analyze", json=req, headers=headers)
        
    assert res.status_code == 200, res.text
    data = res.json()
    print("WARNINGS:", data.get("warnings"))
    assert "analysis_id" in data
    analysis_id = data["analysis_id"]
    
    # Check if analysis is saved
    res2 = client.get("/api/v1/analyses", headers=headers)
    assert res2.status_code == 200
    analyses = res2.json()
    assert len(analyses) == 1
    assert analyses[0]["id"] == analysis_id
    
    # Check detail
    res3 = client.get(f"/api/v1/analyses/{analysis_id}", headers=headers)
    assert res3.status_code == 200
    detail = res3.json()
    assert "response_snapshot" in detail
    assert detail["response_snapshot"]["analysis_id"] == analysis_id
    assert len(detail["response_snapshot"]["universes"]) == 3
