from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

try:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
    
    # RLS Defense-in-Depth: Clear transaction-local variables when connection is checked out
    # to prevent a pooled connection from leaking a previous request's user context.
    @event.listens_for(engine, "checkout")
    def on_checkout(dbapi_connection, connection_record, connection_proxy):
        if not settings.DATABASE_URL.startswith("sqlite"):
            cursor = dbapi_connection.cursor()
            try:
                # Reset RLS session variables to safe defaults
                cursor.execute("SET app.current_user_id = '';")
                cursor.execute("SET app.is_login = '';")
            except Exception:
                pass
            finally:
                cursor.close()
                
except Exception as e:
    print("Failed to initialize database engine. Please check your configuration.")
    engine = None

if engine:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    SessionLocal = None

Base = declarative_base()

def get_db():
    if not SessionLocal:
        raise RuntimeError("Database not configured or connection failed.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
