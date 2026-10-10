import os
import psycopg
from sqlalchemy import create_engine
from app.database.models import Base

def create_schema():
    # 1. Ensure futurefund_schema exists and futurefund_api has access
    print("Creating schema...")
    try:
        conn_str = "postgresql://postgres:postgres@localhost:5432/futurefund"
        with psycopg.connect(conn_str, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE SCHEMA IF NOT EXISTS futurefund_schema AUTHORIZATION postgres;")
                cur.execute("GRANT USAGE ON SCHEMA futurefund_schema TO futurefund_api;")
                cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA futurefund_schema TO futurefund_api;")
                cur.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA futurefund_schema GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO futurefund_api;")
                cur.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA futurefund_schema TO futurefund_api;")
                cur.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA futurefund_schema GRANT USAGE, SELECT ON SEQUENCES TO futurefund_api;")
    except Exception as e:
        print(f"Failed to create schema: {e}")
        return

    # 2. Create tables
    print("Creating tables...")
    db_url = "postgresql+psycopg://postgres:postgres@localhost:5432/futurefund?options=-c%20search_path=futurefund_schema,public"
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    create_schema()
