import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.authentication import delete_current_session, get_current_user
from app.core.security import hash_password, hash_token, verify_password
from app.db.models.auth_session import AuthSession
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import AuthResponse, CredentialsRequest, DemoLoginRequest, ProfileUpdateRequest, RegisterRequest, UserResponse
from app.seed.demo_user import DEMO_USER_EMAIL, DEMO_USER_PASSWORD

router = APIRouter(prefix="/auth", tags=["authentication"])
_bearer_scheme = HTTPBearer(auto_error=False)


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_demo=user.is_demo,
        role="Medical Economics Analyst",
        account_type="Demo account" if user.is_demo else "Standard account",
        created_at=user.created_at,
    )


def _auth_response(db: Session, user: User) -> AuthResponse:
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(user_id=user.id, token_hash=hash_token(token)))
    db.commit()
    return AuthResponse(**_user_response(user).model_dump(), access_token=token)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    if db.scalar(select(User).where(User.email == payload.email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account already exists for this email address.")

    user = User(
        email=payload.email,
        display_name=payload.full_name,
        password_hash=hash_password(payload.password),
        is_demo=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _auth_response(db, user)


@router.post("/login", response_model=AuthResponse)
def login(payload: CredentialsRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    return _auth_response(db, user)


@router.post("/demo-login", response_model=UserResponse)
def demo_login(payload: DemoLoginRequest, db: Session = Depends(get_db)) -> UserResponse:
    """Compatibility endpoint retained for the existing foundation test suite."""
    if payload.email != DEMO_USER_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only the seeded demo account is available in this MVP.",
        )

    user = db.scalar(select(User).where(User.email == DEMO_USER_EMAIL))
    if user is None:
        raise HTTPException(status_code=503, detail="Demo account is not initialized.")
    if not verify_password(DEMO_USER_PASSWORD, user.password_hash):
        raise HTTPException(status_code=503, detail="Demo account credentials are not initialized.")
    return _user_response(user)


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_profile(user_id: int, payload: ProfileUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserResponse:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user = current_user
    user.display_name = payload.full_name
    db.commit()
    db.refresh(user)
    return _user_response(user)


@router.patch("/profile", response_model=UserResponse)
def update_current_profile(payload: ProfileUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserResponse:
    current_user.display_name = payload.full_name
    db.commit()
    db.refresh(current_user)
    return _user_response(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    if credentials is not None:
        delete_current_session(db, credentials.credentials)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
