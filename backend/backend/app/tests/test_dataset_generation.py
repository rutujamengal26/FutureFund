import pytest
import os
import csv
import tempfile
from app.ml.generate_data import generate_dataset

def test_dataset_reproducibility():
    with tempfile.TemporaryDirectory() as temp_dir:
        dir1 = os.path.join(temp_dir, "run1")
        dir2 = os.path.join(temp_dir, "run2")
        
        generate_dataset(num_profiles=10, seed=42, output_dir=dir1)
        generate_dataset(num_profiles=10, seed=42, output_dir=dir2)
        
        # Read the training files
        file1 = os.path.join(dir1, "futurefund_synthetic_training_v2.csv")
        file2 = os.path.join(dir2, "futurefund_synthetic_training_v2.csv")
        
        with open(file1, "r") as f1, open(file2, "r") as f2:
            content1 = f1.read()
            content2 = f2.read()
            
        assert content1 == content2, "Dataset generation with same seed should be perfectly identical"

def test_dataset_leakage_and_structure():
    with tempfile.TemporaryDirectory() as temp_dir:
        generate_dataset(num_profiles=5, seed=10, output_dir=temp_dir)
        
        training_file = os.path.join(temp_dir, "futurefund_synthetic_training_v2.csv")
        outcomes_file = os.path.join(temp_dir, "futurefund_synthetic_simulation_outcomes_v2.csv")
        
        with open(training_file, "r") as f:
            train_reader = list(csv.DictReader(f))
            
        with open(outcomes_file, "r") as f:
            outcomes_reader = list(csv.DictReader(f))
            
        assert len(train_reader) == 15 # 5 profiles * 3 universes
        assert len(outcomes_reader) == 15
        
        # Check leakage constraints in training
        first_row = train_reader[0]
        assert "minimum_cash_balance_inr" not in first_row
        assert "ending_cash_balance_inr" not in first_row
        assert "first_reserve_threshold_breach_month" not in first_row
        
        # Target constraints
        labels = [int(r["financial_stress_label"]) for r in train_reader]
        assert all(lbl in (0, 1) for lbl in labels)
        
        # Match training rows with outcome rows
        assert [r["record_id"] for r in train_reader] == [r["record_id"] for r in outcomes_reader]
        
        # Check valid horizons
        for row in train_reader:
            assert int(row["simulation_horizon_months"]) in (12, 24, 36)
