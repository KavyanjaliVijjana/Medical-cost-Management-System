from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import Alert, CostRecord, Dataset, DriverInsight, ForecastPoint, ForecastRun, Recommendation, ScenarioRun, User  # Ensures model metadata is registered.
from app.db.session import SessionLocal, engine
from app.seed.demo_user import seed_demo_user


def initialize_database() -> None:
    """Create foundational tables and idempotently seed the demo account."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        seed_demo_user(db)
    finally:
        db.close()
