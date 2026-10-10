import os
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import GroupShuffleSplit
from xgboost import XGBClassifier
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
import joblib

from app.ml.preprocessing import create_preprocessing_pipeline, validate_and_filter_features, ALL_FEATURES, NUMERIC_FEATURES
from app.ml.evaluate import evaluate_model, plot_confusion_matrix, generate_classification_report, evaluate_baseline

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "v3", "futurefund_training_v3.csv")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "models", "v1")

def load_and_split_data(filepath: str, seed: int = 42):
    """
    Loads data and performs a group-aware split by profile_id.
    Ensures Universes A, B, and C for a single profile stay in the same split.
    Splits into 70% Train, 15% Validation, 15% Test.
    """
    df = pd.read_csv(filepath)
    
    # Validation
    assert "profile_id" in df.columns, "profile_id missing"
    assert "financial_stress_label" in df.columns, "target missing"
    
    X = df.drop(columns=["financial_stress_label"])
    y = df["financial_stress_label"]
    groups = df["profile_id"]
    
    gss = GroupShuffleSplit(n_splits=1, train_size=0.7, random_state=seed)
    train_idx, temp_idx = next(gss.split(X, y, groups))
    
    X_train, y_train, groups_train = X.iloc[train_idx], y.iloc[train_idx], groups.iloc[train_idx]
    X_temp, y_temp, groups_temp = X.iloc[temp_idx], y.iloc[temp_idx], groups.iloc[temp_idx]
    
    # Second split: 50% Val, 50% Test from the Temp (which results in 15% overall each)
    gss_temp = GroupShuffleSplit(n_splits=1, train_size=0.5, random_state=seed)
    val_idx, test_idx = next(gss_temp.split(X_temp, y_temp, groups_temp))
    
    X_val, y_val, groups_val = X_temp.iloc[val_idx], y_temp.iloc[val_idx], groups_temp.iloc[val_idx]
    X_test, y_test, groups_test = X_temp.iloc[test_idx], y_temp.iloc[test_idx], groups_temp.iloc[test_idx]
    
    # Assert zero overlap
    assert len(set(groups_train).intersection(set(groups_val))) == 0
    assert len(set(groups_train).intersection(set(groups_test))) == 0
    assert len(set(groups_val).intersection(set(groups_test))) == 0
    
    # Filter features before training
    X_train_filtered = validate_and_filter_features(X_train)
    X_val_filtered = validate_and_filter_features(X_val)
    X_test_filtered = validate_and_filter_features(X_test)
    
    splits = {
        "train": (X_train_filtered, y_train, groups_train),
        "val": (X_val_filtered, y_val, groups_val),
        "test": (X_test_filtered, y_test, groups_test)
    }
    
    return splits, df

def train_model(X_train, y_train, X_val, y_val, seed: int = 42):
    """
    Trains the XGBoost pipeline.
    """
    # Calculate scale_pos_weight to handle class imbalance
    num_neg = np.sum(y_train == 0)
    num_pos = np.sum(y_train == 1)
    scale_pos_weight = num_neg / num_pos if num_pos > 0 else 1.0
    
    preprocessor = create_preprocessing_pipeline()
    
    xgb = XGBClassifier(
        random_state=seed,
        scale_pos_weight=scale_pos_weight,
        eval_metric='logloss',
        max_depth=6,
        n_estimators=100,
        learning_rate=0.1
    )
    
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', xgb)
    ])
    
    # Fit the pipeline
    # We could use early stopping, but with pipelines it's a bit verbose. 
    # 100 estimators is generally safe.
    pipeline.fit(X_train, y_train)
    
    return pipeline, scale_pos_weight

def train_baseline_lr(X_train, y_train, seed: int = 42):
    preprocessor = create_preprocessing_pipeline()
    lr = LogisticRegression(class_weight='balanced', random_state=seed, max_iter=1000)
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', lr)
    ])
    pipeline.fit(X_train, y_train)
    return pipeline

def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    seed = 42
    
    print("Loading and splitting data...")
    splits, original_df = load_and_split_data(DATA_PATH, seed=seed)
    
    X_train, y_train, groups_train = splits["train"]
    X_val, y_val, groups_val = splits["val"]
    X_test, y_test, groups_test = splits["test"]
    
    print("Training XGBoost model...")
    pipeline, scale_pos_weight = train_model(X_train, y_train, X_val, y_val, seed=seed)
    
    print("Training Logistic Regression baseline...")
    lr_pipeline = train_baseline_lr(X_train, y_train, seed=seed)
    
    print("Evaluating models...")
    # Validation evaluation
    y_val_prob_xgb = pipeline.predict_proba(X_val)[:, 1]
    xgb_val_metrics = evaluate_model(y_val, y_val_prob_xgb)
    
    y_val_prob_lr = lr_pipeline.predict_proba(X_val)[:, 1]
    lr_val_metrics = evaluate_model(y_val, y_val_prob_lr)
    
    val_baseline_metrics = evaluate_baseline(y_val)
    
    # Test evaluation
    y_test_prob_xgb = pipeline.predict_proba(X_test)[:, 1]
    xgb_test_metrics = evaluate_model(y_test, y_test_prob_xgb)
    
    # Choose threshold based on validation (we'll stick to 0.5 for now, but could be adjusted)
    chosen_threshold = 0.5
    
    # Save artifacts
    print("Saving artifacts...")
    pipeline_path = os.path.join(MODELS_DIR, "xgboost_pipeline.joblib")
    joblib.dump(pipeline, pipeline_path)
    
    feature_schema_path = os.path.join(MODELS_DIR, "feature_schema.json")
    with open(feature_schema_path, "w") as f:
        json.dump({"features": ALL_FEATURES}, f, indent=4)
        
    training_metadata = {
        "model_version": "v1.0",
        "dataset_source": "data/v3/futurefund_training_v3.csv",
        "target_definition": "financial_stress_label = 1 if closing cash balance < committed monthly outflow in any simulated month >= 1",
        "random_seed": seed,
        "hyperparameters": {
            "scale_pos_weight": scale_pos_weight,
            "max_depth": 6,
            "n_estimators": 100,
            "learning_rate": 0.1
        },
        "train_profiles": len(set(groups_train)),
        "val_profiles": len(set(groups_val)),
        "test_profiles": len(set(groups_test)),
        "train_rows": len(X_train),
        "val_rows": len(X_val),
        "test_rows": len(X_test),
        "train_class_1_ratio": float(np.mean(y_train)),
        "val_class_1_ratio": float(np.mean(y_val)),
        "test_class_1_ratio": float(np.mean(y_test)),
    }
    with open(os.path.join(MODELS_DIR, "training_metadata.json"), "w") as f:
        json.dump(training_metadata, f, indent=4)
        
    evaluation_metrics = {
        "xgboost_val": xgb_val_metrics,
        "xgboost_test": xgb_test_metrics,
        "logistic_regression_val": lr_val_metrics,
        "majority_baseline_val": val_baseline_metrics,
        "classification_threshold": chosen_threshold,
        "classification_report_test": generate_classification_report(y_test, y_test_prob_xgb, chosen_threshold)
    }
    with open(os.path.join(MODELS_DIR, "evaluation_metrics.json"), "w") as f:
        json.dump(evaluation_metrics, f, indent=4)
        
    # Confusion matrix
    plot_confusion_matrix(y_test, y_test_prob_xgb, chosen_threshold, os.path.join(MODELS_DIR, "confusion_matrix.png"))
    
    # Feature importance (approximate via XGBoost native if possible, or just note it)
    xgb_model = pipeline.named_steps['classifier']
    preprocessor = pipeline.named_steps['preprocessor']
    
    # Get feature names after one-hot encoding
    cat_encoder = preprocessor.named_transformers_['cat'].named_steps['onehot']
    cat_features = list(cat_encoder.get_feature_names_out(["universe_id"]))
    all_feature_names = NUMERIC_FEATURES + cat_features
    
    importances = xgb_model.feature_importances_
    fi_df = pd.DataFrame({
        "feature": all_feature_names,
        "importance": importances
    }).sort_values(by="importance", ascending=False)
    fi_df.to_csv(os.path.join(MODELS_DIR, "feature_importance.csv"), index=False)
    
    # Create README
    readme_content = f"""# XGBoost Model V1

## Overview
This is the trained XGBoost model for predicting `financial_stress_label`. The model was trained on the synthetic V3 dataset.

## Disclaimers
* **This model learns patterns generated by FutureFund's synthetic data and financial simulation assumptions. It is not a validated real-world predictor of Indian household financial stress.**
* Do not describe the predicted probability as a real-world probability of default or as a guarantee of future financial failure.
* The simulator remains the authoritative calculation engine.

## Metrics
* Test ROC-AUC: {xgb_test_metrics['roc_auc']:.4f}
* Test PR-AUC: {xgb_test_metrics['pr_auc']:.4f}
* Test F1-Score: {xgb_test_metrics['f1_score']:.4f}

## Features
The exact feature list is locked in `feature_schema.json`. Identifier columns (`record_id`, `profile_id`) and outcome columns (`ending_cash_balance_inr`, etc.) are explicitly excluded.
"""
    with open(os.path.join(MODELS_DIR, "README.md"), "w") as f:
        f.write(readme_content)
        
    print("Done! Artifacts saved to models/v1/")

if __name__ == "__main__":
    main()
