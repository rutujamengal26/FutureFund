# FutureFund — AI-Powered Financial Decision Intelligence

FutureFund is a financial decision-support platform designed to help users understand the long-term consequences of major financial decisions before committing to them.

Instead of evaluating a decision using only its immediate cost, FutureFund simulates multiple possible financial futures, estimates financial stress, tests adverse scenarios, and explores alternative decisions to help users make more informed choices.

The platform combines deterministic financial calculations, multi-universe simulations, machine learning, and generative AI in a unified application.

> **Core principle:** Deterministic calculations establish financial outcomes. Machine learning estimates simulation-defined financial stress. Generative AI explains the results and helps users interact with the system.

---

## Table of Contents

* [Overview](#overview)
* [Key Features](#key-features)
* [Three Financial Universes](#three-financial-universes)
* [Technology Stack](#technology-stack)
* [System Architecture](#system-architecture)
* [Project Structure](#project-structure)
* [Financial Simulation Engine](#financial-simulation-engine)
* [Machine Learning Pipeline](#machine-learning-pipeline)
* [AI Integration](#ai-integration)
* [Stress Testing](#stress-testing)
* [Auto-Pivot Recommendations](#auto-pivot-recommendations)
* [PostgreSQL Persistence](#postgresql-persistence)
* [Installation and Setup](#installation-and-setup)
* [Running the Application](#running-the-application)
* [API Endpoints](#api-endpoints)
* [Testing](#testing)
* [Dataset and Model Limitations](#dataset-and-model-limitations)
* [Security](#security)
* [Roadmap](#roadmap)
* [Disclaimer](#disclaimer)

---

## Overview

Financial decisions such as purchasing a vehicle, taking a loan, or making a large purchase can affect savings, monthly cash flow, and financial resilience for years.

FutureFund helps users explore these consequences before making a commitment.

Users can provide their financial profile, describe a proposed decision, configure economic assumptions, and simulate different decision strategies.

The system evaluates:

* Monthly income and expenses.
* Existing and proposed loan obligations.
* Loan EMI and total interest.
* Rent and expense inflation.
* Income growth assumptions.
* Projected cash balances and reserve breaches.
* Adverse financial scenarios.
* Alternative loan amounts and repayment strategies.

The results are presented as decision-support information rather than guaranteed predictions of future financial conditions.

## Key Features

### 1. Financial Profiling

Collect and validate the user's financial position, including:

* Monthly income and other income.
* Rent and essential expenses.
* Variable expenses.
* Current savings.
* Existing monthly EMI obligations.

### 2. Loan Calculations

Calculate:

* Monthly Equated Monthly Instalment (EMI).
* Amortization schedules.
* Principal and interest components.
* Total repayment and total interest.

### 3. Multi-Universe Simulation

Compare three alternative strategies:

* **Act Now:** Proceed with the decision immediately.
* **Wait & Prepare:** Delay the decision to evaluate the financial effects of waiting.
* **Reimagine:** Evaluate a smaller proposed loan or financial commitment.

### 4. Inflation and Income Growth

Model how configurable assumptions affect future cash flow:

* Annual rent inflation.
* Annual essential-expense inflation.
* Annual variable-expense inflation.
* Annual income growth.

### 5. Machine Learning

Use an XGBoost classification pipeline to estimate whether a simulated financial scenario will breach the application's defined reserve threshold.

### 6. Financial Stress Testing

Evaluate how financial outcomes change under adverse events, such as income reductions, income interruptions, emergency expenses, and permanent expense increases.

### 7. Auto-Pivot

Generate and rank alternative financial decisions according to user constraints and objectives.

### 8. Gemini AI Assistance

Use natural-language decision parsing and evidence-grounded second opinions to make financial analysis easier to understand.

### 9. User Accounts and Analysis History

The backend includes authentication, financial profile management, and persistence workflows designed to save analyses and retrieve historical results using PostgreSQL.

---

## Three Financial Universes

FutureFund compares alternative decision strategies using the same underlying financial profile and economic assumptions.

| Universe   | Strategy       | Purpose                                 |
| ---------- | -------------- | --------------------------------------- |
| Universe A | Act Now        | Evaluate the immediate decision         |
| Universe B | Wait & Prepare | Evaluate a delayed decision             |
| Universe C | Reimagine      | Evaluate a reduced financial commitment |

The current simulation defaults include a six-month delay for Wait & Prepare and a loan amount of approximately 70% of the original amount for Reimagine.

These are configurable implementation assumptions, not universal financial recommendations.

---

## Technology Stack

| Layer                  | Technology                        |
| ---------------------- | --------------------------------- |
| Frontend               | React-based web application       |
| Backend API            | Python, FastAPI                   |
| Validation             | Pydantic                          |
| Financial calculations | Python, Decimal arithmetic        |
| Database               | PostgreSQL                        |
| ORM                    | SQLAlchemy                        |
| Database migrations    | Alembic                           |
| Machine learning       | XGBoost, scikit-learn             |
| Data processing        | Pandas                            |
| Model persistence      | Joblib                            |
| Generative AI          | Google Gemini API, `google-genai` |
| Authentication         | JWT-based authentication          |
| Password hashing       | Argon2                            |
| Testing                | Pytest                            |

The exact frontend framework, package versions, and installed dependencies should be verified against the current project configuration.

---

## System Architecture

```text
React Frontend
      |
      | HTTP / JSON
      v
FastAPI Backend
      |
      +-- Authentication and User Management
      |
      +-- Financial Calculation Engine
      |       |
      |       +-- EMI and Amortization
      |       +-- Financial Profile Analysis
      |
      +-- Multi-Universe Simulator
      |       |
      |       +-- Act Now
      |       +-- Wait & Prepare
      |       +-- Reimagine
      |
      +-- Stress Testing Engine
      |
      +-- Auto-Pivot Recommendation Engine
      |
      +-- XGBoost Inference Pipeline
      |
      +-- Gemini AI Services
      |
      v
SQLAlchemy / Alembic
      |
      v
PostgreSQL Database
```

The financial simulation engine is the source of deterministic financial outcomes. The ML pipeline provides a separate estimate of simulation-defined stress, while Gemini explains the supplied evidence.

---

## Project Structure

The following is a high-level representation of the reported repository structure. Verify individual filenames against the current checkout.

```text
HACKMATRIX/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints.py
│   │   ├── ai/
│   │   │   ├── client.py
│   │   │   ├── decision_parser.py
│   │   │   └── second_opinion.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── database/
│   │   │   ├── models.py
│   │   │   └── session.py
│   │   ├── financial/
│   │   │   ├── calculations.py
│   │   │   └── features.py
│   │   ├── ml/
│   │   │   ├── preprocessing.py
│   │   │   ├── train.py
│   │   │   ├── predict.py
│   │   │   └── evaluate.py
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── simulation/
│   │   │   ├── simulator.py
│   │   │   ├── inflation.py
│   │   │   ├── universes.py
│   │   │   ├── stress_test.py
│   │   │   └── auto_pivot.py
│   │   ├── tests/
│   │   └── main.py
│   ├── alembic/
│   ├── requirements.txt
│   └── .env.example
├── data/
│   ├── source/
│   ├── processed/
│   └── v3/
├── models/
│   └── v1/
├── docs/
│   ├── API_CONTRACT.md
│   ├── DATA_DICTIONARY.md
│   ├── DATASET_AUDIT.md
│   └── SYSTEM_ARCHITECTURE.md
└── README.md
```

---

## Financial Simulation Engine

### EMI calculation

For a fixed-rate loan with a positive monthly interest rate:

$$
EMI=P\frac{r(1+r)^n}{(1+r)^n-1}
$$

Where:

* \(P\) is the loan principal.
* \(r\) is the monthly interest rate.
* \(n\) is the repayment tenure in months.

For a zero-interest loan:

$$
EMI=\frac{P}{n}
$$

The calculation engine uses decimal-based rounding for currency calculations and generates amortization schedules.

### Inflation and income growth

The simulation uses annual assumptions to project monthly values over time.

For a baseline monthly value \(B\), annual growth rate \(g\), and month \(m\):

$$
V_m=B(1+g)^{m/12}
$$

Expense inflation and income growth are applied according to the configured assumptions.

### Cash-flow projection

The simulator tracks projected cash balances by incorporating income, expenses, loan repayments, upfront outflows, and applicable stress events.

The model permits negative cash balances to represent a projected shortfall rather than silently forcing balances to zero.

---

## Machine Learning Pipeline

FutureFund includes an XGBoost pipeline trained on generated simulation data.

### Dataset

The reported dataset-generation pipeline uses:

* 100,000 synthetic financial profiles.
* Three scenarios per profile.
* 300,000 generated scenario records.

The dataset generator runs the profiles through the FutureFund simulator and creates labels based on the defined reserve-breach rule.

### Training workflow

1. Load the generated training dataset.
2. Validate the expected feature schema.
3. Exclude identifiers and outcome-only columns.
4. Split data by profile to prevent scenarios from the same profile appearing in different partitions.
5. Preprocess numerical and categorical inputs.
6. Train and evaluate XGBoost and baseline models.
7. Save the fitted pipeline, feature schema, metadata, and evaluation metrics.

### Model evaluation

The reported initial evaluation included ROC-AUC, PR-AUC, precision, recall, F1-score, balanced accuracy, and a confusion matrix.

The reported test ROC-AUC was approximately 0.9916. This result reflects the synthetic, simulator-generated target and must not be interpreted as equivalent real-world predictive accuracy.

The model estimates whether the simulation-defined stress condition occurs. It does not establish the probability that a real person will default on a loan.

---

## AI Integration

FutureFund uses the official Google Gen AI SDK to provide two main capabilities.

### Natural-language decision parsing

Users can describe a financial decision in ordinary language.

For example:

> I want to buy a car with a ₹5 lakh loan at 10% annual interest over five years.

The parser extracts the relevant financial inputs and requests clarification when required information is missing or ambiguous.

### Evidence-grounded second opinion

Gemini receives a structured summary of simulation results and generates an explanation of the available strategies, risks, and trade-offs.

The AI layer is intended to explain the evidence rather than replace the deterministic calculation engine.

A valid Gemini API key is required for live Gemini API calls, but not for unit tests that mock the SDK.

---

## Stress Testing

The stress-testing engine compares baseline and adverse-scenario outcomes across the three financial universes.

Supported event types include:

* Temporary income reduction.
* Complete income interruption for a specified period.
* One-time emergency expenses.
* Permanent increases in rent or other expenses.

Example preset scenarios include:

* `mild_disruption`
* `income_shock`
* `emergency_expense`
* `combined_stress`

The output includes changes in projected cash balances and reserve-breach information.

Stress scenarios are hypothetical tests, not forecasts of events that will actually occur.

---

## Auto-Pivot Recommendations

Auto-Pivot explores alternative decisions to find options that better satisfy the user's constraints.

Candidate variations can include:

* Lower loan principal.
* Different repayment tenure.
* Delayed decision timing.

Candidates are evaluated against supported constraints and ranked using deterministic scoring objectives, such as minimizing monthly repayment burden or preserving cash reserves.

Candidates that fail strict constraints remain distinguishable from eligible candidates. The engine should not present an ineligible candidate as a recommendation that satisfies the user's requirements.

---

## PostgreSQL Persistence

FutureFund includes a SQLAlchemy-based persistence layer and Alembic migrations.

The reported schema includes:

| Table                        | Purpose                      |
| ---------------------------- | ---------------------------- |
| `users`                      | User accounts                |
| `financial_profiles`         | Saved financial profiles     |
| `decisions`                  | Financial decision inputs    |
| `analysis_runs`              | Analysis history             |
| `analysis_universe_results`  | Saved universe results       |
| `stress_test_runs`           | Stress-test history          |
| `auto_pivot_runs`            | Auto-Pivot execution history |
| `auto_pivot_recommendations` | Candidate recommendations    |

JSON/JSONB snapshot columns are used where appropriate to preserve historical inputs and results.

The intended data flow is:

**Frontend → FastAPI → SQLAlchemy → PostgreSQL**

The frontend must not connect directly to the database.

### Database configuration

Create `backend/.env` using the example configuration and set a valid PostgreSQL connection string:

```dotenv
DATABASE_URL=postgresql+psycopg://futurefund_user:YOUR_PASSWORD@localhost:5432/futurefund
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-2.5-flash
```

Use your actual credentials. Keep `.env` out of version control and never publish secrets in this README.

If the database uses a custom schema, ensure the SQLAlchemy models, database permissions, connection configuration, and Alembic migrations all agree on that schema.

---

## Installation and Setup

### Prerequisites

Install the following:

* Python version compatible with the backend dependencies.
* PostgreSQL.
* Git.
* Node.js and npm if running the React frontend.

### 1. Clone or open the repository

```powershell
git clone YOUR_REPOSITORY_URL
cd HACKMATRIX
```

If the project already exists locally, open its existing directory instead.

### 2. Create a Python virtual environment

```powershell
cd backend

python -m venv venv

.\venv\Scripts\Activate.ps1
```

### 3. Install backend dependencies

```powershell
python -m pip install --upgrade pip

pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` if the example file exists:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and configure `DATABASE_URL`, `GEMINI_API_KEY`, and other required settings.

Do not overwrite an existing `.env` file containing valid configuration.

### 5. Apply database migrations

After verifying the PostgreSQL connection and schema configuration:

```powershell
alembic upgrade head
```

Check the active migration:

```powershell
alembic current
```

Confirm that the expected application tables exist before relying on persistent user history.

---

## Running the Application

### Start the backend

From the `backend` directory with the virtual environment activated:

```powershell
uvicorn app.main:app --reload
```

The default local API address is:

`http://127.0.0.1:8000`

### Open API documentation

FastAPI Swagger UI:

`http://127.0.0.1:8000/docs`

ReDoc, if enabled:

`http://127.0.0.1:8000/redoc`

### Start the frontend

From the actual frontend directory, install dependencies and use the script defined in its `package.json`.

For a typical Vite application:

```powershell
npm install
npm run dev
```

Configure the frontend API base URL to point to the running FastAPI backend.

The frontend's port and environment-variable names depend on the existing frontend implementation.

---

## API Endpoints

The backend's documented API contract includes the following routes.

| Method   | Endpoint                        | Purpose                            |
| -------- | ------------------------------- | ---------------------------------- |
| `POST`   | `/api/v1/auth/register`         | Register a user                    |
| `POST`   | `/api/v1/auth/login`            | Authenticate a user                |
| `POST`   | `/api/v1/profiles`              | Create a financial profile         |
| `GET`    | `/api/v1/profiles`              | List saved profiles                |
| `DELETE` | `/api/v1/profiles/{id}`         | Delete a profile                   |
| `GET`    | `/api/v1/analyses`              | Retrieve analysis history          |
| `GET`    | `/api/v1/analyses/{id}`         | Retrieve an analysis               |
| `POST`   | `/api/v1/decisions/analyze`     | Run the decision analysis workflow |
| `POST`   | `/api/v1/gemini/parse-decision` | Parse a natural-language decision  |
| `POST`   | `/api/v1/gemini/second-opinion` | Generate an AI second opinion      |

The stress-testing and Auto-Pivot functionality are implemented in the reported simulation modules. Their public route availability should be verified in the running API documentation.

---

## Testing

Run the backend test suite from the `backend` directory:

```powershell
python -m pytest -v
```

The reported development milestones reached 79 passing tests after database integration.

**Important:** A passing test suite does not by itself prove that PostgreSQL persistence works. Some database tests use isolated SQLite databases.

For PostgreSQL integration verification:

1. Confirm the backend connects to the intended PostgreSQL database.
2. Run the Alembic migration.
3. Register a test account.
4. Save a financial profile.
5. Run an authenticated analysis.
6. Retrieve the saved history.
7. Verify the resulting records in PostgreSQL.

Only report PostgreSQL integration as verified after these checks succeed against the actual PostgreSQL instance.

---

## Dataset and Model Limitations

The current training dataset is synthetic and generated from the application's simulation rules.

Consequently:

* Model labels reflect the simulator's reserve-breach definition.
* The model can learn deterministic relationships built into the simulator.
* High evaluation metrics do not establish generalization to real-world financial outcomes.
* External income shocks and emergency expenses are not necessarily represented in every training-data version.
* Real-world validation using appropriate, licensed financial data remains future work.

Any future use of public survey data must respect its licensing, privacy, and permitted-use requirements.

---

## Security

FutureFund handles sensitive financial information. Before production deployment:

* Keep database credentials and Gemini API keys on the server.
* Use HTTPS.
* Hash passwords securely.
* Enforce authorization and ownership checks for every user-specific resource.
* Validate inputs with Pydantic.
* Restrict CORS to trusted frontend origins.
* Avoid logging passwords, tokens, API keys, or unnecessary financial details.
* Back up PostgreSQL and test restoration.
* Apply database migrations in a controlled deployment process.
* Add rate limiting and operational monitoring.
* Review account deletion, retention, and data export requirements.

Development configuration is not automatically production-ready.

---

## Roadmap

Potential future improvements include:

* Connect real financial survey data to improve input realism.
* Validate stress estimates against suitable real-world outcome data.
* Add richer historical analysis dashboards.
* Improve model calibration and decision-threshold selection.
* Add user-configurable inflation and economic scenarios.
* Expand Auto-Pivot constraints and comparison visualizations.
* Improve auditability and reproducibility of historical analyses.
* Add production deployment, monitoring, and database backup automation.

---

## Disclaimer

FutureFund is an educational financial decision-support tool. It provides mathematical projections, hypothetical stress scenarios, and model estimates based on supplied data and configured assumptions.

It does not guarantee future financial outcomes, predict actual loan default with established real-world accuracy, or replace professional financial advice.

Users should independently evaluate their financial circumstances before making significant financial commitments.

---

## Project Status

The reported implementation includes:

* Financial calculations and amortization.
* Multi-universe simulation.
* Synthetic dataset generation.
* XGBoost model training and inference.
* Stress testing.
* Auto-Pivot candidate search.
* Gemini AI integration.
* FastAPI orchestration.
* PostgreSQL persistence and database migrations.

The complete end-to-end workflow, frontend integration, and production readiness should be verified in the current development environment before being represented as fully operational.
