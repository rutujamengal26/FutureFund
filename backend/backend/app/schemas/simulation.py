from pydantic import BaseModel, Field
from typing import List
from app.schemas.analysis import AssumptionsSchema

class UniverseConfiguration(BaseModel):
    universe_id: str
    display_name: str
    loan_amount_inr: float
    decision_delay_months: int
    upfront_cash_outflow_inr: float
    annual_interest_rate_pct: float
    tenure_months: int

class MonthlyProjectionRecord(BaseModel):
    month: int
    projected_monthly_income_inr: float
    projected_other_income_inr: float
    projected_rent_inr: float
    projected_essential_expenses_inr: float
    projected_variable_expenses_inr: float
    existing_monthly_emi_inr: float
    new_monthly_emi_inr: float
    total_monthly_outflow_inr: float
    monthly_surplus_inr: float
    opening_cash_balance_inr: float
    upfront_cash_outflow_inr: float
    closing_cash_balance_inr: float
    remaining_new_loan_balance_inr: float
    cumulative_new_loan_interest_paid_inr: float

class UniverseSummary(BaseModel):
    universe_id: str
    display_name: str
    configured_loan_amount_inr: float
    decision_start_month: int
    scheduled_emi_inr: float
    total_interest_full_loan_inr: float
    interest_paid_within_horizon_inr: float
    monthly_surplus_start_inr: float
    monthly_surplus_end_inr: float
    ending_projected_cash_balance_inr: float
    minimum_projected_cash_balance_inr: float
    month_of_minimum_cash_balance: int
    remaining_loan_balance_at_horizon_inr: float
    total_projected_living_expenses_inr: float
    total_projected_income_inr: float
    assumptions: AssumptionsSchema

class UniverseSimulationResult(BaseModel):
    summary: UniverseSummary
    projection: List[MonthlyProjectionRecord]

class SimulationEngineResult(BaseModel):
    universes: List[UniverseSimulationResult]
