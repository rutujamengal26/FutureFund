from typing import List, Dict, Optional
from app.schemas.analysis import ProfileSchema, AssumptionsSchema, DecisionSchema
from app.schemas.simulation import UniverseConfiguration
from app.schemas.stress_test import (
    StressScenario, StressEvent, IncomeReductionEvent, IncomeInterruptionEvent,
    EmergencyExpenseEvent, PermanentExpenseIncreaseEvent, StressedMonthlyRecord,
    UniverseStressSummary, UniverseStressComparison
)
from app.simulation.simulator import simulate_universe
from app.simulation.universes import generate_universe_configs

# Define Preset Scenarios
PRESET_SCENARIOS: Dict[str, StressScenario] = {
    "mild_disruption": StressScenario(
        scenario_id="mild_disruption",
        name="Mild Disruption",
        description="A minor 10% income reduction for 2 months and a permanent 5% rent increase.",
        events=[
            IncomeReductionEvent(reduction_pct=10.0, start_month=3, duration_months=2),
            PermanentExpenseIncreaseEvent(type="rent_increase", increase_pct=5.0, start_month=6)
        ]
    ),
    "income_shock": StressScenario(
        scenario_id="income_shock",
        name="Income Shock",
        description="Complete loss of primary income for 3 months.",
        events=[
            IncomeInterruptionEvent(start_month=2, duration_months=3, applies_to="primary")
        ]
    ),
    "emergency_expense": StressScenario(
        scenario_id="emergency_expense",
        name="Emergency Expense",
        description="A sudden, one-time emergency expense.",
        events=[
            EmergencyExpenseEvent(amount_inr=50000.0, month=4)
        ]
    ),
    "combined_stress": StressScenario(
        scenario_id="combined_stress",
        name="Combined Stress",
        description="Income reduction, emergency expense, and inflation shocks combined.",
        events=[
            IncomeReductionEvent(reduction_pct=20.0, start_month=3, duration_months=3),
            EmergencyExpenseEvent(amount_inr=40000.0, month=6),
            PermanentExpenseIncreaseEvent(type="rent_increase", increase_pct=10.0, start_month=7),
            PermanentExpenseIncreaseEvent(type="essential_increase", increase_pct=5.0, start_month=7)
        ]
    )
}

def get_preset_scenario(scenario_id: str) -> StressScenario:
    if scenario_id not in PRESET_SCENARIOS:
        raise ValueError(f"Unknown preset scenario ID: {scenario_id}")
    return PRESET_SCENARIOS[scenario_id]

def run_stress_test_for_universe(
    profile: ProfileSchema,
    config: UniverseConfiguration,
    assumptions: AssumptionsSchema,
    scenario: StressScenario
) -> UniverseStressComparison:
    """
    Runs the baseline and stressed projections for a single universe and returns a comparison.
    """
    # 1. Run Baseline
    baseline_result = simulate_universe(profile, config, assumptions, stress_events=None)
    
    # 2. Run Stressed
    stressed_result = simulate_universe(profile, config, assumptions, stress_events=scenario.events)
    
    # 3. Combine into comparison
    baseline_summary = baseline_result.summary
    stressed_summary = stressed_result.summary
    
    baseline_proj = baseline_result.projection
    stressed_proj = stressed_result.projection
    
    monthly_comparisons = []
    
    baseline_first_breach: Optional[int] = None
    stressed_first_breach: Optional[int] = None
    
    for i in range(len(baseline_proj)):
        b = baseline_proj[i]
        s = stressed_proj[i]
        
        # Reserve threshold is exactly the committed outflow (living + EMI + any upfront emergency if we wanted to count it, 
        # but in simulator we added emergency_expense to total_outflow_month, which acts as the reserve threshold for that month)
        b_reserve_threshold = b.total_monthly_outflow_inr
        s_reserve_threshold = s.total_monthly_outflow_inr
        
        b_breach = False
        s_breach = False
        
        # Breach happens if closing cash falls strictly below the total outflow for that month (from month 1 onwards)
        if b.month >= 1 and b.closing_cash_balance_inr < b_reserve_threshold:
            b_breach = True
            if baseline_first_breach is None:
                baseline_first_breach = b.month
                
        if s.month >= 1 and s.closing_cash_balance_inr < s_reserve_threshold:
            s_breach = True
            if stressed_first_breach is None:
                stressed_first_breach = s.month
        
        comp = StressedMonthlyRecord(
            month=b.month,
            
            baseline_projected_income_inr=b.projected_monthly_income_inr + b.projected_other_income_inr,
            stressed_projected_income_inr=s.projected_monthly_income_inr + s.projected_other_income_inr,
            
            baseline_living_expenses_inr=b.projected_rent_inr + b.projected_essential_expenses_inr + b.projected_variable_expenses_inr,
            stressed_living_expenses_inr=s.projected_rent_inr + s.projected_essential_expenses_inr + s.projected_variable_expenses_inr,
            
            existing_emi_inr=b.existing_monthly_emi_inr,
            new_loan_emi_inr=b.new_monthly_emi_inr,
            
            baseline_monthly_surplus_inr=b.monthly_surplus_inr,
            stressed_monthly_surplus_inr=s.monthly_surplus_inr,
            
            baseline_closing_cash_balance_inr=b.closing_cash_balance_inr,
            stressed_closing_cash_balance_inr=s.closing_cash_balance_inr,
            cash_balance_difference_inr=s.closing_cash_balance_inr - b.closing_cash_balance_inr,
            
            baseline_reserve_threshold_inr=b_reserve_threshold,
            stressed_reserve_threshold_inr=s_reserve_threshold,
            
            remaining_loan_balance_inr=s.remaining_new_loan_balance_inr,
            
            baseline_reserve_breach=b_breach,
            stressed_reserve_breach=s_breach
        )
        monthly_comparisons.append(comp)

    summary = UniverseStressSummary(
        universe_id=config.universe_id,
        stress_scenario_id=scenario.scenario_id,
        
        baseline_ending_cash_balance_inr=baseline_summary.ending_projected_cash_balance_inr,
        stressed_ending_cash_balance_inr=stressed_summary.ending_projected_cash_balance_inr,
        ending_cash_change_inr=stressed_summary.ending_projected_cash_balance_inr - baseline_summary.ending_projected_cash_balance_inr,
        
        baseline_minimum_cash_balance_inr=baseline_summary.minimum_projected_cash_balance_inr,
        stressed_minimum_cash_balance_inr=stressed_summary.minimum_projected_cash_balance_inr,
        minimum_cash_change_inr=stressed_summary.minimum_projected_cash_balance_inr - baseline_summary.minimum_projected_cash_balance_inr,
        
        first_stressed_reserve_breach_month=stressed_first_breach,
        baseline_first_reserve_breach_month=baseline_first_breach,
        
        baseline_monthly_surplus_at_horizon_inr=baseline_summary.monthly_surplus_end_inr,
        stressed_monthly_surplus_at_horizon_inr=stressed_summary.monthly_surplus_end_inr,
        
        remaining_loan_balance_inr=stressed_summary.remaining_loan_balance_at_horizon_inr,
        stress_events_applied=len(scenario.events)
    )

    return UniverseStressComparison(summary=summary, monthly_projections=monthly_comparisons)

def run_stress_test(
    profile: ProfileSchema,
    decision: DecisionSchema,
    assumptions: AssumptionsSchema,
    scenario_id: str
) -> Dict[str, UniverseStressComparison]:
    """
    Runs the selected stress test scenario across all three standard universes.
    """
    scenario = get_preset_scenario(scenario_id)
    universes = generate_universe_configs(decision)
    
    results = {}
    for config in universes:
        comparison = run_stress_test_for_universe(profile, config, assumptions, scenario)
        results[config.universe_id] = comparison
        
    return results
