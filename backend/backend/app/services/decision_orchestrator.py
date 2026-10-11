import uuid
from typing import Dict, Any, Optional

from app.schemas.orchestrator import OrchestratorRequest, OrchestratorResponse, MLModelMetadata
from app.schemas.analysis import ProfileSchema, DecisionSchema
from app.schemas.ai import DecisionParseResult, ParsedProfile, ParsedDecision
from app.schemas.auto_pivot import AutoPivotRequest, UserConstraints

from app.ai.decision_parser import parse_decision_text
from app.ai.second_opinion import generate_second_opinion

from app.simulation.universes import generate_universe_configs
from app.simulation.simulator import simulate_universe
from app.simulation.stress_test import run_stress_test
from app.simulation.auto_pivot import find_alternatives

from app.financial.features import extract_financial_features
from app.ml.predict import predict_financial_stress

from sqlalchemy.orm import Session
from app.database.models import User, Decision, AnalysisRun, AnalysisUniverseResult, StressTestRun as DBStressTestRun, AutoPivotRun, AutoPivotRecommendation

def _merge_parsed_data(
    parsed: DecisionParseResult, 
    override_profile: Optional[ProfileSchema], 
    override_decision: Optional[DecisionSchema]
) -> tuple[Optional[ProfileSchema], Optional[DecisionSchema], list[str]]:
    warnings = []
    
    # Apply profile overrides
    final_profile = None
    if override_profile:
        final_profile = override_profile
        if parsed.profile:
            warnings.append("Explicit profile override took precedence over NLP parsed profile.")
    elif parsed.profile:
        try:
            # We must map ParsedProfile which has optional fields to ProfileSchema which requires them
            # This is a naive translation. We just validate the dict.
            final_profile = ProfileSchema(**parsed.profile.model_dump(exclude_none=True))
        except Exception:
            pass # We will handle missing required fields next
            
    final_decision = None
    if override_decision:
        final_decision = override_decision
        if parsed.decision:
            warnings.append("Explicit decision override took precedence over NLP parsed decision.")
    elif parsed.decision:
        try:
            final_decision = DecisionSchema(**parsed.decision.model_dump(exclude_none=True))
        except Exception:
            pass

    return final_profile, final_decision, warnings


def analyze_decision(request: OrchestratorRequest, db: Session = None, current_user: User = None) -> OrchestratorResponse:
    analysis_id = str(uuid.uuid4())
    warnings = []
    
    parsed_result = None
    final_profile = request.profile
    final_decision = request.decision
    
    # 1. AI Parsing if text provided
    if request.text:
        try:
            parsed_result = parse_decision_text(request.text, existing_profile=request.profile)
            if parsed_result.status == "CLARIFICATION_REQUIRED" and not (request.profile and request.decision):
                # If explicit structures weren't provided to override the missing bits, stop here.
                return OrchestratorResponse(
                    status="CLARIFICATION_REQUIRED",
                    analysis_id=analysis_id,
                    parsed_result=parsed_result,
                    validated_profile=request.profile,
                    validated_decision=request.decision,
                    warnings=warnings
                )
                
            # Attempt to merge parsed result with explicit inputs
            fp, fd, merge_warnings = _merge_parsed_data(parsed_result, request.profile, request.decision)
            if fp and not final_profile:
                final_profile = fp
            if fd and not final_decision:
                final_decision = fd
            warnings.extend(merge_warnings)
                
        except Exception as e:
            print(f"DEBUG EXCEPTION: {repr(e)}")
            warnings.append(f"AI Decision Parser failed: {e}")
            if not (final_profile and final_decision):
                pr = DecisionParseResult(
                    status="CLARIFICATION_REQUIRED",
                    missing_fields=["profile", "decision"],
                    clarification_question=f"Our AI service is currently unavailable (Error: {e}). Please provide explicit structural inputs or try again later."
                )
                return OrchestratorResponse(
                    status="CLARIFICATION_REQUIRED",
                    analysis_id=analysis_id,
                    parsed_result=pr,
                    validated_profile=request.profile,
                    validated_decision=request.decision,
                    warnings=warnings
                )

    # 2. Validation of structured inputs
    if not final_profile or not final_decision or not request.assumptions:
        missing = []
        if not final_profile: missing.append("profile")
        if not final_decision: missing.append("decision")
        if not request.assumptions: missing.append("assumptions")
        
        pr = parsed_result or DecisionParseResult(
            status="CLARIFICATION_REQUIRED",
            missing_fields=missing,
            clarification_question=f"Please provide missing structural inputs: {', '.join(missing)}"
        )
        pr.status = "CLARIFICATION_REQUIRED"
        
        return OrchestratorResponse(
            status="CLARIFICATION_REQUIRED",
            analysis_id=analysis_id,
            parsed_result=pr,
            validated_profile=final_profile,
            validated_decision=final_decision,
            warnings=warnings
        )
        
    # At this point, we have complete, validated profile, decision, and assumptions.
    
    # 3. Simulate Universes
    configs = generate_universe_configs(final_decision)
    universes = []
    ml_estimates = {}
    
    for cfg in configs:
        result = simulate_universe(final_profile, cfg, request.assumptions)
        universes.append(result)
        
        # 4. ML Predictions
        # Extract features for the model. Note: ML model uses baseline universe configuration.
        # But wait, predict_financial_stress just takes features. We use the proposed EMI from the current universe.
        features = extract_financial_features(final_profile, proposed_emi=result.summary.scheduled_emi_inr)
        
        # We need to construct a dict containing ALL_FEATURES.
        feature_dict = {
            "universe_id": cfg.universe_id,
            "monthly_income_inr": final_profile.monthly_income_inr,
            "other_income_inr": final_profile.other_income_inr,
            "monthly_rent_inr": final_profile.monthly_rent_inr,
            "essential_expenses_excluding_rent_inr": final_profile.essential_expenses_excluding_rent_inr,
            "variable_expenses_inr": final_profile.variable_expenses_inr,
            "current_savings_inr": final_profile.current_savings_inr,
            "existing_monthly_emi_inr": final_profile.existing_monthly_emi_inr,
            
            "original_proposed_loan_amount_inr": final_decision.amount_inr,
            "configured_loan_amount_inr": cfg.loan_amount_inr,
            "decision_delay_months": cfg.decision_delay_months,
            "upfront_cash_outflow_inr": cfg.upfront_cash_outflow_inr,
            "annual_interest_rate_pct": cfg.annual_interest_rate_pct,
            "tenure_months": cfg.tenure_months,
            
            "annual_rent_inflation_pct": request.assumptions.annual_rent_inflation_pct,
            "annual_essential_expense_inflation_pct": request.assumptions.annual_essential_expense_inflation_pct,
            "annual_variable_expense_inflation_pct": request.assumptions.annual_variable_expense_inflation_pct,
            "annual_income_growth_pct": request.assumptions.annual_income_growth_pct,
            "simulation_horizon_months": request.assumptions.simulation_horizon_months,
            
            "total_monthly_income": features.total_monthly_income,
            "current_monthly_living_expenses": features.current_monthly_living_expenses,
            "current_monthly_surplus": features.current_monthly_surplus,
            "proposed_emi": features.proposed_emi,
            "monthly_surplus_after_proposed_emi": features.monthly_surplus_after_proposed_emi,
            "existing_emi_burden": features.existing_emi_burden,
            "proposed_emi_burden": features.proposed_emi_burden,
            "debt_to_income_ratio": features.debt_to_income_ratio,
            "reserve_coverage": features.reserve_coverage,
        }
        
        try:
            pred = predict_financial_stress(feature_dict)
            ml_estimates[cfg.universe_id] = MLModelMetadata(**pred)
        except Exception as e:
            warnings.append(f"ML Prediction failed for {cfg.universe_id}: {e}")

    # 5. Stress Testing
    stress_results = {}
    if request.stress_scenario_id:
        try:
            stress_results = run_stress_test(
                final_profile, final_decision, request.assumptions, request.stress_scenario_id
            )
        except Exception as e:
            warnings.append(f"Stress test failed: {e}")
            
    # 6. Auto-Pivot
    auto_pivot_resp = None
    if request.auto_pivot_constraints or (final_decision and final_decision.amount_inr > 0):
        try:
            ap_constraints = request.auto_pivot_constraints or UserConstraints(
                require_non_negative_monthly_surplus=True
            )
            ap_req = AutoPivotRequest(
                profile=final_profile,
                decision=final_decision,
                assumptions=request.assumptions,
                constraints=ap_constraints,
                search_config=request.auto_pivot_config,
                stress_scenario_id=request.stress_scenario_id
            )
            auto_pivot_resp = find_alternatives(ap_req)
        except Exception as e:
            warnings.append(f"Auto-Pivot failed: {e}")
            
    # 7. AI Second Opinion
    second_opinion = None
    
    multiple_futures_plans = []
    for u in universes:
        s = u.summary
        multiple_futures_plans.append({
            "plan_name": s.display_name or s.universe_id,
            "scheduled_monthly_emi_inr": s.scheduled_emi_inr,
            "ending_projected_cash_reserve_inr": s.ending_projected_cash_balance_inr,
            "minimum_projected_cash_reserve_inr": s.minimum_projected_cash_balance_inr,
            "remaining_loan_balance_inr": s.remaining_loan_balance_at_horizon_inr,
            "total_interest_paid_inr": s.total_interest_full_loan_inr
        })


    auto_pivot_plans = []
    base_amt = float(final_decision.amount_inr or 500000)
    base_tenure = int(final_decision.tenure_months or 36)
    rate = float(final_decision.annual_interest_rate or 10.5) / 100.0 / 12.0

    p_small = base_amt * 0.8
    emi_small = round((p_small * rate * ((1.0 + rate) ** base_tenure)) / (((1.0 + rate) ** base_tenure) - 1.0)) if rate > 0 else round(p_small / base_tenure)
    auto_pivot_plans.append({
        "plan_name": "Smaller Loan",
        "category": "Auto-Pivot",
        "description": f"Borrow 20% less (₹{int(p_small):,}) over {base_tenure} months",
        "loan_amount_inr": p_small,
        "monthly_emi_inr": emi_small,
        "total_interest_inr": round((emi_small * base_tenure) - p_small),
        "primary_benefit": "Lowest overall borrowing and lower monthly EMI"
    })

    t_long = base_tenure + 12
    emi_long = round((base_amt * rate * ((1.0 + rate) ** t_long)) / (((1.0 + rate) ** t_long) - 1.0)) if rate > 0 else round(base_amt / t_long)
    auto_pivot_plans.append({
        "plan_name": "Longer Tenure",
        "category": "Auto-Pivot",
        "description": f"Extend tenure to {t_long} months with principal ₹{int(base_amt):,}",
        "loan_amount_inr": base_amt,
        "monthly_emi_inr": emi_long,
        "total_interest_inr": round((emi_long * t_long) - base_amt),
        "primary_benefit": "Lowest monthly payment burden to preserve immediate monthly cash flow"
    })

    emi_wait = round((base_amt * rate * ((1.0 + rate) ** base_tenure)) / (((1.0 + rate) ** base_tenure) - 1.0)) if rate > 0 else round(base_amt / base_tenure)
    auto_pivot_plans.append({
        "plan_name": "Wait Before Purchasing",
        "category": "Auto-Pivot",
        "description": "Delay loan start by 6 months to save up cash reserves",
        "loan_amount_inr": base_amt,
        "monthly_emi_inr": emi_wait,
        "total_interest_inr": round((emi_wait * base_tenure) - base_amt),
        "primary_benefit": "Stacks liquid emergency buffer before committing to monthly EMI"
    })

    evidence = {
        "user_profile": {
            "monthly_income_inr": final_profile.monthly_income_inr,
            "monthly_living_expenses_inr": (final_profile.monthly_rent_inr or 0) + (final_profile.essential_expenses_excluding_rent_inr or 0) + (final_profile.variable_expenses_inr or 0),
            "current_savings_inr": final_profile.current_savings_inr,
            "existing_monthly_emi_inr": final_profile.existing_monthly_emi_inr
        },
        "original_decision": final_decision.model_dump(),
        "multiple_futures_plans": multiple_futures_plans,
        "auto_pivot_plans": auto_pivot_plans,
        "assumptions": request.assumptions.model_dump(),
        "universes_summary": [u.summary.model_dump() for u in universes],
        "ml_estimates": {k: v.model_dump() for k, v in ml_estimates.items()}
    }
    
    if stress_results:
        evidence["stress_tests"] = {k: v.summary.model_dump() for k, v in stress_results.items()}
        
    if auto_pivot_resp:
        evidence["auto_pivot_recommended"] = auto_pivot_resp.recommended_candidate_id
        evidence["auto_pivot_eligible_count"] = auto_pivot_resp.eligible_candidates
        
    try:
        second_opinion = generate_second_opinion(evidence)
    except Exception as e:
        warnings.append(f"Second Opinion failed: {e}")

        
    response = OrchestratorResponse(
        status="READY",
        analysis_id=analysis_id,
        parsed_result=parsed_result,
        validated_profile=final_profile,
        validated_decision=final_decision,
        assumptions=request.assumptions,
        universes=universes,
        ml_estimates=ml_estimates,
        stress_tests=stress_results,
        auto_pivot=auto_pivot_resp,
        second_opinion=second_opinion,
        warnings=warnings
    )
    
    if current_user and db:
        print(f"DEBUG: persistence executing for user {current_user.id}")
        # Atomic Persistence
        try:
            db_decision = Decision(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                original_text=request.text,
                normalized_data=final_decision.model_dump(),
                status="READY"
            )
            db.add(db_decision)
            db.flush()
            
            db_analysis = AnalysisRun(
                id=analysis_id,
                user_id=current_user.id,
                decision_id=db_decision.id,
                status="READY",
                simulation_horizon=request.assumptions.simulation_horizon_months,
                request_snapshot=request.model_dump(exclude_none=True),
                response_snapshot=response.model_dump(exclude_none=True),
                metadata_info={"ml_estimates": {k: v.model_dump() for k, v in ml_estimates.items()}}
            )
            db.add(db_analysis)
            
            for u in universes:
                db.add(AnalysisUniverseResult(
                    analysis_id=analysis_id,
                    universe_code=u.summary.universe_id,
                    result_metrics=u.summary.model_dump(),
                    monthly_trajectory=[m.model_dump() for m in u.projection]
                ))
                
            if stress_results:
                for u_id, st in stress_results.items():
                    db.add(DBStressTestRun(
                        analysis_id=analysis_id,
                        scenario_id=st.summary.stress_scenario_id,
                        config_snapshot={"scenario_id": st.summary.stress_scenario_id},
                        baseline_result={"ending_cash": st.summary.baseline_ending_cash_balance_inr},
                        stressed_result=st.summary.model_dump()
                    ))
                    
            if auto_pivot_resp:
                db_ap = AutoPivotRun(
                    analysis_id=analysis_id,
                    constraints_snapshot=request.auto_pivot_constraints.model_dump() if request.auto_pivot_constraints else {},
                    status="COMPLETED",
                    summary_result={"eligible_candidates": auto_pivot_resp.eligible_candidates, "recommended": auto_pivot_resp.recommended_candidate_id}
                )
                db.add(db_ap)
                db.flush() # get id
                
                for cand in auto_pivot_resp.candidates:
                    db.add(AutoPivotRecommendation(
                        auto_pivot_run_id=db_ap.id,
                        rank=cand.rank,
                        candidate_inputs=cand.configuration.model_dump(),
                        computed_result=cand.baseline_summary.model_dump(),
                        is_eligible=cand.is_eligible,
                        rejection_reasons=[c.constraint_name for c in cand.constraint_checks if not c.is_satisfied]
                    ))
                    
            db.commit()
        except Exception as e:
            db.rollback()
            warnings.append(f"Persistence failed: {e}")
            raise ValueError(f"Persistence failed: {e}")
            
    return response
