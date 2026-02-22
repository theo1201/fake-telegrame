from sqlmodel import create_engine, SQLModel, Session
import os

# Database path - Render and local development both support persistent storage
DATABASE_URL = "sqlite:///./data.db"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def _migrate_account_personal_details():
    """Add personal details columns to account table if they don't exist."""
    from sqlalchemy import text, inspect
    try:
        with engine.connect() as conn:
            # Check if account table exists first
            inspector = inspect(engine)
            if "account" not in inspector.get_table_names():
                print("Warning: account table does not exist, skipping migration")
                return
            
            result = conn.execute(text("PRAGMA table_info(account)"))
            columns = {row[1] for row in result}
            new_cols = [
                ("first_name", "TEXT DEFAULT ''"),
                ("last_name", "TEXT DEFAULT ''"),
                ("date_of_birth", "TEXT DEFAULT ''"),
                ("email", "TEXT DEFAULT ''"),
                ("phone_number", "TEXT DEFAULT ''"),
                ("address", "TEXT DEFAULT ''"),
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
