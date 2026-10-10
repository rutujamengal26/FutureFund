# FutureFund API Contract

## POST `/api/v1/analyze`

**Description:** Triggers a complete financial simulation and risk assessment based on the user's profile, decision, and assumptions.

### Request Body

```json
{
  "profile": {
    "monthly_income_inr": 100000.0,
    "other_income_inr": 10000.0,
    "monthly_rent_inr": 25000.0,
    "essential_expenses_excluding_rent_inr": 15000.0,
    "variable_expenses_inr": 10000.0,
    "current_savings_inr": 500000.0,
    "existing_monthly_emi_inr": 5000.0
  },
  "decision": {
    "type": "home_purchase",
    "amount_inr": 5000000.0,
    "annual_interest_rate": 8.5,
    "tenure_months": 240,
    "upfront_cash_outflow_inr": 1000000.0
  },
  "assumptions": {
    "annual_rent_inflation_pct": 5.0,
    "annual_essential_expense_inflation_pct": 6.0,
    "annual_variable_expense_inflation_pct": 4.0,
    "annual_income_growth_pct": 10.0,
    "simulation_horizon_months": 36
  }
}
```

### Response Body

```json
{
  "analysis_id": "uuid-1234",
  "risk_assessment": {
    "stress_score": 0.85,
    "status": "High Risk"
  },
  "universes": [
    {
      "summary": {
        "universe_id": "act_now",
        "display_name": "Act Now",
        "configured_loan_amount_inr": 5000000.0,
        "decision_start_month": 0,
        "scheduled_emi_inr": 43391.0,
        "total_interest_full_loan_inr": 5413840.0,
        "interest_paid_within_horizon_inr": 1051515.0,
        "monthly_surplus_start_inr": 15000.0,
        "monthly_surplus_end_inr": 12000.0,
        "ending_projected_cash_balance_inr": 450000.0,
        "minimum_projected_cash_balance_inr": 350000.0,
        "month_of_minimum_cash_balance": 5,
        "remaining_loan_balance_at_horizon_inr": 4850000.0,
        "total_projected_living_expenses_inr": 1800000.0,
        "total_projected_income_inr": 3960000.0,
        "assumptions": {
           "annual_rent_inflation_pct": 5.0,
           "annual_essential_expense_inflation_pct": 6.0,
           "annual_variable_expense_inflation_pct": 4.0,
           "annual_income_growth_pct": 10.0,
           "simulation_horizon_months": 36
        }
      },
      "projection": [
        {
          "month": 1,
          "projected_monthly_income_inr": 100800.0,
          "projected_rent_inr": 25100.0,
          "new_monthly_emi_inr": 43391.0,
          "closing_cash_balance_inr": 465000.0
        }
      ]
    },
    {
      "summary": {
        "universe_id": "wait_prepare",
        "display_name": "Wait & Prepare"
      },
      "projection": []
    }
  ],
  "stress_tests": {
    "income_loss_scenario": "Failed",
    "interest_rate_hike": "Passed"
  },
  "auto_pivot_alternatives": [],
  "second_opinion": {
    "summary": "AI generated insight based on the simulation results."
  },
  "assumptions": {
    "annual_rent_inflation_pct": 5.0,
    "annual_essential_expense_inflation_pct": 6.0,
    "annual_variable_expense_inflation_pct": 4.0,
    "annual_income_growth_pct": 10.0,
    "simulation_horizon_months": 36
  }
}
```

## Future Endpoints (Phase 8+)

### `POST /api/v1/gemini/parse-decision` (Legacy route, now routes to configured AI)
Accepts natural language text and an optional existing profile. Returns a `DecisionParseResult` extracting the profile details and a `ParsedDecision`. It will return a `CLARIFICATION_REQUIRED` status with targeted questions if essential parameters (like loan amount or tenure) are missing.

### `POST /api/v1/gemini/second-opinion` (Legacy route, now routes to configured AI)
Returns a `SecondOpinionResponse` with an LLM-generated narrative analyzing the user's financial profile. It strictly relies on passed `analysis_evidence` for grounding and enforces that all numbers are cited from the underlying deterministic engines.

## Authentication & Persistence Endpoints (Phase 9)

All persistence endpoints require a valid JWT `Authorization: Bearer <token>`.

### `POST /api/v1/auth/register` & `POST /api/v1/auth/login`
Authentication routes managing user registration and access token generation.

### `POST /api/v1/profiles` & `GET /api/v1/profiles`
Create or retrieve saved financial profiles.

### `GET /api/v1/analyses`
Returns a paginated list of analysis run summaries for the authenticated user.
```json
[
  {
    "id": "uuid-5678",
    "status": "READY",
    "simulation_horizon": 36,
    "created_at": "2026-10-10T12:00:00Z"
  }
]
```

### `GET /api/v1/analyses/{analysis_id}`
Returns a detailed historical snapshot, encapsulating the entire orchestrator request and the computed response containing simulation trajectories, auto-pivot results, and stress tests.
