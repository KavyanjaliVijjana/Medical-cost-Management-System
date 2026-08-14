import os

os.environ["DATABASE_URL"] = "sqlite:///./test_medical_cost.db"

import pytest
from types import SimpleNamespace

from sqlalchemy import select

from app.core.authentication import get_current_user
from app.db.base import Base
from app.db.init_db import initialize_database
from app.db.models.user import User
from app.db.session import engine
from app.db.session import SessionLocal
from app.main import app


@pytest.fixture(autouse=True)
def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    initialize_database()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def seeded_owner_for_legacy_data_api_tests(request):
    """Keep prior service/API tests focused on their deterministic concern; ownership is tested separately."""
    if request.node.fspath.basename in {"test_auth_api.py", "test_data_ownership.py"}:
        yield
        return
    with SessionLocal() as db:
        demo_user = db.scalar(select(User).where(User.email == "demo@medicalcost.local"))
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=demo_user.id)
    yield
    app.dependency_overrides.pop(get_current_user, None)
