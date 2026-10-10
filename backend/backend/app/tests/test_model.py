import pytest
import os
import json
import pandas as pd
import numpy as np

from app.ml.preprocessing import create_preprocessing_pipeline, validate_and_filter_features, ALL_FEATURES
from app.ml.predict import predict_financial_stress

def test_feature_allowlist():
    assert "financial_stress_label" not in ALL_FEATURES
    assert "profile_id" not in ALL_FEATURES
    assert "record_id" not in ALL_FEATURES
    assert "ending_cash_balance_inr" not in ALL_FEATURES

def test_preprocessing_handles_unknown_categories():
    pipeline = create_preprocessing_pipeline()
    
    # Create dummy data
    df_train = pd.DataFrame([{f: 1.0 for f in ALL_FEATURES}])
    df_train["universe_id"] = "act_now"
    
    pipeline.fit(df_train)
    
    # Create inference data with unknown category
    df_infer = pd.DataFrame([{f: 1.0 for f in ALL_FEATURES}])
    df_infer["universe_id"] = "unknown_universe"
    
    # Should not raise error
    transformed = pipeline.transform(df_infer)
    assert transformed.shape[0] == 1

def test_predict_financial_stress_valid_input():
    features = {f: 1000.0 for f in ALL_FEATURES}
    features["universe_id"] = "act_now"
    
    result = predict_financial_stress(features)
    
    assert "estimated_probability" in result
    assert "predicted_class" in result
    assert 0.0 <= result["estimated_probability"] <= 1.0

def test_predict_financial_stress_missing_feature():
    features = {f: 1000.0 for f in ALL_FEATURES[:-1]}  # missing one feature
    
    with pytest.raises(ValueError):
        predict_financial_stress(features)

def test_predict_financial_stress_invalid_type():
    features = {f: 1000.0 for f in ALL_FEATURES}
    features["universe_id"] = "act_now"
    features["monthly_income_inr"] = "not a number"
    
    with pytest.raises(ValueError):
        predict_financial_stress(features)
