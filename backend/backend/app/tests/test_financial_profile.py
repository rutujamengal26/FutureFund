import pytest
from app.schemas.analysis import ProfileSchema
from app.financial.calculations import calculate_financial_position
import math

def test_calculate_financial_position_standard():
    profile = ProfileSchema(
        monthly_income_inr=100000.0,
        other_income_inr=10000.0,
        monthly_rent_inr=25000.0,
        essential_expenses_excluding_rent_inr=15000.0,
        variable_expenses_inr=10000.0,
        current_savings_inr=500000.0,
        existing_monthly_emi_inr=5000.0
    )
    
    pos = calculate_financial_position(profile, proposed_emi=20000.0)
    
    assert pos.total_monthly_income_inr == 110000.0
    assert pos.current_monthly_living_expenses_inr == 50000.0 # 25k + 15k + 10k
    assert pos.current_monthly_outflow_inr == 55000.0 # 50k + 5k
    assert pos.current_monthly_surplus_inr == 55000.0 # 110k - 55k
    assert pos.monthly_surplus_after_proposed_loan_inr == 35000.0 # 55k - 20k
    assert pos.total_monthly_debt_payments_inr == 25000.0 # 5k + 20k
    assert math.isclose(pos.debt_to_income_ratio_pct, (25000.0 / 110000.0) * 100, abs_tol=0.01) # type: ignore
    
    assert math.isclose(pos.reserve_coverage_months_current, 500000.0 / 55000.0, abs_tol=0.01) # type: ignore
    assert math.isclose(pos.reserve_coverage_months_proposed, 500000.0 / 75000.0, abs_tol=0.01) # type: ignore

def test_calculate_financial_position_zero_income():
    profile = ProfileSchema(
        monthly_income_inr=0.0,
        other_income_inr=0.0,
        monthly_rent_inr=10000.0,
        essential_expenses_excluding_rent_inr=5000.0,
        variable_expenses_inr=0.0,
        current_savings_inr=50000.0,
        existing_monthly_emi_inr=0.0
    )
    
    pos = calculate_financial_position(profile, proposed_emi=0.0)
    
    assert pos.total_monthly_income_inr == 0.0
    assert pos.debt_to_income_ratio_pct is None
