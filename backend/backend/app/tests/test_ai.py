import pytest
import json
import httpx
from unittest.mock import patch, MagicMock
from app.ai.client import AIConfigurationError, AIAPIError, AIValidationError, AITimeoutError
from app.ai.decision_parser import parse_decision_text
from app.ai.second_opinion import generate_second_opinion

from app.core.config import settings

@pytest.fixture
def mock_env_gemini(monkeypatch):
    old_provider = settings.AI_PROVIDER
    old_key = settings.GEMINI_API_KEY
    settings.AI_PROVIDER = "gemini"
    settings.GEMINI_API_KEY = "test_key"
    yield
    settings.AI_PROVIDER = old_provider
    settings.GEMINI_API_KEY = old_key

@pytest.fixture
def mock_env_groq(monkeypatch):
    old_provider = settings.AI_PROVIDER
    old_key = settings.GROQ_API_KEY
    settings.AI_PROVIDER = "groq"
    settings.GROQ_API_KEY = "test_groq_key"
    yield
    settings.AI_PROVIDER = old_provider
    settings.GROQ_API_KEY = old_key

@pytest.fixture
def mock_gemini_client():
    with patch("app.ai.client.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        yield mock_client

def test_missing_api_key_configuration_error(mock_env_gemini):
    settings.GEMINI_API_KEY = ""
    with pytest.raises(AIConfigurationError):
        parse_decision_text("I want a car loan.")

def test_unsupported_provider_configuration_error(mock_env_gemini):
    settings.AI_PROVIDER = "unsupported"
    with pytest.raises(AIConfigurationError, match="Unsupported AI_PROVIDER"):
        parse_decision_text("I want a car loan.")

def test_decision_parser_valid_extraction_gemini(mock_env_gemini, mock_gemini_client):
    mock_gemini_client.models.generate_content.return_value = MagicMock(text=json.dumps({
        "status": "READY",
        "profile": {
            "monthly_income_inr": 60000.0,
            "monthly_rent_inr": 12000.0,
            "current_savings_inr": 150000.0
        },
        "decision": {
            "type": "personal",
            "amount_inr": 500000.0,
            "tenure_months": 36
        },
        "missing_fields": [],
        "ambiguous_fields": [],
        "assumptions_made": []
    }))

    result = parse_decision_text("I earn 60000 per month, pay 12000 rent, have 1.5 lakh in savings and want a 5 lakh personal loan for three years.")
    
    assert result.status == "READY"
    assert result.profile.monthly_income_inr == 60000.0
    assert result.profile.current_savings_inr == 150000.0
    assert result.decision.amount_inr == 500000.0
    assert result.decision.tenure_months == 36
    assert result.decision.type == "personal"
    mock_gemini_client.models.generate_content.assert_called_once()
    assert mock_gemini_client.models.generate_content.call_args.kwargs["model"] == settings.GEMINI_MODEL

def test_decision_parser_missing_fields_forces_clarification_gemini(mock_env_gemini, mock_gemini_client):
    mock_gemini_client.models.generate_content.return_value = MagicMock(text=json.dumps({
        "status": "CLARIFICATION_REQUIRED",
        "profile": {},
        "decision": {"amount_inr": 500000.0},
        "missing_fields": ["tenure_months", "type"],
        "ambiguous_fields": [],
        "assumptions_made": [],
        "clarification_question": "What is the tenure?"
    }))

    result = parse_decision_text("I want a 5 lakh loan.")
    
    assert result.status == "CLARIFICATION_REQUIRED"
    assert "tenure_months" in result.missing_fields
    assert result.decision.amount_inr == 500000.0

def test_pydantic_rejection_of_malformed_output_gemini(mock_env_gemini, mock_gemini_client):
    mock_gemini_client.models.generate_content.return_value = MagicMock(
        text=json.dumps({"decision": {"amount_inr": 100}})
    )
    
    with pytest.raises(AIValidationError) as exc_info:
        parse_decision_text("invalid")
    assert "Invalid structured output" in str(exc_info.value)

def test_transient_failure_retries_gemini(mock_env_gemini, mock_gemini_client):
    mock_success_response = MagicMock(text=json.dumps({
        "status": "READY",
        "decision": {
            "type": "personal",
            "amount_inr": 50000.0,
            "tenure_months": 12
        }
    }))
    generate_content = mock_gemini_client.models.generate_content
    generate_content.side_effect = [
        RuntimeError("Transient API Error"),
        RuntimeError("Transient API Error"),
        mock_success_response
    ]
    
    with patch("time.sleep"):
        result = parse_decision_text("Some text")
        
    assert result.status == "READY"
    assert generate_content.call_count == 3

def test_gemini_timeout(mock_env_gemini, mock_gemini_client):
    mock_gemini_client.models.generate_content.side_effect = httpx.TimeoutException("Timeout")
    
    with patch("time.sleep"):
        with pytest.raises(AITimeoutError):
            parse_decision_text("Some text")

def test_gemini_unavailable(mock_env_gemini, mock_gemini_client):
    mock_gemini_client.models.generate_content.side_effect = RuntimeError("API unavailable")
    
    with patch("time.sleep"):
        with pytest.raises(AIAPIError) as exc:
            parse_decision_text("Some text")
        assert "Failed to generate content" in str(exc.value)

def test_second_opinion_generates_gemini(mock_env_gemini, mock_gemini_client):
    mock_gemini_client.models.generate_content.return_value = MagicMock(text=json.dumps({
        "summary": "This is a summary",
        "key_findings": ["Finding 1"],
        "universe_comparison": "Comparison",
        "financial_trade_offs": ["Trade-off"],
        "stress_test_findings": "None",
        "auto_pivot_alternatives": "None",
        "important_assumptions": ["Inflation"],
        "suggested_next_steps": ["Save"],
        "disclaimer": "This is a disclaimer."
    }))

    evidence = {"some": "data"}
    res = generate_second_opinion(evidence)
    
    assert res.summary == "This is a summary"
    assert res.disclaimer == "This is a disclaimer."

def test_decision_parser_valid_extraction_groq(mock_env_groq):
    with patch("groq.Groq") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "status": "READY",
            "profile": {
                "monthly_income_inr": 60000.0,
                "monthly_rent_inr": 12000.0,
                "current_savings_inr": 150000.0
            },
            "decision": {
                "type": "personal",
                "amount_inr": 500000.0,
                "tenure_months": 36
            },
            "missing_fields": [],
            "ambiguous_fields": [],
            "assumptions_made": []
        })
        mock_client.chat.completions.create.return_value = mock_response

        result = parse_decision_text("I earn 60000 per month, pay 12000 rent, have 1.5 lakh in savings and want a 5 lakh personal loan for three years.")
        
        assert result.status == "READY"
        assert result.profile.monthly_income_inr == 60000.0
        assert result.decision.amount_inr == 500000.0
