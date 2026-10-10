"""
FutureFund Phase 3 — Dataset V3 Generator

Ingests base profiles from the existing FinMultiverse 100k dataset, assigns
deterministic inflation/growth assumptions, runs each through the Phase 2
multi-universe simulator, and derives financial_stress_label from actual
monthly projections.

The original dataset's financial_stress_label is IGNORED — we recompute it
from our own simulator output.

Usage:
    python -m app.ml.generate_data_v3 --profiles 100 --seed 42 --outdir ../data/v3_pilot
    python -m app.ml.generate_data_v3 --profiles 0 --seed 42 --outdir ../data/v3
    (--profiles 0 means "use all available rows")
"""
import argparse
import random
import csv
import json
import os
import sys
import time

from app.schemas.analysis import ProfileSchema, DecisionSchema, AssumptionsSchema
from app.simulation.universes import generate_universe_configs
from app.simulation.simulator import simulate_universe


# ─── source dataset path (relative to backend/) ─────────────────────────────
SOURCE_CSV = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "source",
    "FinMultiverse_100k_refined_training_dataset.csv"
)

# Documented assumption ranges for the inflation/growth parameters that the
# source dataset lacks.  Values are assigned deterministically per-profile
# using a seeded RNG so results are fully reproducible.
ASSUMPTION_RANGES = {
    "annual_rent_inflation_pct":              (0.0, 10.0),
    "annual_essential_expense_inflation_pct":  (0.0, 10.0),
    "annual_variable_expense_inflation_pct":   (0.0,  8.0),
    "annual_income_growth_pct":                (0.0, 15.0),
}


# ─── helpers ─────────────────────────────────────────────────────────────────

def _load_source_profiles(source_path: str, max_profiles: int = 0):
    """Read the source CSV and return a list of dicts (one per row)."""
    resolved = os.path.normpath(source_path)
    if not os.path.isfile(resolved):
        raise FileNotFoundError(f"Source dataset not found: {resolved}")

    with open(resolved, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if max_profiles > 0:
        rows = rows[:max_profiles]
    return rows


def _row_to_schemas(row: dict, rng: random.Random):
    """
    Convert one source CSV row into (ProfileSchema, DecisionSchema,
    AssumptionsSchema) using the existing Pydantic models.

    Inflation/growth assumptions are generated deterministically from *rng*.
    The source dataset's own financial_stress_label is discarded.
    """
    profile = ProfileSchema(
        monthly_income_inr=float(row["monthly_income_inr"]),
        other_income_inr=float(row["other_monthly_income_inr"]),
        monthly_rent_inr=float(row["monthly_rent_inr"]),
        essential_expenses_excluding_rent_inr=float(row["monthly_essential_expenses_excl_rent_inr"]),
        variable_expenses_inr=float(row["monthly_variable_expenses_inr"]),
        current_savings_inr=float(row["current_savings_inr"]),
        existing_monthly_emi_inr=float(row["existing_monthly_emi_inr"]),
    )

    decision = DecisionSchema(
        type=row["decision_type"],
        amount_inr=float(row["proposed_loan_amount_inr"]),
        annual_interest_rate=float(row["annual_interest_rate_pct"]),
        tenure_months=int(row["loan_tenure_months"]),
        upfront_cash_outflow_inr=float(row["upfront_cash_outflow_inr"]),
    )

    # The source CSV already has simulation_horizon_months — reuse it.
    horizon = int(row["simulation_horizon_months"])
    if horizon not in (12, 24, 36):
        horizon = 12  # fall back to safe default

    assumptions = AssumptionsSchema(
        annual_rent_inflation_pct=round(
            rng.uniform(*ASSUMPTION_RANGES["annual_rent_inflation_pct"]), 2),
        annual_essential_expense_inflation_pct=round(
            rng.uniform(*ASSUMPTION_RANGES["annual_essential_expense_inflation_pct"]), 2),
        annual_variable_expense_inflation_pct=round(
            rng.uniform(*ASSUMPTION_RANGES["annual_variable_expense_inflation_pct"]), 2),
        annual_income_growth_pct=round(
            rng.uniform(*ASSUMPTION_RANGES["annual_income_growth_pct"]), 2),
        simulation_horizon_months=horizon,
    )

    return profile, decision, assumptions


def calculate_stress_label(projection):
    """
    financial_stress_label = 1 if, in at least one projected month >= 1,
    closing_cash_balance < that month's total_monthly_outflow.
    """
    for p in projection[1:]:          # skip month 0
        if p.closing_cash_balance_inr < p.total_monthly_outflow_inr:
            return 1, p.month
    return 0, None


# ─── main generator ─────────────────────────────────────────────────────────

def generate_v3_dataset(
    source_path: str,
    max_profiles: int,
    seed: int,
    output_dir: str,
    batch_size: int = 500,
):
    os.makedirs(output_dir, exist_ok=True)

    training_file = os.path.join(output_dir, "futurefund_training_v3.csv")
    outcomes_file = os.path.join(output_dir, "futurefund_outcomes_v3.csv")
    invalid_file  = os.path.join(output_dir, "futurefund_invalid_profiles_v3.csv")
    manifest_file = os.path.join(output_dir, "manifest.json")

    source_rows = _load_source_profiles(source_path, max_profiles)
    total_profiles = len(source_rows)

    training_rows = []
    outcome_rows  = []
    invalid_rows  = []
    stress_counts = {0: 0, 1: 0}
    universe_counts = {"act_now": 0, "wait_prepare": 0, "reimagine": 0}

    t0 = time.time()
    processed = 0

    for idx, row in enumerate(source_rows):
        source_record_id = row.get("record_id", f"row_{idx}")
        profile_id = f"v3_{source_record_id}"

        # Deterministic RNG per-profile for assumptions
        rng = random.Random(seed + idx)

        try:
            profile, decision, assumptions = _row_to_schemas(row, rng)
        except (ValueError, KeyError) as exc:
            invalid_rows.append({
                "profile_id": profile_id,
                "source_record_id": source_record_id,
                "error": str(exc),
            })
            continue

        configs = generate_universe_configs(decision)

        for config in configs:
            record_id = f"{profile_id}_{config.universe_id}"
            universe_counts[config.universe_id] += 1

            sim_result = simulate_universe(profile, config, assumptions)
            stress_label, breach_month = calculate_stress_label(sim_result.projection)
            stress_counts[stress_label] += 1

            # ── training row (inputs only + label) ───────────────────────
            training_rows.append({
                "record_id": record_id,
                "profile_id": profile_id,
                "universe_id": config.universe_id,
                "monthly_income_inr": profile.monthly_income_inr,
                "other_income_inr": profile.other_income_inr,
                "monthly_rent_inr": profile.monthly_rent_inr,
                "essential_expenses_excluding_rent_inr":
                    profile.essential_expenses_excluding_rent_inr,
                "variable_expenses_inr": profile.variable_expenses_inr,
                "current_savings_inr": profile.current_savings_inr,
                "existing_monthly_emi_inr": profile.existing_monthly_emi_inr,
                "original_proposed_loan_amount_inr": decision.amount_inr,
                "configured_loan_amount_inr": config.loan_amount_inr,
                "annual_interest_rate_pct": config.annual_interest_rate_pct,
                "tenure_months": config.tenure_months,
                "decision_delay_months": config.decision_delay_months,
                "upfront_cash_outflow_inr": config.upfront_cash_outflow_inr,
                "annual_rent_inflation_pct":
                    assumptions.annual_rent_inflation_pct,
                "annual_essential_expense_inflation_pct":
                    assumptions.annual_essential_expense_inflation_pct,
                "annual_variable_expense_inflation_pct":
                    assumptions.annual_variable_expense_inflation_pct,
                "annual_income_growth_pct":
                    assumptions.annual_income_growth_pct,
                "simulation_horizon_months":
                    assumptions.simulation_horizon_months,
                "financial_stress_label": stress_label,
            })

            # ── outcome row (simulation results — kept separate) ─────────
            outcome_rows.append({
                "record_id": record_id,
                "profile_id": profile_id,
                "universe_id": config.universe_id,
                "configured_loan_amount_inr": config.loan_amount_inr,
                "decision_start_month": config.decision_delay_months,
                "scheduled_emi_inr":
                    sim_result.summary.scheduled_emi_inr,
                "total_interest_full_loan_inr":
                    sim_result.summary.total_interest_full_loan_inr,
                "interest_paid_within_horizon_inr":
                    sim_result.summary.interest_paid_within_horizon_inr,
                "total_projected_income_inr":
                    sim_result.summary.total_projected_income_inr,
                "total_projected_living_expenses_inr":
                    sim_result.summary.total_projected_living_expenses_inr,
                "ending_cash_balance_inr":
                    sim_result.summary.ending_projected_cash_balance_inr,
                "minimum_cash_balance_inr":
                    sim_result.summary.minimum_projected_cash_balance_inr,
                "month_of_minimum_cash_balance":
                    sim_result.summary.month_of_minimum_cash_balance,
                "remaining_loan_balance_at_horizon_inr":
                    sim_result.summary.remaining_loan_balance_at_horizon_inr,
                "first_reserve_threshold_breach_month":
                    breach_month if breach_month is not None else "",
                "financial_stress_label": stress_label,
            })

        processed += 1
        if processed % batch_size == 0:
            elapsed = time.time() - t0
            print(f"  Processed {processed}/{total_profiles} profiles "
                  f"({elapsed:.1f}s elapsed)")

    # ── write CSV files ──────────────────────────────────────────────────────
    if training_rows:
        with open(training_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=training_rows[0].keys())
            w.writeheader()
            w.writerows(training_rows)

    if outcome_rows:
        with open(outcomes_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=outcome_rows[0].keys())
            w.writeheader()
            w.writerows(outcome_rows)

    if invalid_rows:
        with open(invalid_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=invalid_rows[0].keys())
            w.writeheader()
            w.writerows(invalid_rows)

    # ── manifest ─────────────────────────────────────────────────────────────
    manifest = {
        "version": "3.0",
        "source_file": os.path.basename(source_path),
        "seed": seed,
        "source_profiles_read": total_profiles,
        "valid_profiles_processed": processed,
        "invalid_profiles": len(invalid_rows),
        "total_scenario_records": len(training_rows),
        "target_definition": (
            "financial_stress_label = 1 if closing_cash_balance_inr "
            "< total_monthly_outflow_inr for any month >= 1"
        ),
        "assumption_ranges": {k: list(v)
                              for k, v in ASSUMPTION_RANGES.items()},
        "universe_counts": universe_counts,
        "label_distribution": stress_counts,
    }
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s.")
    print(f"  Valid profiles : {processed}")
    print(f"  Invalid profiles: {len(invalid_rows)}")
    print(f"  Scenario records: {len(training_rows)}")
    print(f"  Label distribution: {stress_counts}")
    print(f"  Files saved to: {output_dir}")


# ─── CLI entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FutureFund V3 dataset generator — "
                    "ingests 100k source profiles and re-simulates them."
    )
    parser.add_argument("--profiles", type=int, default=0,
                        help="Max profiles to process (0 = all)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    parser.add_argument("--outdir", type=str, default="../data/v3",
                        help="Output directory")
    parser.add_argument("--source", type=str, default=None,
                        help="Path to source CSV (defaults to data/source/)")
    args = parser.parse_args()

    src = args.source or os.path.normpath(SOURCE_CSV)
    if not os.path.isabs(src):
        src = os.path.abspath(src)

    out = args.outdir
    if not os.path.isabs(out):
        out = os.path.abspath(out)

    generate_v3_dataset(
        source_path=src,
        max_profiles=args.profiles,
        seed=args.seed,
        output_dir=out,
    )
