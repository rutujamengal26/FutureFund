from pydantic import BaseModel, Field
from typing import List, Optional

class AmortizationRow(BaseModel):
    month: int
    opening_balance: float
    scheduled_emi: float
    interest_component: float
    principal_component: float
    closing_balance: float

class AmortizationSchedule(BaseModel):
    schedule: List[AmortizationRow]
    total_paid: float
    total_interest: float
    final_balance: float

class FinancialPosition(BaseModel):
    total_monthly_income_inr: float
    current_monthly_living_expenses_inr: float
    current_monthly_outflow_inr: float
    current_monthly_surplus_inr: float
    proposed_loan_emi_inr: float
    monthly_surplus_after_proposed_loan_inr: float
    total_monthly_debt_payments_inr: float
    debt_to_income_ratio_pct: Optional[float] = Field(None, description="Percentage of income going to debt")
    reserve_coverage_months_current: Optional[float] = Field(None, description="Months of current outflows covered by savings")
    reserve_coverage_months_proposed: Optional[float] = Field(None, description="Months of proposed outflows covered by savings")

class FinancialFeatures(BaseModel):
    total_monthly_income: float
    current_monthly_living_expenses: float
    current_monthly_surplus: float
    proposed_emi: float
    monthly_surplus_after_proposed_emi: float
    existing_emi_burden: float
    proposed_emi_burden: float
    debt_to_income_ratio: Optional[float]
    reserve_coverage: Optional[float]
