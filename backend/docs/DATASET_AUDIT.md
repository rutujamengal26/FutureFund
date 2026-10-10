# FutureFund Dataset Audit Report

## 1. File Details
* **Location**: `data/v2/FinMultiverse_100k_refined_training_dataset.csv`
* **Format**: Comma-Separated Values (CSV)
* **File Size**: ~14.4 MB
* **Rows**: 100,000 (excluding header)
* **Columns**: 22

## 2. Column Names and Representative Statistics
The dataset includes standard profile metrics along with new shock-event features:
* `record_id` (e.g., `FM_SYN_000001`)
* `age_band` (e.g., `25-34`, `45-54`)
* `employment_type` (e.g., `salaried`, `self_employed`)
* `city_tier` (e.g., `tier_1`, `tier_3`)
* `monthly_income_inr` (Range: 12,000.0 to 380,500.0)
* `other_monthly_income_inr`
* `monthly_rent_inr`
* `monthly_essential_expenses_excl_rent_inr`
* `monthly_variable_expenses_inr`
* `current_savings_inr`
* `existing_monthly_emi_inr`
* `decision_type` (e.g., `personal_loan`, `vehicle_loan`)
* `proposed_loan_amount_inr`
* `annual_interest_rate_pct`
* `loan_tenure_months`
* `upfront_cash_outflow_inr`
* `income_shock_pct` (Shock variable)
* `shock_start_month` (Shock variable)
* `shock_duration_months` (Shock variable)
* `emergency_expense_inr` (Shock variable)
* `simulation_horizon_months`
* `financial_stress_label` (Target label)

## 3. Data Quality Findings
* **Missing Values**: 0 missing values across all columns.
* **Duplicate Rows/IDs**: 0 duplicate `record_id` values.
* **Invalid Numerical Values**: No negative incomes or invalid numeric errors were encountered during the sweep.

## 4. Target Label and Class Distribution
* **Target**: `financial_stress_label`
* **0 (Non-Stressed)**: 58,944 (58.94%)
* **1 (Stressed)**: 41,056 (41.06%)
* **Analysis**: The class distribution is very well-balanced naturally.

## 5. Provenance and Licence
* **Provenance**: The dataset is clearly synthetic (`FM_SYN_` prefix) and maps tightly to the "FinMultiverse" project naming.
* **Licence**: No explicit license, usage restriction, or source metadata is embedded directly inside the dataset file.

## 6. Relevance and Feature Mapping to FutureFund
The dataset shares a heavy overlap with FutureFund Phase 1 variables:
* `monthly_income_inr` -> `ProfileSchema.monthly_income_inr`
* `monthly_rent_inr` -> `ProfileSchema.monthly_rent_inr`
* `current_savings_inr` -> `ProfileSchema.current_savings_inr`
* `proposed_loan_amount_inr` -> `DecisionSchema.amount_inr`

**Unavailable/Ambiguous Fields:**
* It completely lacks Phase 2 compounding variables: `annual_rent_inflation_pct`, `annual_essential_expense_inflation_pct`, `annual_variable_expense_inflation_pct`, and `annual_income_growth_pct`.
* It completely lacks `universe_id` logic (Act Now, Wait & Prepare, Reimagine).

## 7. Target Leakage Risks
The dataset appears clean from internal target leakage. The columns present are explicitly "starting state" (e.g., `current_savings_inr`) and "assumptions" (e.g., `income_shock_pct`). There are no future outcome aggregations like "ending_cash_balance" or "breach_month" that would leak the `financial_stress_label`.

## 8. Target Suitability and Integration Strategy
**Assessment: Unsuitable out-of-the-box.**
While the data has a `financial_stress_label`, its simulation mechanics are drastically different from our Phase 2 engine. It is modeling stress via *shocks* (`income_shock_pct`, `emergency_expense_inr`) rather than *compounding inflation factors* and *Universe offsets*. Training an XGBoost model on this label would cause the model to learn physics that our Phase 2 simulator does not even possess yet.

**Recommended Integration Strategy:**
We should import the raw starting profiles (income, rent, savings, demographics) from this 100k dataset to form a robust base, but we **MUST** pass those base profiles through our own Phase 2 simulator (by injecting missing universe rules and inflation parameters) to independently recalculate and generate a fresh `financial_stress_label`.

## 9. Hardware Requirements
* **Memory**: The 100k x 22 CSV consumes only ~14.4 MB on disk and easily fits into standard Pandas/XGBoost DataFrames (< 150 MB RAM). 
* **Processing**: Model training over 100k rows with ~20 features will take only a few seconds on a standard modern CPU.
