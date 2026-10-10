import os
import psycopg
from alembic import command
from alembic.config import Config

def init_db():
    # 0. Create schema
    conn_str = "postgresql://postgres:postgres@localhost:5432/futurefund_test"
    with psycopg.connect(conn_str, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS futurefund_schema AUTHORIZATION futurefund_user;")
            cur.execute("ALTER ROLE futurefund_user SET search_path TO futurefund_schema, public;")

    # 1. Run migrations as futurefund_user
    test_db_url = "postgresql+psycopg://futurefund_user:838098@localhost:5432/futurefund_test"
    os.environ["DATABASE_URL"] = test_db_url
    alembic_cfg = Config("alembic.ini")
    print("Applying migrations to test DB...")
    command.upgrade(alembic_cfg, "head")
    
    # 2. Grant privileges to futurefund_api as postgres superuser
    print("Granting privileges to futurefund_api...")
    conn_str = "postgresql://postgres:postgres@localhost:5432/futurefund_test"
    with psycopg.connect(conn_str, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("GRANT USAGE ON SCHEMA futurefund_schema TO futurefund_api;")
            cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA futurefund_schema TO futurefund_api;")
            cur.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA futurefund_schema GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO futurefund_api;")
            print("Privileges granted.")

if __name__ == "__main__":
    init_db()
