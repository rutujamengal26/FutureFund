import pytest
from pydantic import ValidationError
from app.schemas.analysis import ProfileSchema, AssumptionsSchema, DecisionSchema
from app.schemas.stress_test import (
    StressScenario, IncomeReductionEvent, IncomeInterruptionEvent,
    EmergencyExpenseEvent, PermanentExpenseIncreaseEvent
)
from app.simulation.universes import generate_universe_configs
from app.simulation.stress_test import run_stress_test_for_universe, run_stress_test, PRESET_SCENARIOS

@pytest.fixture
def profile():
    return ProfileSchema(
        monthly_income_inr=100000.0,
        other_income_inr=10000.0,
        monthly_rent_inr=30000.0,
        essential_expenses_excluding_rent_inr=20000.0,
        variable_expenses_inr=15000.0,
        current_savings_inr=50000.0,
        existing_monthly_emi_inr=0.0
    )

@pytest.fixture
def decision():
    return DecisionSchema(
        type="car",
        amount_inr=500000.0,
        annual_interest_rate=10.0,
        tenure_months=60,
        upfront_cash_outflow_inr=50000.0
    )

@pytest.fixture
def assumptions():
    return AssumptionsSchema(
        annual_rent_inflation_pct=5.0,
        annual_essential_expense_inflation_pct=5.0,
        annual_variable_expense_inflation_pct=5.0,
        annual_income_growth_pct=10.0,
        simulation_horizon_months=12
    )

@pytest.fixture
def universe_a(decision):
    return generate_universe_configs(decision)[0]

@pytest.fixture
def universe_b(decision):
    return generate_universe_configs(decision)[1]

def test_no_stress_events_equals_baseline(profile, universe_a, assumptions):
    scenario = StressScenario(scenario_id="none", name="None", description="none", events=[])
    comp = run_stress_test_for_universe(profile, universe_a, assumptions, scenario)
    
    assert comp.summary.ending_cash_change_inr == 0.0
    assert comp.summary.minimum_cash_change_inr == 0.0
    assert comp.summary.baseline_ending_cash_balance_inr == comp.summary.stressed_ending_cash_balance_inr
    
    for m in comp.monthly_projections:
        assert m.baseline_projected_income_inr == m.stressed_projected_income_inr
        assert m.baseline_living_expenses_inr == m.stressed_living_expenses_inr
        assert m.baseline_closing_cash_balance_inr == m.stressed_closing_cash_balance_inr
        assert m.cash_balance_difference_inr == 0.0

def test_zero_income_reduction(profile, universe_a, assumptions):
    events = [IncomeReductionEvent(reduction_pct=0.0, start_month=3, duration_months=2)]
    scenario = StressScenario(scenario_id="zero", name="Zero", description="zero", events=events)
    comp = run_stress_test_for_universe(profile, universe_a, assumptions, scenario)
    
    assert comp.summary.ending_cash_change_inr == 0.0

def test_temporary_income_reduction_timing(profile, universe_a, assumptions):
    events = [IncomeReductionEvent(reduction_pct=50.0, start_month=3, duration_months=2, applies_to="primary")]
    scenario = StressScenario(scenario_id="temp_reduction", name="Temp", description="temp", events=events)
    comp = run_stress_test_for_universe(profile, universe_a, assumptions, scenario)
    
    for m in comp.monthly_projections:
        if m.month in [3, 4]:
            assert m.stressed_projected_income_inr < m.baseline_projected_income_inr
        else:
            assert m.stressed_projected_income_inr == m.baseline_projected_income_inr

def test_income_interruption(profile, universe_a, assumptions):
    events = [IncomeInterruptionEvent(start_month=2, duration_months=3, applies_to="both")]
    scenario = StressScenario(scenario_id="interruption", name="Int", description="int", events=events)
    comp = run_stress_test_for_universe(profile, universe_a, assumptions, scenario)
    
    for m in comp.monthly_projections:
        if m.month in [2, 3, 4]:
            assert m.stressed_projected_income_inr == 0.0
            assert m.baseline_projected_income_inr > 0.0
        elif m.month > 0:
            assert m.stressed_projected_income_inr == m.baseline_projected_income_inr

def test_emergency_expense_applied_once(profile, universe_a, assumptions):
    events = [EmergencyExpenseEvent(amount_inr=40000.0, month=6)]
    scenario = StressScenario(scenario_id="emergency", name="Emerg", description="emerg", events=events)
    comp = run_stress_test_for_universe(profile, universe_a, assumptions, scenario)
    
    diff = 0
    for m in comp.monthly_projections:
        if m.month == 6:
            # Closing cash should drop by 40k in month 6 compared to baseline
            # Actually, the cash_balance_difference in month 6 will be -40k, and in subsequent months it will remain -40k
            diff = m.stressed_closing_cash_balance_inr - m.baseline_closing_cash_balance_inr
            assert round(diff, 2) == -40000.0
        elif m.month > 6:
            assert round(m.stressed_closing_cash_balance_inr - m.baseline_closing_cash_balance_inr, 2) == -40000.0

def test_permanent_rent_increase(profile, universe_a, assumptions):
    events = [PermanentExpenseIncreaseEvent(type="rent_increase", increase_pct=10.0, start_month=7)]
    scenario = StressScenario(scenario_id="rent", name="Rent", description="rent", events=events)
    comp = run_stress_test_for_universe(profile, universe_a, assumptions, scenario)
    
    for m in comp.monthly_projections:
        if 0 < m.month < 7:
            assert m.stressed_living_expenses_inr == m.baseline_living_expenses_inr
        elif m.month >= 7:
            assert m.stressed_living_expenses_inr > m.baseline_living_expenses_inr

def test_expense_increases_targeted(profile, universe_a, assumptions):
    # Test that essential increase only affects essential. We check this by observing that living expenses increase, 
    # but since we only expose total living expenses, we can just ensure it goes up by the correct amount.
    events = [PermanentExpenseIncreaseEvent(type="essential_increase", increase_pct=10.0, start_month=5)]
    scenario = StressScenario(scenario_id="ess", name="Ess", description="ess", events=events)
    comp = run_stress_test_for_universe(profile, universe_a, assumptions, scenario)
    
    m5 = comp.monthly_projections[5]
    diff = m5.stressed_living_expenses_inr - m5.baseline_living_expenses_inr
    # Profile essential is 20k. At month 5 with 5% annual inflation, it's a bit higher. 10% of that should be the difference.
    assert diff > 1900  # approximately 10% of 20k

def test_combined_events(profile, decision, assumptions):
    results = run_stress_test(profile, decision, assumptions, "combined_stress")
    
    act_now = results["act_now"]
    assert act_now.summary.stress_events_applied == 4
    assert act_now.summary.ending_cash_change_inr < 0

def test_multiple_universes_same_assumptions(profile, decision, assumptions):
    results = run_stress_test(profile, decision, assumptions, "income_shock")
    
    # All 3 universes should have the event applied
    for uid in ["act_now", "wait_prepare", "reimagine"]:
        comp = results[uid]
        assert comp.summary.stress_events_applied == 1
        m2 = comp.monthly_projections[2]
        assert m2.stressed_projected_income_inr < m2.baseline_projected_income_inr

def test_universe_b_loan_repayment_timing(profile, universe_b, assumptions):
    # Universe B has a 6 month delay. Repayments start in month 7.
    # We apply a stress event in month 4, it should not trigger EMI.
    events = [IncomeReductionEvent(reduction_pct=50.0, start_month=4, duration_months=1)]
    scenario = StressScenario(scenario_id="t", name="t", description="t", events=events)
    comp = run_stress_test_for_universe(profile, universe_b, assumptions, scenario)
    
    m4 = comp.monthly_projections[4]
    assert m4.new_loan_emi_inr == 0.0
    
    m7 = comp.monthly_projections[7]
    assert m7.new_loan_emi_inr > 0.0

def test_negative_cash_balance(profile, universe_a, assumptions):
    # Enormous emergency expense
    events = [EmergencyExpenseEvent(amount_inr=1000000.0, month=2)]
    scenario = StressScenario(scenario_id="huge", name="huge", description="huge", events=events)
    comp = run_stress_test_for_universe(profile, universe_a, assumptions, scenario)
    
    m2 = comp.monthly_projections[2]
    assert m2.stressed_closing_cash_balance_inr < 0.0

def test_reserve_breach_calculation(profile, universe_a, assumptions):
    profile.current_savings_inr = 500000.0  # High savings to avoid early breach
    events = [EmergencyExpenseEvent(amount_inr=1000000.0, month=3)]
    scenario = StressScenario(scenario_id="breach", name="breach", description="breach", events=events)
    comp = run_stress_test_for_universe(profile, universe_a, assumptions, scenario)
    
    assert comp.summary.first_stressed_reserve_breach_month == 3
    # Baseline might not breach at all, or might breach later
    if comp.summary.baseline_first_reserve_breach_month is not None:
        assert comp.summary.baseline_first_reserve_breach_month > 3 or comp.summary.baseline_first_reserve_breach_month == 3

def test_invalid_percentages():
    with pytest.raises(ValidationError):
        IncomeReductionEvent(reduction_pct=-10.0, start_month=3, duration_months=2)
    with pytest.raises(ValidationError):
        IncomeReductionEvent(reduction_pct=110.0, start_month=3, duration_months=2)

def test_invalid_months():
    with pytest.raises(ValidationError):
        EmergencyExpenseEvent(amount_inr=1000.0, month=0)
    with pytest.raises(ValidationError):
        IncomeReductionEvent(reduction_pct=10.0, start_month=-1, duration_months=2)

def test_invalid_durations():
    with pytest.raises(ValidationError):
        IncomeReductionEvent(reduction_pct=10.0, start_month=1, duration_months=0)

def test_negative_emergency_expense():
    with pytest.raises(ValidationError):
        EmergencyExpenseEvent(amount_inr=-1000.0, month=1)
