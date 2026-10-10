import argparse
import random
import csv
import json
import os
from app.schemas.analysis import ProfileSchema, DecisionSchema, AssumptionsSchema
from app.simulation.universes import generate_universe_configs
from app.simulation.simulator import simulate_universe

def generate_profile(seed: int, index: int) -> tuple[ProfileSchema, DecisionSchema, AssumptionsSchema]:
    # Use deterministic random based on seed and index
    r = random.Random(seed + index)
    
    monthly_income = round(r.uniform(20000, 300000), 2)
    other_income = round(r.uniform(0, 50000) if r.random() > 0.5 else 0.0, 2)
    
    rent = round(r.uniform(0, monthly_income * 0.5), 2)
    essential = round(r.uniform(5000, 100000), 2)
    variable = round(r.uniform(2000, 50000), 2)
    
    savings = round(r.uniform(0, 2000000), 2)
    existing_emi = round(r.uniform(0, monthly_income * 0.4) if r.random() > 0.3 else 0.0, 2)
    
    profile = ProfileSchema(
        monthly_income_inr=monthly_income,
        other_income_inr=other_income,
        monthly_rent_inr=rent,
        essential_expenses_excluding_rent_inr=essential,
        variable_expenses_inr=variable,
        current_savings_inr=savings,
        existing_monthly_emi_inr=existing_emi
    )
    
    loan_amount = round(r.uniform(50000, 5000000), 2)
    interest_rate = round(r.uniform(7.0, 15.0), 2)
    tenure = r.choice([12, 24, 36, 48, 60, 120, 240])
    upfront = round(r.uniform(0, loan_amount * 0.2), 2)
    
    decision = DecisionSchema(
        type="general",
        amount_inr=loan_amount,
        annual_interest_rate=interest_rate,
        tenure_months=tenure,
        upfront_cash_outflow_inr=upfront
    )
    
    rent_inflation = round(r.uniform(0.0, 10.0), 2)
    essential_inflation = round(r.uniform(0.0, 10.0), 2)
    variable_inflation = round(r.uniform(0.0, 10.0), 2)
    income_growth = round(r.uniform(0.0, 15.0), 2)
    horizon = r.choice([12, 24, 36])
    
    assumptions = AssumptionsSchema(
        annual_rent_inflation_pct=rent_inflation,
        annual_essential_expense_inflation_pct=essential_inflation,
        annual_variable_expense_inflation_pct=variable_inflation,
        annual_income_growth_pct=income_growth,
        simulation_horizon_months=horizon
    )
    
    return profile, decision, assumptions

def calculate_stress_label(projection):
    # financial_stress_label = 1 if closing cash balance < total_monthly_outflow in any month >= 1
    for p in projection[1:]: # Skip month 0
        if p.closing_cash_balance_inr < p.total_monthly_outflow_inr:
            return 1, p.month
    return 0, None

def generate_dataset(num_profiles: int, seed: int, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    
    training_file = os.path.join(output_dir, "futurefund_synthetic_training_v2.csv")
    outcomes_file = os.path.join(output_dir, "futurefund_synthetic_simulation_outcomes_v2.csv")
    manifest_file = os.path.join(output_dir, "manifest.json")
    
    # Avoid overwriting existing files silently if they exist with exact paths, 
    # but the instructions specified saving to data/v2 which is new.
    
    training_rows = []
    outcome_rows = []
    
    stress_counts = {0: 0, 1: 0}
    universe_counts = {"act_now": 0, "wait_prepare": 0, "reimagine": 0}
    
    for i in range(num_profiles):
        profile_id = f"prof_{i+1}"
        profile, decision, assumptions = generate_profile(seed, i)
        
        configs = generate_universe_configs(decision)
        
        for config in configs:
            record_id = f"{profile_id}_{config.universe_id}"
            universe_counts[config.universe_id] += 1
            
            sim_result = simulate_universe(profile, config, assumptions)
            
            stress_label, breach_month = calculate_stress_label(sim_result.projection)
            stress_counts[stress_label] += 1
            
            # Training row (only inputs and label)
            training_rows.append({
                "record_id": record_id,
                "profile_id": profile_id,
                "universe_id": config.universe_id,
                "monthly_income_inr": profile.monthly_income_inr,
                "other_income_inr": profile.other_income_inr,
                "monthly_rent_inr": profile.monthly_rent_inr,
                "essential_expenses_excluding_rent_inr": profile.essential_expenses_excluding_rent_inr,
                "variable_expenses_inr": profile.variable_expenses_inr,
                "current_savings_inr": profile.current_savings_inr,
                "existing_monthly_emi_inr": profile.existing_monthly_emi_inr,
                "original_proposed_loan_amount_inr": decision.amount_inr,
                "configured_loan_amount_inr": config.loan_amount_inr,
                "annual_interest_rate_pct": config.annual_interest_rate_pct,
                "tenure_months": config.tenure_months,
                "decision_delay_months": config.decision_delay_months,
                "upfront_cash_outflow_inr": config.upfront_cash_outflow_inr,
                "annual_rent_inflation_pct": assumptions.annual_rent_inflation_pct,
                "annual_essential_expense_inflation_pct": assumptions.annual_essential_expense_inflation_pct,
                "annual_variable_expense_inflation_pct": assumptions.annual_variable_expense_inflation_pct,
                "annual_income_growth_pct": assumptions.annual_income_growth_pct,
                "simulation_horizon_months": assumptions.simulation_horizon_months,
                "financial_stress_label": stress_label
            })
            
            # Outcome row
            outcome_rows.append({
                "record_id": record_id,
                "profile_id": profile_id,
                "universe_id": config.universe_id,
                "configured_loan_amount_inr": config.loan_amount_inr,
                "decision_start_month": config.decision_delay_months,
                "scheduled_emi_inr": sim_result.summary.scheduled_emi_inr,
                "total_interest_full_loan_inr": sim_result.summary.total_interest_full_loan_inr,
                "interest_paid_within_horizon_inr": sim_result.summary.interest_paid_within_horizon_inr,
                "total_projected_income_inr": sim_result.summary.total_projected_income_inr,
                "total_projected_living_expenses_inr": sim_result.summary.total_projected_living_expenses_inr,
                "ending_cash_balance_inr": sim_result.summary.ending_projected_cash_balance_inr,
                "minimum_cash_balance_inr": sim_result.summary.minimum_projected_cash_balance_inr,
                "month_of_minimum_cash_balance": sim_result.summary.month_of_minimum_cash_balance,
                "remaining_loan_balance_at_horizon_inr": sim_result.summary.remaining_loan_balance_at_horizon_inr,
                "first_reserve_threshold_breach_month": breach_month if breach_month is not None else "",
                "financial_stress_label": stress_label
            })
            
    # Write files
    with open(training_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=training_rows[0].keys())
        writer.writeheader()
        writer.writerows(training_rows)
        
    with open(outcomes_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=outcome_rows[0].keys())
        writer.writeheader()
        writer.writerows(outcome_rows)
        
    # Write manifest
    manifest = {
        "version": "2.0",
        "seed": seed,
        "base_profiles_generated": num_profiles,
        "total_scenario_records": len(training_rows),
        "target_definition": "financial_stress_label = 1 if closing_cash_balance_inr < total_monthly_outflow_inr for any month >= 1",
        "universe_counts": universe_counts,
        "label_distribution": stress_counts
    }
    
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=4)
        
    print(f"Generated {num_profiles} profiles -> {len(training_rows)} scenario records.")
    print(f"Label distribution: {stress_counts}")
    print(f"Files saved to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", type=int, default=5000, help="Number of base profiles")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--outdir", type=str, default="../data/v2", help="Output directory")
    args = parser.parse_args()
    
    if not os.path.isabs(args.outdir):
        out_path = os.path.abspath(args.outdir)
    else:
        out_path = args.outdir
        
    generate_dataset(args.profiles, args.seed, out_path)
