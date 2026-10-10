import os
import psycopg
from app.core.config import settings

def main():
    conn_str = settings.DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    print(f"Connecting to: {conn_str}")
    
    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin, rolbypassrls FROM pg_roles;")
            roles = cur.fetchall()
            print("\nROLES:")
            for r in roles:
                if 'futurefund' in r[0]:
                    print(r)
            
            cur.execute("""
                SELECT tablename, tableowner 
                FROM pg_tables 
                WHERE schemaname = 'public' OR schemaname = 'futurefund_schema';
            """)
            tables = cur.fetchall()
            print("\nTABLES AND OWNERS:")
            for t in tables:
                print(t)
                
            cur.execute("""
                SELECT * FROM pg_policies;
            """)
            policies = cur.fetchall()
            print("\nPOLICIES:")
            for p in policies:
                print(p)

if __name__ == "__main__":
    main()
