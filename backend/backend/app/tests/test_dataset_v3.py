"""Tests for the V3 dataset generator (100k source ingestion)."""
import pytest
import os
import csv
import json
import tempfile
from app.ml.generate_data_v3 import generate_v3_dataset

# Resolve the source CSV used across tests
_SOURCE = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "source",
    "FinMultiverse_100k_refined_training_dataset.csv"
))

@pytest.fixture
def pilot_dir():
    """Generate a small 10-profile pilot in a temp directory."""
    with tempfile.TemporaryDirectory() as td:
        generate_v3_dataset(
            source_path=_SOURCE,
            max_profiles=10,
            seed=42,
            output_dir=td,
        )
        yield td

# ── reproducibility ──────────────────────────────────────────────────────────

def test_reproducibility():
    with tempfile.TemporaryDirectory() as d1, \
         tempfile.TemporaryDirectory() as d2:
        generate_v3_dataset(_SOURCE, max_profiles=10, seed=42, output_dir=d1)
        generate_v3_dataset(_SOURCE, max_profiles=10, seed=42, output_dir=d2)

        f1 = os.path.join(d1, "futurefund_training_v3.csv")
        f2 = os.path.join(d2, "futurefund_training_v3.csv")
        assert open(f1).read() == open(f2).read()

# ── structure ────────────────────────────────────────────────────────────────

def test_row_counts(pilot_dir):
    train = _read(pilot_dir, "futurefund_training_v3.csv")
    outcomes = _read(pilot_dir, "futurefund_outcomes_v3.csv")
    assert len(train) == 30       # 10 profiles × 3 universes
    assert len(outcomes) == 30

def test_three_universes_per_profile(pilot_dir):
    train = _read(pilot_dir, "futurefund_training_v3.csv")
    from collections import Counter
    profile_counts = Counter(r["profile_id"] for r in train)
    for pid, cnt in profile_counts.items():
        assert cnt == 3, f"{pid} has {cnt} rows, expected 3"

def test_unique_record_ids(pilot_dir):
    train = _read(pilot_dir, "futurefund_training_v3.csv")
    ids = [r["record_id"] for r in train]
    assert len(ids) == len(set(ids)), "Duplicate record_ids found"

def test_valid_horizons(pilot_dir):
    train = _read(pilot_dir, "futurefund_training_v3.csv")
    for r in train:
        assert int(r["simulation_horizon_months"]) in (12, 24, 36)

# ── no leakage ───────────────────────────────────────────────────────────────

def test_no_outcome_leakage(pilot_dir):
    train = _read(pilot_dir, "futurefund_training_v3.csv")
    leak_cols = {
        "ending_cash_balance_inr", "minimum_cash_balance_inr",
        "first_reserve_threshold_breach_month",
        "total_projected_income_inr", "total_projected_living_expenses_inr",
        "month_of_minimum_cash_balance",
    }
    for col in leak_cols:
        assert col not in train[0], f"Leaked column '{col}' in training"

# ── target validity ──────────────────────────────────────────────────────────

def test_binary_labels(pilot_dir):
    train = _read(pilot_dir, "futurefund_training_v3.csv")
    for r in train:
        assert int(r["financial_stress_label"]) in (0, 1)

def test_id_correspondence(pilot_dir):
    train = _read(pilot_dir, "futurefund_training_v3.csv")
    outcomes = _read(pilot_dir, "futurefund_outcomes_v3.csv")
    assert ([r["record_id"] for r in train]
            == [r["record_id"] for r in outcomes])

# ── helper ───────────────────────────────────────────────────────────────────

def _read(d, name):
    with open(os.path.join(d, name), "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))
