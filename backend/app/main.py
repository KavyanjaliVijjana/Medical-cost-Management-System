from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analytics, auth, datasets, forecasts, health, insights, recommendations
from app.core.config import get_settings
from app.db.init_db import initialize_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Healthcare financial and operational analytics foundation.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(forecasts.router, prefix="/api/v1")
app.include_router(insights.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
