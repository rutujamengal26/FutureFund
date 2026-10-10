import psycopg

def fix_schema():
    print("Connecting as futurefund_user...")
    conn = psycopg.connect("postgresql://futurefund_user:your_password@localhost:5432/futurefund")
    conn.autocommit = True
    
    print("Creating schema...")
    conn.execute("CREATE SCHEMA IF NOT EXISTS futurefund_schema AUTHORIZATION futurefund_user;")
    
    print("Setting search path...")
    conn.execute("ALTER ROLE futurefund_user SET search_path TO futurefund_schema;")
    
    print("Done!")

if __name__ == "__main__":
    fix_schema()
