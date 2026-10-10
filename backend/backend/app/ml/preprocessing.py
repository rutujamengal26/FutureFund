import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

# Define explicit feature allowlist
NUMERIC_FEATURES = [
    "monthly_income_inr",
    "other_income_inr",
    "monthly_rent_inr",
    "essential_expenses_excluding_rent_inr",
    "variable_expenses_inr",
    "current_savings_inr",
    "existing_monthly_emi_inr",
    "original_proposed_loan_amount_inr",
    "configured_loan_amount_inr",
    "annual_interest_rate_pct",
    "tenure_months",
    "decision_delay_months",
    "upfront_cash_outflow_inr",
    "annual_rent_inflation_pct",
    "annual_essential_expense_inflation_pct",
    "annual_variable_expense_inflation_pct",
    "annual_income_growth_pct",
    "simulation_horizon_months",
]

CATEGORICAL_FEATURES = [
    "universe_id"
]

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

def create_preprocessing_pipeline() -> ColumnTransformer:
    """
    Creates a scikit-learn ColumnTransformer for preprocessing features.
    
    Numeric features:
    - Impute missing values with median (though our synthetic data is clean, good practice for real data).
    - Scale using StandardScaler.
    
    Categorical features:
    - Impute missing values with 'missing'.
    - OneHotEncode (handle_unknown='ignore' to gracefully handle unseen categories in inference).
    """
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, NUMERIC_FEATURES),
            ('cat', categorical_transformer, CATEGORICAL_FEATURES)
        ],
        remainder='drop'  # Explicitly drop any columns not in the allowlist
    )
    
    return preprocessor

def validate_and_filter_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates that all required features are present and returns a DataFrame 
    with only the allowed features in the correct order.
    """
    missing_cols = [col for col in ALL_FEATURES if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required features: {missing_cols}")
        
    return df[ALL_FEATURES].copy()
