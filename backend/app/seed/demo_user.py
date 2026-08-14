from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models.user import User

DEMO_USER_EMAIL = "demo@medicalcost.local"
DEMO_USER_NAME = "Medical Economics Demo"
DEMO_USER_PASSWORD = "Demo@12345"


def seed_demo_user(db: Session) -> User:
    """Create the one hackathon demo user if it does not already exist."""
    user = db.scalar(select(User).where(User.email == DEMO_USER_EMAIL))
    if user is None:
        user = User(
            email=DEMO_USER_EMAIL,
            display_name=DEMO_USER_NAME,
            password_hash=hash_password(DEMO_USER_PASSWORD),
            is_demo=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif user.password_hash is None:
        user.password_hash = hash_password(DEMO_USER_PASSWORD)
        db.commit()
        db.refresh(user)
    return user
