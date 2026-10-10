import psycopg
import os
from dotenv import load_dotenv

def setup_roles():
    load_dotenv()
    db_url = os.environ.get("DATABASE_URL")
    if not db_url or "sqlite" in db_url:
        return

    # We connect as futurefund_user which owns the schema. But it cannot create roles.
    # Therefore, we must use postgres superuser to create the futurefund_api role.
    print("Please execute the following command in psql -U postgres:")
    print("CREATE ROLE futurefund_api WITH LOGIN ENCRYPTED PASSWORD 'api_password';")
    print("GRANT USAGE ON SCHEMA futurefund_schema TO futurefund_api;")
    print("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA futurefund_schema TO futurefund_api;")
    print("ALTER DEFAULT PRIVILEGES IN SCHEMA futurefund_schema GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO futurefund_api;")

if __name__ == "__main__":
    setup_roles()
