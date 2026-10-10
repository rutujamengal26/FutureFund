# FutureFund System Architecture

## Overview
FutureFund is an AI-powered financial decision simulator. The backend is built using Python and FastAPI, designed to be modular and scalable.

## Core Modules
- **app/api**: Contains all API route definitions and controllers.
- **app/schemas**: Pydantic models for request validation and response serialization.
- **app/ai**: Integration with local Ollama (or Gemini) for natural-language decision understanding and second opinions.
- **app/ml**: XGBoost-based financial-stress estimation models.
- **app/financial**: Core financial calculation logic (e.g., fixed-rate loan calculations, inflation adjustments).
- **app/simulation**: Logic for generating the three financial universes (Act Now, Wait & Prepare, Reimagine the Plan) and stress testing.
- **app/services**: Business logic orchestrating interactions between the API layer and the underlying core modules.
- **app/database**: Database connection and ORM models for PostgreSQL persistence.

## Principles
1. **Authoritative Financials**: Financial formulas and simulation results are authoritative and calculated strictly in Python.
2. **AI Guardrails**: The configured AI (Ollama/Gemini) is used for explanation and understanding, not for generating financial calculations.
3. **Data Integrity**: Monetary values are explicitly named (e.g., `_inr`) and rent is never double-counted with other essential expenses.
4. **Security**: Secrets and API keys are managed via environment variables and never exposed to the frontend.

## Stress-Testing Engine (Phase 5)
The FutureFund simulator supports deterministic, configurable stress-testing across all three financial universes. 
- **Types of Shocks**: Temporary income reductions, total income interruptions, one-time emergency expenses, and permanent inflation increases for rent, essential, and variable expenses.
- **Methodology**: The engine reuses the core Phase 1 calculations and Phase 2 monthly simulation loop by injecting optional event objects.
- **Baseline vs. Stressed Comparison**: Returns explicit comparisons tracking the change in ending cash balances, minimum cash balances, and shifts in reserve-breach occurrences.
- **ML Separation**: The XGBoost financial-stress model (Phase 4) is built strictly on baseline rules and is *not* used to assign probabilities to deterministic stress-test outcomes.

## Auto-Pivot Engine (Phase 6)
The Auto-Pivot Engine allows users to algorithmically explore alternative financial decisions that better satisfy their explicit constraints.
- **Candidate Generation**: Deterministically generates and evaluates configurable permutations of loan amount, decision delays, and loan tenure, without generating invalid loan setups.
- **Constraint Checking**: Supports strict checks on ending cash balance, maximum EMI, maximum DTI, total interest, and surplus requirements. Evaluated under the baseline or a selected stress scenario.
- **Ranking**: Calculates a score based on configurable objectives (`balanced`, `preserve_cash`, `minimize_total_interest`, `reduce_monthly_burden`). Ranks eligible candidates higher.
- **ML & Trade-offs**: Emits transparent, human-readable trade-offs for each candidate. The engine remains purely deterministic and does not rely on XGBoost or LLMs for candidate formulation.

## AI Integration (Phase 7 & 10)
The system leverages local Ollama, Google's official Python Gen AI SDK (`google-genai`), or the Groq Python SDK (`groq`) to provide natural-language decision understanding and evidence-based Second Opinions.
- **Provider Routing**: Selected dynamically via `AI_PROVIDER` (e.g., `gemini`, `ollama`, or `groq`) ensuring identical Pydantic output contracts.
- **Decision Parser**: Extracts structured financial intents and parameters from unstructured user text using strict JSON schemas. It safely forces clarifications for ambiguous inputs rather than hallucinating defaults.
- **Second Opinion**: Reads verified calculation evidence (simulations, stress tests, Auto-Pivot alternatives) to generate a grounded, conversational summary of the user's financial posture. It strictly abides by instructions to *explain* deterministic results rather than *calculate* new ones.
- **Error Handling**: Uses bounded retries for transient networking/API errors. Pydantic is used to strictly enforce API contracts for all ML and LLM responses.

## PostgreSQL Integration & Persistence (Phase 9)
The system stores user-specific data, profiles, and analytical records securely via PostgreSQL.
- **ORM & Migrations**: Implements SQLAlchemy 2.x and Alembic for robust schema tracking and type-safe database queries.
- **JSONB Snapshots**: Employs flexible `JSONB` structures for recording deterministic outcomes, universe trajectories, and configuration constraints, ensuring that historical analysis artifacts are completely isolated from future schema or code changes.
- **Atomic Operations**: Analysis runs and all associated downstream artifacts (simulation universes, stress scenarios, pivot candidates) are securely written atomically during the unified API orchestration loop. Failed records are rolled back, and invalid/incomplete workflows never dirty the data.
- **Authentication**: Secured end-to-end endpoints via JWT/OAuth2 schemes with Argon2id password hashing to enforce that every analysis record is strongly bound to a single user context. Unauthenticated analyses are optionally processed completely losslessly but treated as fully ephemeral without hitting the persistent data layer.
