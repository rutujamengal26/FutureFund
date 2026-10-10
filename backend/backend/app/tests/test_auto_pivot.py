import pytest
from pydantic import ValidationError
from app.schemas.analysis import ProfileSchema, DecisionSchema, AssumptionsSchema
from app.schemas.auto_pivot import AutoPivotRequest, UserConstraints, SearchConfiguration
from app.simulation.auto_pivot import find_alternatives

@pytest.fixture
def base_profile():
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
def base_decision():
    return DecisionSchema(
        type="car",
        amount_inr=500000.0,
        annual_interest_rate=10.0,
        tenure_months=60,
        upfront_cash_outflow_inr=50000.0
    )

@pytest.fixture
def base_assumptions():
    return AssumptionsSchema(
        annual_rent_inflation_pct=5.0,
        annual_essential_expense_inflation_pct=5.0,
        annual_variable_expense_inflation_pct=5.0,
        annual_income_growth_pct=10.0,
        simulation_horizon_months=12
    )

def test_original_appears_as_baseline(base_profile, base_decision, base_assumptions):
    req = AutoPivotRequest(profile=base_profile, decision=base_decision, assumptions=base_assumptions)
    res = find_alternatives(req)
    
    assert res.baseline_candidate_id == "baseline_original"
    baseline = next(c for c in res.candidates if c.candidate_id == "baseline_original")
    
    assert baseline.configuration.loan_amount_inr == 500000.0
    assert baseline.configuration.decision_delay_months == 0
    assert baseline.configuration.tenure_months == 60

def test_candidate_ids_unique(base_profile, base_decision, base_assumptions):
    req = AutoPivotRequest(profile=base_profile, decision=base_decision, assumptions=base_assumptions)
    res = find_alternatives(req)
    
    ids = [c.candidate_id for c in res.candidates]
    assert len(ids) == len(set(ids))

def test_candidate_limits_respected(base_profile, base_decision, base_assumptions):
    req = AutoPivotRequest(
        profile=base_profile, decision=base_decision, assumptions=base_assumptions,
        search_config=SearchConfiguration(max_candidates=5)
    )
    res = find_alternatives(req)
    assert len(res.candidates) == 5

def test_smaller_loan_amount_recalculates_emi(base_profile, base_decision, base_assumptions):
    req = AutoPivotRequest(
        profile=base_profile, decision=base_decision, assumptions=base_assumptions,
        search_config=SearchConfiguration(max_candidates=100)
    )
    res = find_alternatives(req)
    
    baseline = next(c for c in res.candidates if c.candidate_id == "baseline_original")
    smaller = next(c for c in res.candidates if c.configuration.loan_amount_inr < 500000.0)
    
    # Same tenure
    smaller_same_tenure = next(c for c in res.candidates if c.configuration.loan_amount_inr < 500000.0 and c.configuration.tenure_months == 60)
    
    assert smaller_same_tenure.configuration.scheduled_emi_inr < baseline.configuration.scheduled_emi_inr

def test_changed_tenure_recalculates_interest(base_profile, base_decision, base_assumptions):
    req = AutoPivotRequest(
        profile=base_profile, decision=base_decision, assumptions=base_assumptions,
        search_config=SearchConfiguration(max_candidates=100)
    )
    res = find_alternatives(req)
    
    baseline = next(c for c in res.candidates if c.candidate_id == "baseline_original")
    shorter_tenure = next(c for c in res.candidates if c.configuration.loan_amount_inr == 500000.0 and c.configuration.tenure_months < 60)
    
    assert shorter_tenure.baseline_summary.total_interest_full_loan_inr < baseline.baseline_summary.total_interest_full_loan_inr

def test_stress_scenario_applied(base_profile, base_decision, base_assumptions):
    req = AutoPivotRequest(
        profile=base_profile, decision=base_decision, assumptions=base_assumptions,
        stress_scenario_id="emergency_expense",
        search_config=SearchConfiguration(max_candidates=2)
    )
    res = find_alternatives(req)
    
    for c in res.candidates:
        assert c.stress_summary is not None
        assert c.stress_summary.ending_cash_change_inr < 0

def test_constraint_checking_hard(base_profile, base_decision, base_assumptions):
    req = AutoPivotRequest(
        profile=base_profile, decision=base_decision, assumptions=base_assumptions,
        constraints=UserConstraints(maximum_decision_delay_months=0)
    )
    res = find_alternatives(req)
    
    # Candidates with delay > 0 should be ineligible
    delayed = [c for c in res.candidates if c.configuration.decision_delay_months > 0]
    for d in delayed:
        assert not d.is_eligible
        
    immediate = [c for c in res.candidates if c.configuration.decision_delay_months == 0]
    # Check if they are eligible (assuming they pass other implied/default things)
    assert immediate[0].is_eligible

def test_no_candidate_passes(base_profile, base_decision, base_assumptions):
    req = AutoPivotRequest(
        profile=base_profile, decision=base_decision, assumptions=base_assumptions,
        constraints=UserConstraints(maximum_monthly_emi_inr=1.0) # impossible
    )
    res = find_alternatives(req)
    
    assert res.eligible_candidates == 0
    assert res.recommended_candidate_id is None
    for c in res.candidates:
        assert not c.is_eligible

def test_ranking_deterministic(base_profile, base_decision, base_assumptions):
    req1 = AutoPivotRequest(profile=base_profile, decision=base_decision, assumptions=base_assumptions)
    req2 = AutoPivotRequest(profile=base_profile, decision=base_decision, assumptions=base_assumptions)
    
    res1 = find_alternatives(req1)
    res2 = find_alternatives(req2)
    
    assert [c.candidate_id for c in res1.candidates] == [c.candidate_id for c in res2.candidates]
    assert res1.recommended_candidate_id == res2.recommended_candidate_id

def test_longer_tenure_not_automatically_better(base_profile, base_decision, base_assumptions):
    req = AutoPivotRequest(
        profile=base_profile, decision=base_decision, assumptions=base_assumptions,
        search_config=SearchConfiguration(ranking_objective="minimize_total_interest", max_candidates=20)
    )
    res = find_alternatives(req)
    
    # Top ranked should be shorter tenure if all else is equal, because minimize_total_interest
    top = res.candidates[0]
    # It should have a short tenure (12 is min)
    assert top.configuration.tenure_months == 12

def test_invalid_constraints_rejected():
    with pytest.raises(ValidationError):
        UserConstraints(maximum_monthly_emi_inr="invalid")

