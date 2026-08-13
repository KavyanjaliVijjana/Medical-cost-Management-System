import os

os.environ["DATABASE_URL"] = "sqlite:///./test_medical_cost.db"

import pytest

from app.db.base import Base
from app.db.init_db import initialize_database
from app.db.session import engine


@pytest.fixture(autouse=True)
def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    initialize_database()
    yield
    Base.metadata.drop_all(bind=engine)
