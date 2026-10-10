from pydantic import BaseModel, Field, root_validator
from typing import Optional, List, Literal, Union

class StressEventBase(BaseModel):
    type: str

class IncomeReductionEvent(StressEventBase):
    type: Literal["income_reduction"] = "income_reduction"
    reduction_pct: float = Field(..., ge=0, le=100)
    start_month: int = Field(..., ge=1)
    duration_months: int = Field(..., ge=1)
    applies_to: Literal["primary", "other", "both"] = "primary"

class IncomeInterruptionEvent(StressEventBase):
    type: Literal["income_interruption"] = "income_interruption"
    start_month: int = Field(..., ge=1)
    duration_months: int = Field(..., ge=1)
    applies_to: Literal["primary", "other", "both"] = "primary"

class EmergencyExpenseEvent(StressEventBase):
    type: Literal["emergency_expense"] = "emergency_expense"
    amount_inr: float = Field(..., gt=0)
    month: int = Field(..., ge=1)

class PermanentExpenseIncreaseEvent(StressEventBase):
    type: Literal["rent_increase", "essential_increase", "variable_increase"]
    increase_pct: float = Field(..., gt=0)
    start_month: int = Field(..., ge=1)

StressEvent = Union[
    IncomeReductionEvent,
    IncomeInterruptionEvent,
    EmergencyExpenseEvent,
    PermanentExpenseIncreaseEvent
]

class StressScenario(BaseModel):
    scenario_id: str
    name: str
    description: str
    events: List[StressEvent]

class StressedMonthlyRecord(BaseModel):
    month: int
    
    baseline_projected_income_inr: float
    stressed_projected_income_inr: float
    
    baseline_living_expenses_inr: float
    stressed_living_expenses_inr: float
    
    existing_emi_inr: float
    new_loan_emi_inr: float
    
    baseline_monthly_surplus_inr: float
    stressed_monthly_surplus_inr: float
    
    baseline_closing_cash_balance_inr: float
    stressed_closing_cash_balance_inr: float
    cash_balance_difference_inr: float
    
    baseline_reserve_threshold_inr: float
    stressed_reserve_threshold_inr: float
    
    remaining_loan_balance_inr: float
    
    baseline_reserve_breach: bool
    stressed_reserve_breach: bool

class UniverseStressSummary(BaseModel):
    universe_id: str
    stress_scenario_id: str
    
    baseline_ending_cash_balance_inr: float
    stressed_ending_cash_balance_inr: float
    ending_cash_change_inr: float
    
    baseline_minimum_cash_balance_inr: float
    stressed_minimum_cash_balance_inr: float
    minimum_cash_change_inr: float
    
    first_stressed_reserve_breach_month: Optional[int]
    baseline_first_reserve_breach_month: Optional[int]
    
    baseline_monthly_surplus_at_horizon_inr: float
    stressed_monthly_surplus_at_horizon_inr: float
    
    remaining_loan_balance_inr: float
    stress_events_applied: int

class UniverseStressComparison(BaseModel):
    summary: UniverseStressSummary
    monthly_projections: List[StressedMonthlyRecord]
