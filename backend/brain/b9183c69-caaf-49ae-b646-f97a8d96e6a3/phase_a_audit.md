# Phase A: Database Security and Architecture Audit

## 1. Tables Holding User-Owned Data
- **Directly Owned (via `user_id`)**: `users`, `financial_profiles`, `decisions`, `analysis_runs`.
- **Indirectly Owned (Cascading from `analysis_id`)**: `analysis_universe_results`, `stress_test_runs`, `auto_pivot_runs`.
- **Deeply Nested (Cascading from `auto_pivot_run_id`)**: `auto_pivot_recommendations`.

## 2. Ownership Enforcement in Existing Application
- Python application routes (`get_profiles`, `get_analysis`, etc.) appropriately filter records by `user_id = current_user.id` in `app/services/persistence.py`.
- However, nested records (like universes and stress tests) are retrieved via SQLAlchemy ORM relationships. This is safe *if* the parent analysis is verified, but provides no defense against direct SQL querying or buggy cross-owner assignment.
- Row-Level Security (RLS) is currently **not active**. 

## 3. Roles and Ownership (PostgreSQL)
- **Role**: `futurefund_user` is the creator and owner of `futurefund_schema` and all its tables.
- **Vulnerability**: Table owners automatically **bypass RLS** unless `FORCE ROW LEVEL SECURITY` is applied to the tables. Since the FastAPI runtime connects as `futurefund_user`, simply enabling RLS (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`) will have **no effect**.
- **Resolution**: We must split the roles. `futurefund_user` should remain the migration/schema owner. We will create a new least-privilege role (`futurefund_api`) strictly for the FastAPI application runtime, which will be subject to RLS.

## 4. Session State & Connection Pooling Leaks
- FastAPI utilizes a SQLAlchemy `SessionLocal` connected to a pool (`pool_pre_ping=True`).
- **Vulnerability**: If we configure RLS to rely on a session variable (e.g., `current_setting('app.current_user_id')`), a pooled connection returning to the pool will retain that state. A subsequent request using the same connection could inherit another user's identity!
- **Resolution**: We must use SQLAlchemy `PoolEvents.checkout` to explicitly wipe the session variable (`SET app.current_user_id = '';`) every time a connection is leased to a request.

## 5. The Login Catch-22
- RLS blocks `SELECT` on the `users` table unless `app.current_user_id` is set. 
- However, during login (and JWT verification), the system needs to `SELECT` the user *before* it knows their ID!
- **Resolution**: We will introduce a narrow context flag `app.is_login = '1'`. The `users` table RLS policy will allow SELECT if `app.is_login` is active or if the `id` matches `current_user_id`. The FastAPI auth dependency will set `is_login`, fetch the user, and immediately wipe `is_login` and set `current_user_id`.

## Action Plan (Phases B–F)
1. **Schema & Roles**: Create `futurefund_api` role. Grant minimal DML privileges. Update `.env` to use this new role.
2. **Alembic Migration**: Generate a migration that enables RLS on all tables, applies policies enforcing `user_id` (and JOINs for nested tables), and uses `FORCE ROW LEVEL SECURITY`.
3. **App Updates**: Modify `app/database/session.py` with SQLAlchemy event hooks to prevent connection pool leaks. Update `app/api/auth.py` to securely inject the transaction-local Postgres context.
4. **Adversarial Testing**: Create automated tests pitting Alice vs. Bob to ensure the database forcibly rejects cross-tenant reads and writes.
