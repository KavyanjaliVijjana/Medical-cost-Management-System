from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import Alert, AuthSession, CostRecord, Dataset, DriverInsight, ForecastPoint, ForecastRun, Recommendation, ScenarioRun, User  # Ensures model metadata is registered.
from app.db.session import SessionLocal, engine
from app.seed.demo_user import seed_demo_user


def initialize_database() -> None:
    """Create foundational tables and idempotently seed the demo account."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if engine.dialect.name == "sqlite":
            columns = {row[1] for row in db.execute(text("PRAGMA table_info(users)"))}
            if "password_hash" not in columns:
                db.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
                db.commit()
            dataset_columns = {row[1] for row in db.execute(text("PRAGMA table_info(datasets)"))}
            if "user_id" not in dataset_columns:
                db.execute(text("ALTER TABLE datasets ADD COLUMN user_id INTEGER REFERENCES users(id)"))
                db.commit()
        demo_user = seed_demo_user(db)
        # Legacy local datasets predate account ownership. Keep them visible only to the seeded demo account.
        db.execute(text("UPDATE datasets SET user_id = :user_id WHERE user_id IS NULL"), {"user_id": demo_user.id})
        db.commit()
    finally:
        db.close()
