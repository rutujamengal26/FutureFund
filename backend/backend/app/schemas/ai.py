from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ParsedProfile(BaseModel):
    monthly_income_inr: Optional[float] = None
    other_income_inr: Optional[float] = None
    monthly_rent_inr: Optional[float] = None
    essential_expenses_excluding_rent_inr: Optional[float] = None
    variable_expenses_inr: Optional[float] = None
    current_savings_inr: Optional[float] = None
    existing_monthly_emi_inr: Optional[float] = None

class ParsedDecision(BaseModel):
    type: Optional[str] = Field(None, description="The type of decision (e.g., car, home, personal)")
    amount_inr: Optional[float] = None
    annual_interest_rate: Optional[float] = None
    tenure_months: Optional[int] = None
    upfront_cash_outflow_inr: Optional[float] = None

class DecisionParseResult(BaseModel):
    status: str = Field(..., description="Either 'READY' or 'CLARIFICATION_REQUIRED'")
    profile: Optional[ParsedProfile] = None
    decision: Optional[ParsedDecision] = None
    missing_fields: List[str] = Field(default_factory=list)
    ambiguous_fields: List[str] = Field(default_factory=list)
    assumptions_made: List[str] = Field(default_factory=list)
    clarification_question: Optional[str] = None

class SecondOpinionRequest(BaseModel):
    analysis_evidence: Dict[str, Any]

class SecondOpinionResponse(BaseModel):
    summary: str = Field(..., description="Concise summary of the financial situation.")
    key_findings: List[str] = Field(..., description="Key findings supported by the supplied results.")
    universe_comparison: str = Field(..., description="Comparison of the three universes.")
    financial_trade_offs: List[str] = Field(..., description="Relevant financial trade-offs.")
    stress_test_findings: Optional[str] = Field(None, description="Stress-test findings when available.")
    auto_pivot_alternatives: Optional[str] = Field(None, description="Evaluated Auto-Pivot alternatives when available.")
    important_assumptions: List[str] = Field(..., description="Important assumptions and limitations.")
    suggested_next_steps: List[str] = Field(..., description="Suggested next steps for the user.")
    disclaimer: str = Field(..., description="Educational disclaimer stating this is not guaranteed financial advice and ML predictions are synthetic.")
