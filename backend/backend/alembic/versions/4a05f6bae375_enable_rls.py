"""enable_rls

Revision ID: 4a05f6bae375
Revises: 547c0e488cfe
Create Date: 2026-10-10 22:36:00.763084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a05f6bae375'
down_revision: Union[str, Sequence[str], None] = '547c0e488cfe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY users_isolation_policy ON users 
        FOR ALL USING (
            id = current_setting('app.current_user_id', true) OR current_setting('app.is_login', true) = '1'
        )
    """)

    # 2. direct ownership tables
    for table in ["financial_profiles", "decisions", "analysis_runs"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY {table}_policy ON {table} 
            FOR ALL 
            USING (user_id = current_setting('app.current_user_id', true))
            WITH CHECK (user_id = current_setting('app.current_user_id', true))
        """)

    # 3. level 1 nested (child of analysis_runs)
    for table in ["analysis_universe_results", "stress_test_runs", "auto_pivot_runs"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY {table}_policy ON {table} 
            FOR ALL 
            USING (
                EXISTS (SELECT 1 FROM analysis_runs WHERE id = analysis_id AND user_id = current_setting('app.current_user_id', true))
            )
            WITH CHECK (
                EXISTS (SELECT 1 FROM analysis_runs WHERE id = analysis_id AND user_id = current_setting('app.current_user_id', true))
            )
        """)

    # 4. level 2 nested (child of auto_pivot_runs)
    table = "auto_pivot_recommendations"
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"""
        CREATE POLICY {table}_policy ON {table} 
        FOR ALL 
        USING (
            EXISTS (
                SELECT 1 FROM auto_pivot_runs pr
                JOIN analysis_runs a ON a.id = pr.analysis_id
                WHERE pr.id = auto_pivot_run_id AND a.user_id = current_setting('app.current_user_id', true)
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM auto_pivot_runs pr
                JOIN analysis_runs a ON a.id = pr.analysis_id
                WHERE pr.id = auto_pivot_run_id AND a.user_id = current_setting('app.current_user_id', true)
            )
        )
    """)


def downgrade() -> None:
    tables = [
        "users", "financial_profiles", "decisions", "analysis_runs",
        "analysis_universe_results", "stress_test_runs", "auto_pivot_runs",
        "auto_pivot_recommendations"
    ]
    for table in tables:
        policy_name = f"{table}_isolation_policy" if table == "users" else f"{table}_policy"
        op.execute(f"DROP POLICY IF EXISTS {policy_name} ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
