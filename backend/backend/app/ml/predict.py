import os
import json
import joblib
import pandas as pd
from typing import Dict, Any

from app.ml.preprocessing import ALL_FEATURES

MODELS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "models", "v1"))
PIPELINE_PATH = os.path.join(MODELS_DIR, "xgboost_pipeline.joblib")
METADATA_PATH = os.path.join(MODELS_DIR, "training_metadata.json")
EVAL_PATH = os.path.join(MODELS_DIR, "evaluation_metrics.json")

# Lazy loading of model to avoid reloading on every prediction
_pipeline = None
_metadata = None
_eval_metrics = None

def _load_artifacts():
    global _pipeline, _metadata, _eval_metrics
    if _pipeline is None:
        if not os.path.exists(PIPELINE_PATH):
            raise FileNotFoundError("Model pipeline not found. Please train the model first.")
        _pipeline = joblib.load(PIPELINE_PATH)
        
        with open(METADATA_PATH, "r") as f:
            _metadata = json.load(f)
            
        with open(EVAL_PATH, "r") as f:
            _eval_metrics = json.load(f)

def predict_financial_stress(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predicts the probability of financial stress (simulator-defined reserve breach)
    given a dictionary of features.
    
    Args:
        features: Dictionary containing all required inputs defined in the feature schema.
        
    Returns:
        Dictionary containing prediction results, probabilities, and model metadata.
    """
    _load_artifacts()
    
    # 1. Validate required features
    missing_cols = [col for col in ALL_FEATURES if col not in features]
    if missing_cols:
        raise ValueError(f"Missing required features for prediction: {missing_cols}")
        
    # Convert single dictionary to DataFrame for processing
    # Filter to only keep allowed features, in correct order
    df = pd.DataFrame([features])[ALL_FEATURES]
    
    # Check numeric types
    for col in ALL_FEATURES:
        if col != "universe_id":
            # Attempt to convert to float to ensure numeric validity
            try:
                df[col] = df[col].astype(float)
            except ValueError:
                raise ValueError(f"Feature '{col}' must be numeric.")
                
    # 2. Apply preprocessing and predict
    # The pipeline inherently applies the preprocessing before passing to XGBoost
    probability = float(_pipeline.predict_proba(df)[0, 1])
    
    # 3. Apply threshold
    threshold = _eval_metrics.get("classification_threshold", 0.5)
    predicted_class = 1 if probability >= threshold else 0
    
    # 4. Return result
    return {
        "risk_target": "financial_stress_label",
        "estimated_probability": probability,
        "predicted_class": predicted_class,
        "classification_threshold": threshold,
        "model_version": _metadata.get("model_version", "v1.0")
    }
