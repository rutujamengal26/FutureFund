from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from app.schemas.analysis import ProfileSchema, DecisionSchema, AssumptionsSchema
from app.schemas.simulation import UniverseSummary
from app.schemas.stress_test import UniverseStressSummary

class UserConstraints(BaseModel):
    minimum_ending_cash_balance_inr: Optional[float] = None
    minimum_cash_balance_inr: Optional[float] = None
    maximum_monthly_emi_inr: Optional[float] = None
    maximum_debt_to_income_pct: Optional[float] = None
    maximum_total_interest_inr: Optional[float] = None
    maximum_decision_delay_months: Optional[int] = None
    require_non_negative_monthly_surplus: Optional[bool] = None

class SearchConfiguration(BaseModel):
    max_candidates: int = Field(20, description="Maximum number of candidates to evaluate")
    loan_amount_multipliers: List[float] = Field([1.0, 0.9, 0.8, 0.7, 0.6, 0.5])
    decision_delays_months: List[int] = Field([0, 3, 6, 9])
    tenure_options_months: List[int] = Field([12, 24, 36, 48, 60])
    ranking_objective: Literal["balanced", "preserve_cash", "minimize_total_interest", "reduce_monthly_burden"] = "balanced"

class AutoPivotRequest(BaseModel):
    profile: ProfileSchema
    decision: DecisionSchema
    assumptions: AssumptionsSchema
    constraints: Optional[UserConstraints] = None
    search_config: Optional[SearchConfiguration] = None
    stress_scenario_id: Optional[str] = None

class ConstraintCheck(BaseModel):
    constraint_name: str
    requested_value: Any
    calculated_value: Any
    is_satisfied: bool

class CandidateConfiguration(BaseModel):
    loan_amount_inr: float
    decision_delay_months: int
    tenure_months: int
    scheduled_emi_inr: float

class CandidateChange(BaseModel):
    metric: str
    original_value: Any
    candidate_value: Any

class AutoPivotCandidate(BaseModel):
    candidate_id: str
    configuration: CandidateConfiguration
    changes_from_baseline: List[CandidateChange]
    
    baseline_summary: UniverseSummary
    stress_summary: Optional[UniverseStressSummary] = None
    
    constraint_checks: List[ConstraintCheck]
    is_eligible: bool
    
    ranking_score: float
    rank: Optional[int] = None
    
    trade_offs: List[str]

class AutoPivotResponse(BaseModel):
    analysis_id: str
    ranking_objective: str
    assumptions: AssumptionsSchema
    baseline_candidate_id: str
    candidates: List[AutoPivotCandidate]
    eligible_candidates: int
    recommended_candidate_id: Optional[str]
    limitations: List[str]
    search_metadata: Dict[str, Any]
