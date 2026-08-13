from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import DemoLoginRequest, UserResponse
from app.seed.demo_user import DEMO_USER_EMAIL

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/demo-login", response_model=UserResponse)
def demo_login(payload: DemoLoginRequest, db: Session = Depends(get_db)) -> User:
    """Return the seeded demo account; authentication is deliberately MVP-only."""
    if payload.email != DEMO_USER_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only the seeded demo account is available in this MVP.",
        )

    user = db.scalar(select(User).where(User.email == DEMO_USER_EMAIL))
    if user is None:
        raise HTTPException(status_code=503, detail="Demo account is not initialized.")
    return user
