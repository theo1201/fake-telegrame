from sqlmodel import create_engine, SQLModel, Session
import os

# Database URL - automatically use PostgreSQL if DATABASE_URL env var is set (Render)
# Otherwise use SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")

# Render provides DATABASE_URL in format: postgresql://user:pass@host/dbname
# SQLAlchemy needs postgresql:// but some providers use postgres://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
else:
    # PostgreSQL configuration
    engine = create_engine(DATABASE_URL, echo=False)


def _migrate_account_personal_details():
    """Add personal details columns to account table if they don't exist."""
    from sqlalchemy import text, inspect
    try:
        with engine.connect() as conn:
            # Check if account table exists first
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            if "account" not in table_names:
                print("Warning: account table does not exist, skipping migration")
                return
            
            # Different SQL for SQLite vs PostgreSQL
            is_sqlite = DATABASE_URL.startswith("sqlite")
            
            if is_sqlite:
                # SQLite: use PRAGMA to get column info
                result = conn.execute(text("PRAGMA table_info(account)"))
                columns = {row[1] for row in result}
            else:
                # PostgreSQL: query information_schema
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'account'
                """))
                columns = {row[0] for row in result}
            
            # Define new columns with appropriate SQL syntax
            if is_sqlite:
                new_cols = [
                    ("first_name", "TEXT DEFAULT ''"),
                    ("last_name", "TEXT DEFAULT ''"),
                    ("date_of_birth", "TEXT DEFAULT ''"),
                    ("email", "TEXT DEFAULT ''"),
                    ("phone_number", "TEXT DEFAULT ''"),
                    ("address", "TEXT DEFAULT ''"),
                ]
            else:
                new_cols = [
                    ("first_name", "VARCHAR DEFAULT ''"),
                    ("last_name", "VARCHAR DEFAULT ''"),
                    ("date_of_birth", "VARCHAR DEFAULT ''"),
                    ("email", "VARCHAR DEFAULT ''"),
                    ("phone_number", "VARCHAR DEFAULT ''"),
                    ("address", "VARCHAR DEFAULT ''"),
                ]
            
            for col_name, col_def in new_cols:
                if col_name not in columns:
                    conn.execute(text(f"ALTER TABLE account ADD COLUMN {col_name} {col_def}"))
            conn.commit()
    except Exception as e:
        # Migration is optional, don't crash if it fails
        print(f"Warning: Migration failed (non-fatal): {e}")


def init_db():
    """Initialize database - create all tables if they don't exist."""
    try:
        # Create all tables first
        SQLModel.metadata.create_all(engine)
        # Then run migrations (add columns if needed)
        _migrate_account_personal_details()
        print("Database initialized successfully")
    except Exception as e:
        import traceback
        print(f"Error initializing database: {e}")
        traceback.print_exc()
        raise


def get_session():
    with Session(engine) as session:
        yield session
