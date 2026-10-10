import pytest
from app.schemas.analysis import ProfileSchema, DecisionSchema, AssumptionsSchema
from app.simulation.universes import generate_universe_configs
from app.simulation.simulator import simulate_universe

@pytest.fixture
def base_profile():
    return ProfileSchema(
        monthly_income_inr=100000.0,
        other_income_inr=0.0,
        monthly_rent_inr=20000.0,
        essential_expenses_excluding_rent_inr=15000.0,
        variable_expenses_inr=10000.0,
        current_savings_inr=500000.0,
        existing_monthly_emi_inr=5000.0
    )

@pytest.fixture
def base_decision():
    return DecisionSchema(
        type="car",
        amount_inr=500000.0,
        annual_interest_rate=12.0,
        tenure_months=36,
        upfront_cash_outflow_inr=50000.0
    )

@pytest.fixture
def base_assumptions():
    return AssumptionsSchema(
        annual_rent_inflation_pct=0.0,
        annual_essential_expense_inflation_pct=0.0,
        annual_variable_expense_inflation_pct=0.0,
        annual_income_growth_pct=0.0,
        simulation_horizon_months=12
    )

def test_universe_generation(base_decision):
    configs = generate_universe_configs(base_decision)
    assert len(configs) == 3
    assert configs[0].universe_id == "act_now"
    assert configs[0].decision_delay_months == 0
    assert configs[1].universe_id == "wait_prepare"
    assert configs[1].decision_delay_months == 6
    assert configs[2].universe_id == "reimagine"
    assert configs[2].loan_amount_inr == 350000.0 # 5L * 0.7 = 3.5L

def test_simulate_universe_act_now(base_profile, base_decision, base_assumptions):
    configs = generate_universe_configs(base_decision)
    res = simulate_universe(base_profile, configs[0], base_assumptions)
    
    # Check month 0
    assert len(res.projection) == 13 # 0 to 12
    assert res.projection[0].month == 0
    # Upfront cash outflow subtracted in month 0
    assert res.projection[0].opening_cash_balance_inr == 500000.0
    assert res.projection[0].upfront_cash_outflow_inr == 50000.0
    assert res.projection[0].closing_cash_balance_inr == 450000.0
    
    # Month 1
    assert res.projection[1].month == 1
    assert res.projection[1].opening_cash_balance_inr == 450000.0
    assert res.projection[1].upfront_cash_outflow_inr == 0.0
    assert res.projection[1].new_monthly_emi_inr > 0.0
    
    # Month 12 remaining loan balance matches schedule
    assert res.projection[12].remaining_new_loan_balance_inr > 0.0

def test_simulate_universe_wait_prepare(base_profile, base_decision, base_assumptions):
    configs = generate_universe_configs(base_decision)
    res = simulate_universe(base_profile, configs[1], base_assumptions)
    
    # Month 0: no upfront outflow yet
    assert res.projection[0].upfront_cash_outflow_inr == 0.0
    assert res.projection[0].closing_cash_balance_inr == 500000.0
    assert res.projection[0].new_monthly_emi_inr == 0.0
    
    # Month 1 to 5: no new EMI
    for i in range(1, 6):
        assert res.projection[i].new_monthly_emi_inr == 0.0
        
    # Month 6: Upfront outflow happens
    assert res.projection[6].upfront_cash_outflow_inr == 50000.0
    assert res.projection[6].new_monthly_emi_inr == 0.0
    
    # Month 7: New EMI starts
    assert res.projection[7].new_monthly_emi_inr > 0.0

def test_negative_cash_balance(base_profile, base_decision, base_assumptions):
    # Set huge outflow to force negative cash
    base_decision.upfront_cash_outflow_inr = 600000.0
    configs = generate_universe_configs(base_decision)
    res = simulate_universe(base_profile, configs[0], base_assumptions)
    
    # Starting savings = 500k, upfront = 600k -> month 0 closing = -100k
    assert res.projection[0].closing_cash_balance_inr == -100000.0
    
def test_inflation_effect(base_profile, base_decision, base_assumptions):
    configs = generate_universe_configs(base_decision)
    
    # Set positive inflation on rent and income
    base_assumptions.annual_rent_inflation_pct = 6.0
    base_assumptions.annual_income_growth_pct = 10.0
    
    res = simulate_universe(base_profile, configs[0], base_assumptions)
    
    # Month 1 values should be slightly higher than month 0 equivalents (base)
    assert res.projection[12].projected_rent_inr > res.projection[1].projected_rent_inr
    assert res.projection[12].projected_monthly_income_inr > res.projection[1].projected_monthly_income_inr
