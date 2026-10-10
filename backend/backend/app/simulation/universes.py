from app.schemas.analysis import DecisionSchema
from app.schemas.simulation import UniverseConfiguration

def generate_universe_configs(decision: DecisionSchema, custom_reimagine_amount: float = None) -> list[UniverseConfiguration]:
    # Universe A: Act Now
    univ_a = UniverseConfiguration(
        universe_id="act_now",
        display_name="Act Now",
        loan_amount_inr=decision.amount_inr,
        decision_delay_months=0,
        upfront_cash_outflow_inr=decision.upfront_cash_outflow_inr or 0.0,
        annual_interest_rate_pct=decision.annual_interest_rate,
        tenure_months=decision.tenure_months
    )
    
    # Universe B: Wait & Prepare (6-month delay)
    univ_b = UniverseConfiguration(
        universe_id="wait_prepare",
        display_name="Wait & Prepare",
        loan_amount_inr=decision.amount_inr,
        decision_delay_months=6,
        upfront_cash_outflow_inr=decision.upfront_cash_outflow_inr or 0.0,
        annual_interest_rate_pct=decision.annual_interest_rate,
        tenure_months=decision.tenure_months
    )
    
    # Universe C: Reimagine the Plan (smaller loan amount)
    if custom_reimagine_amount is not None:
        reimagine_amount = custom_reimagine_amount
    else:
        # Default scenario is 70% of proposed amount, rounded to nearest 1,000
        reimagine_amount = round((decision.amount_inr * 0.7) / 1000) * 1000.0
        
    univ_c = UniverseConfiguration(
        universe_id="reimagine",
        display_name="Reimagine the Plan",
        loan_amount_inr=reimagine_amount,
        decision_delay_months=0,
        upfront_cash_outflow_inr=decision.upfront_cash_outflow_inr or 0.0,
        annual_interest_rate_pct=decision.annual_interest_rate,
        tenure_months=decision.tenure_months
    )
    
    return [univ_a, univ_b, univ_c]
