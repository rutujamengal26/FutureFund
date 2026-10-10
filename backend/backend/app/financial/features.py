from app.schemas.analysis import ProfileSchema
from app.schemas.financial import FinancialFeatures
from app.financial.calculations import calculate_financial_position

def extract_financial_features(profile: ProfileSchema, proposed_emi: float = 0.0) -> FinancialFeatures:
    """
    Derives model-ready financial features from validated inputs without target leakage.
    """
    pos = calculate_financial_position(profile, proposed_emi)
    
    return FinancialFeatures(
        total_monthly_income=pos.total_monthly_income_inr,
        current_monthly_living_expenses=pos.current_monthly_living_expenses_inr,
        current_monthly_surplus=pos.current_monthly_surplus_inr,
        proposed_emi=pos.proposed_loan_emi_inr,
        monthly_surplus_after_proposed_emi=pos.monthly_surplus_after_proposed_loan_inr,
        existing_emi_burden=profile.existing_monthly_emi_inr,
        proposed_emi_burden=pos.proposed_loan_emi_inr,
        debt_to_income_ratio=pos.debt_to_income_ratio_pct,
        reserve_coverage=pos.reserve_coverage_months_proposed
    )
