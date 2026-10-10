import psycopg
from psycopg import sql

def setup():
    # Connect as postgres superuser
    try:
        conn_str = "postgresql://postgres:postgres@localhost:5432/postgres"
        with psycopg.connect(conn_str, autocommit=True) as conn:
            with conn.cursor() as cur:
                # Create futurefund_api role if not exists
                cur.execute("SELECT 1 FROM pg_roles WHERE rolname='futurefund_api'")
                if not cur.fetchone():
                    cur.execute("CREATE ROLE futurefund_api WITH LOGIN ENCRYPTED PASSWORD 'api_password'")
                    print("Created role futurefund_api")
                else:
                    print("Role futurefund_api already exists")

                # Create test database
                cur.execute("SELECT 1 FROM pg_database WHERE datname='futurefund_test'")
                if not cur.fetchone():
                    cur.execute("CREATE DATABASE futurefund_test OWNER futurefund_user")
                    print("Created database futurefund_test")
                else:
                    print("Database futurefund_test already exists")
    except Exception as e:
        print(f"Error connecting as postgres with password 'postgres': {e}")
        try:
            conn_str = "postgresql://postgres@localhost:5432/postgres"
            with psycopg.connect(conn_str, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM pg_roles WHERE rolname='futurefund_api'")
                    if not cur.fetchone():
                        cur.execute("CREATE ROLE futurefund_api WITH LOGIN ENCRYPTED PASSWORD 'api_password'")
                    cur.execute("SELECT 1 FROM pg_database WHERE datname='futurefund_test'")
                    if not cur.fetchone():
                        cur.execute("CREATE DATABASE futurefund_test OWNER futurefund_user")
                    print("Success with no password!")
        except Exception as e2:
            print(f"Error connecting as postgres with no password: {e2}")

if __name__ == "__main__":
    setup()
