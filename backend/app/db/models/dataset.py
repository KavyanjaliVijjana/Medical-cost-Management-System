from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Dataset(Base):
    """Metadata for a user-uploaded or synthetic cost dataset."""

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(32), default="ready", nullable=False)

    cost_records: Mapped[list["CostRecord"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )
    forecast_runs: Mapped[list["ForecastRun"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )
    driver_insights: Mapped[list["DriverInsight"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
    scenario_runs: Mapped[list["ScenarioRun"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
