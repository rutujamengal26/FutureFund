import pytest
from app.schemas.analysis import ProfileSchema
from app.financial.features import extract_financial_features

def test_extract_financial_features():
    profile = ProfileSchema(
        monthly_income_inr=100000.0,
        other_income_inr=10000.0,
        monthly_rent_inr=25000.0,
        essential_expenses_excluding_rent_inr=15000.0,
        variable_expenses_inr=10000.0,
        current_savings_inr=500000.0,
        existing_monthly_emi_inr=5000.0
    )
    
    features = extract_financial_features(profile, proposed_emi=20000.0)
    
    assert features.total_monthly_income == 110000.0
    assert features.current_monthly_living_expenses == 50000.0
    assert features.current_monthly_surplus == 55000.0
    assert features.proposed_emi == 20000.0
    assert features.monthly_surplus_after_proposed_emi == 35000.0
    assert features.existing_emi_burden == 5000.0
    assert features.proposed_emi_burden == 20000.0
    assert features.debt_to_income_ratio is not None
    assert features.reserve_coverage is not None
