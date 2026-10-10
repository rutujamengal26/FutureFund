import uuid
from typing import List, Dict, Optional, Tuple
from app.schemas.analysis import ProfileSchema, DecisionSchema, AssumptionsSchema
from app.schemas.simulation import UniverseConfiguration
from app.schemas.auto_pivot import (
    AutoPivotRequest, AutoPivotResponse, AutoPivotCandidate,
    ConstraintCheck, CandidateConfiguration, CandidateChange,
    UserConstraints, SearchConfiguration
)
from app.simulation.simulator import simulate_universe
from app.simulation.stress_test import run_stress_test_for_universe, get_preset_scenario
from app.financial.calculations import calculate_emi

def generate_candidate_configs(decision: DecisionSchema, search_config: SearchConfiguration) -> List[UniverseConfiguration]:
    """Generates unique configurations based on the search config, keeping the original as the first item."""
    original_config = UniverseConfiguration(
        universe_id="baseline_original",
        display_name="Original Plan",
        loan_amount_inr=decision.amount_inr,
        decision_delay_months=0,
        upfront_cash_outflow_inr=decision.upfront_cash_outflow_inr or 0.0,
        annual_interest_rate_pct=decision.annual_interest_rate,
        tenure_months=decision.tenure_months
    )
    
    configs = [original_config]
    seen = { (original_config.loan_amount_inr, original_config.decision_delay_months, original_config.tenure_months) }
    
    # We only generate loan variations if original amount > 0
    if decision.amount_inr > 0:
        for mult in search_config.loan_amount_multipliers:
            amt = round((decision.amount_inr * mult) / 1000) * 1000.0
            if amt <= 0: continue
            
            for delay in search_config.decision_delays_months:
                # Respect constraint if possible here? Search config handles raw generation. 
                # Constraints are checked later.
                
                tenures = search_config.tenure_options_months
                if decision.tenure_months not in tenures:
                    tenures = [decision.tenure_months] + tenures
                    
                for tenure in tenures:
                    key = (amt, delay, tenure)
                    if key not in seen:
                        seen.add(key)
                        
                        cfg = UniverseConfiguration(
                            universe_id=f"cand_{len(configs)}",
                            display_name=f"Alternative {len(configs)}",
                            loan_amount_inr=amt,
                            decision_delay_months=delay,
                            upfront_cash_outflow_inr=decision.upfront_cash_outflow_inr or 0.0,
                            annual_interest_rate_pct=decision.annual_interest_rate,
                            tenure_months=tenure
                        )
                        configs.append(cfg)
                        
    # Limit to max_candidates
    return configs[:search_config.max_candidates]

def check_constraints(
    candidate_summary, 
    candidate_config, 
    profile: ProfileSchema, 
    constraints: UserConstraints,
    stress_summary=None
) -> List[ConstraintCheck]:
    checks = []
    
    # We check constraints against the worst case: 
    # if stress_summary is present, use its values for cash and breaches.
    ending_cash = stress_summary.stressed_ending_cash_balance_inr if stress_summary else candidate_summary.ending_projected_cash_balance_inr
    min_cash = stress_summary.stressed_minimum_cash_balance_inr if stress_summary else candidate_summary.minimum_projected_cash_balance_inr
    
    if constraints.minimum_ending_cash_balance_inr is not None:
        checks.append(ConstraintCheck(
            constraint_name="minimum_ending_cash_balance_inr",
            requested_value=constraints.minimum_ending_cash_balance_inr,
            calculated_value=ending_cash,
            is_satisfied=ending_cash >= constraints.minimum_ending_cash_balance_inr
        ))
        
    if constraints.minimum_cash_balance_inr is not None:
        checks.append(ConstraintCheck(
            constraint_name="minimum_cash_balance_inr",
            requested_value=constraints.minimum_cash_balance_inr,
            calculated_value=min_cash,
            is_satisfied=min_cash >= constraints.minimum_cash_balance_inr
        ))
        
    if constraints.maximum_monthly_emi_inr is not None:
        checks.append(ConstraintCheck(
            constraint_name="maximum_monthly_emi_inr",
            requested_value=constraints.maximum_monthly_emi_inr,
            calculated_value=candidate_summary.scheduled_emi_inr,
            is_satisfied=candidate_summary.scheduled_emi_inr <= constraints.maximum_monthly_emi_inr
        ))
        
    if constraints.maximum_debt_to_income_pct is not None:
        # Define DTI as (Existing EMI + New EMI) / Monthly Income
        dti = ((profile.existing_monthly_emi_inr + candidate_summary.scheduled_emi_inr) / profile.monthly_income_inr) * 100
        checks.append(ConstraintCheck(
            constraint_name="maximum_debt_to_income_pct",
            requested_value=constraints.maximum_debt_to_income_pct,
            calculated_value=dti,
            is_satisfied=dti <= constraints.maximum_debt_to_income_pct
        ))
        
    if constraints.maximum_total_interest_inr is not None:
        checks.append(ConstraintCheck(
            constraint_name="maximum_total_interest_inr",
            requested_value=constraints.maximum_total_interest_inr,
            calculated_value=candidate_summary.total_interest_full_loan_inr,
            is_satisfied=candidate_summary.total_interest_full_loan_inr <= constraints.maximum_total_interest_inr
        ))
        
    if constraints.maximum_decision_delay_months is not None:
        checks.append(ConstraintCheck(
            constraint_name="maximum_decision_delay_months",
            requested_value=constraints.maximum_decision_delay_months,
            calculated_value=candidate_config.decision_delay_months,
            is_satisfied=candidate_config.decision_delay_months <= constraints.maximum_decision_delay_months
        ))
        
    if constraints.require_non_negative_monthly_surplus is not None and constraints.require_non_negative_monthly_surplus:
        surplus = stress_summary.stressed_monthly_surplus_at_horizon_inr if stress_summary else candidate_summary.monthly_surplus_end_inr
        checks.append(ConstraintCheck(
            constraint_name="require_non_negative_monthly_surplus",
            requested_value=True,
            calculated_value=surplus >= 0,
            is_satisfied=surplus >= 0
        ))
        
    return checks

def score_candidate(candidate: AutoPivotCandidate, objective: str) -> float:
    """
    Computes a deterministic score for ranking. Higher is better.
    """
    # Base penalty for failing constraints
    score = 0.0 if candidate.is_eligible else -1000000.0
    
    # We normalize some values approximately to create a score.
    # For a real system, these weights would be fine-tuned or user-defined.
    
    # Use stressed metrics if available
    summary = candidate.baseline_summary
    min_cash = candidate.stress_summary.stressed_minimum_cash_balance_inr if candidate.stress_summary else summary.minimum_projected_cash_balance_inr
    ending_cash = candidate.stress_summary.stressed_ending_cash_balance_inr if candidate.stress_summary else summary.ending_projected_cash_balance_inr
    
    # Positive points for preserving cash
    score += (min_cash / 10000) * 1.0  
    score += (ending_cash / 10000) * 0.5
    
    # Negative points for interest
    score -= (summary.total_interest_full_loan_inr / 10000) * 2.0
    
    # Negative points for high EMI
    score -= (summary.scheduled_emi_inr / 1000) * 1.0
    
    if objective == "preserve_cash":
        score += (min_cash / 10000) * 20.0
    elif objective == "minimize_total_interest":
        score -= (summary.total_interest_full_loan_inr / 10000) * 20.0
    elif objective == "reduce_monthly_burden":
        score -= (summary.scheduled_emi_inr / 1000) * 20.0
    # "balanced" uses the default weights above
        
    return score

def generate_trade_offs(candidate: AutoPivotCandidate, original: AutoPivotCandidate) -> List[str]:
    trade_offs = []
    
    if candidate.candidate_id == original.candidate_id:
        return ["This is the original plan."]
        
    cfg = candidate.configuration
    orig_cfg = original.configuration
    
    if cfg.loan_amount_inr < orig_cfg.loan_amount_inr:
        trade_offs.append(f"Reduces loan amount by ₹{orig_cfg.loan_amount_inr - cfg.loan_amount_inr:,.2f}.")
    if cfg.decision_delay_months > orig_cfg.decision_delay_months:
        trade_offs.append(f"Delays decision by {cfg.decision_delay_months - orig_cfg.decision_delay_months} months to build savings.")
    if cfg.tenure_months > orig_cfg.tenure_months:
        trade_offs.append(f"Extends tenure to {cfg.tenure_months} months, lowering EMI but increasing total interest.")
    elif cfg.tenure_months < orig_cfg.tenure_months:
        trade_offs.append(f"Shortens tenure to {cfg.tenure_months} months, raising EMI but saving on total interest.")
        
    # Interest
    int_diff = candidate.baseline_summary.total_interest_full_loan_inr - original.baseline_summary.total_interest_full_loan_inr
    if int_diff < 0:
        trade_offs.append(f"Saves ₹{abs(int_diff):,.2f} in total interest.")
    elif int_diff > 0:
        trade_offs.append(f"Costs an extra ₹{int_diff:,.2f} in total interest.")
        
    if not candidate.is_eligible:
        trade_offs.append("WARNING: Fails one or more of your strict constraints.")
        
    return trade_offs

def find_alternatives(request: AutoPivotRequest) -> AutoPivotResponse:
    # 1. Defaults
    constraints = request.constraints or UserConstraints()
    search_config = request.search_config or SearchConfiguration()
    
    # 2. Generate Configurations
    configs = generate_candidate_configs(request.decision, search_config)
    
    # 3. Evaluate Each
    stress_scenario = get_preset_scenario(request.stress_scenario_id) if request.stress_scenario_id else None
    
    evaluated_candidates = []
    
    for cfg in configs:
        # Baseline simulation
        baseline_result = simulate_universe(request.profile, cfg, request.assumptions)
        
        # Stress simulation (optional)
        stress_summary = None
        if stress_scenario:
            comp = run_stress_test_for_universe(request.profile, cfg, request.assumptions, stress_scenario)
            stress_summary = comp.summary
            
        # Stage A: Constraint Checking
        checks = check_constraints(baseline_result.summary, cfg, request.profile, constraints, stress_summary)
        is_eligible = all(c.is_satisfied for c in checks)
        
        # Build changes
        changes = []
        if cfg.universe_id != "baseline_original":
            if cfg.loan_amount_inr != request.decision.amount_inr:
                changes.append(CandidateChange(metric="loan_amount_inr", original_value=request.decision.amount_inr, candidate_value=cfg.loan_amount_inr))
            if cfg.decision_delay_months != 0:
                changes.append(CandidateChange(metric="decision_delay_months", original_value=0, candidate_value=cfg.decision_delay_months))
            if cfg.tenure_months != request.decision.tenure_months:
                changes.append(CandidateChange(metric="tenure_months", original_value=request.decision.tenure_months, candidate_value=cfg.tenure_months))
        
        cand = AutoPivotCandidate(
            candidate_id=cfg.universe_id,
            configuration=CandidateConfiguration(
                loan_amount_inr=cfg.loan_amount_inr,
                decision_delay_months=cfg.decision_delay_months,
                tenure_months=cfg.tenure_months,
                scheduled_emi_inr=baseline_result.summary.scheduled_emi_inr
            ),
            changes_from_baseline=changes,
            baseline_summary=baseline_result.summary,
            stress_summary=stress_summary,
            constraint_checks=checks,
            is_eligible=is_eligible,
            ranking_score=0.0,
            trade_offs=[]
        )
        evaluated_candidates.append(cand)
        
    # Stage B: Ranking
    original_cand = evaluated_candidates[0]
    
    for cand in evaluated_candidates:
        cand.ranking_score = score_candidate(cand, search_config.ranking_objective)
        cand.trade_offs = generate_trade_offs(cand, original_cand)
        
    # Sort: Eligible first, then by score descending
    evaluated_candidates.sort(key=lambda c: (c.is_eligible, c.ranking_score), reverse=True)
    
    # Assign ranks
    for idx, cand in enumerate(evaluated_candidates):
        cand.rank = idx + 1
        
    eligible_count = sum(1 for c in evaluated_candidates if c.is_eligible)
    recommended_id = evaluated_candidates[0].candidate_id if eligible_count > 0 else None
    
    return AutoPivotResponse(
        analysis_id=str(uuid.uuid4()),
        ranking_objective=search_config.ranking_objective,
        assumptions=request.assumptions,
        baseline_candidate_id="baseline_original",
        candidates=evaluated_candidates,
        eligible_candidates=eligible_count,
        recommended_candidate_id=recommended_id,
        limitations=[
            "Deterministic metrics only; not a guaranteed risk-free forecast.",
            "ML model probabilities are not applied to generated alternatives.",
            "Changes in floating interest rates are not modeled."
        ],
        search_metadata={
            "total_candidates_evaluated": len(evaluated_candidates),
            "stress_scenario_applied": request.stress_scenario_id
        }
    )
