from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ProfileSchema(BaseModel):
    monthly_income_inr: float = Field(..., description="Monthly income in INR")
    other_income_inr: float = Field(0.0, description="Other monthly income in INR")
    monthly_rent_inr: float = Field(..., description="Monthly rent in INR")
    essential_expenses_excluding_rent_inr: float = Field(..., description="Essential expenses excluding rent in INR")
    variable_expenses_inr: float = Field(..., description="Variable monthly expenses in INR")
    current_savings_inr: float = Field(..., description="Current total savings in INR")
    existing_monthly_emi_inr: float = Field(..., description="Existing monthly EMI in INR")

class DecisionSchema(BaseModel):
    type: str = Field(..., description="Type of decision (e.g., house, car, education)")
    amount_inr: float = Field(..., description="Amount required for the decision in INR")
    annual_interest_rate: float = Field(..., description="Annual interest rate for the loan")
    tenure_months: int = Field(..., description="Tenure of the loan in months")
    upfront_cash_outflow_inr: Optional[float] = Field(0.0, description="Any upfront cash outflow required")

class AssumptionsSchema(BaseModel):
    annual_rent_inflation_pct: float = Field(..., description="Annual rent inflation percentage")
    annual_essential_expense_inflation_pct: float = Field(..., description="Annual essential expense inflation percentage")
    annual_variable_expense_inflation_pct: float = Field(..., description="Annual variable expense inflation percentage")
    annual_income_growth_pct: float = Field(..., description="Annual income growth percentage")
    simulation_horizon_months: int = Field(..., description="Simulation horizon in months (e.g., 12, 24, 36)")

class AnalysisRequest(BaseModel):
    profile: ProfileSchema
    decision: DecisionSchema
    assumptions: AssumptionsSchema

class UniverseSchema(BaseModel):
    name: str
    description: str
    metrics: Dict[str, Any]

class AnalysisResponse(BaseModel):
    analysis_id: str
    risk_assessment: Dict[str, Any]
    universes: List[UniverseSchema]
    stress_tests: Dict[str, Any]
    auto_pivot_alternatives: List[Dict[str, Any]]
    second_opinion: Dict[str, Any]
    assumptions: AssumptionsSchema
