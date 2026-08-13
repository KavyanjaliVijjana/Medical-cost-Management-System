from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health_check(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> HealthResponse:
    """Confirm the API and configured database are reachable."""
    db.execute(text("SELECT 1"))
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        database="connected",
    )
