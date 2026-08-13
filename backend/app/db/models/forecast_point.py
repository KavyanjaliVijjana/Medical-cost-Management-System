from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ForecastPoint(Base):
    """A persisted monthly out-of-sample estimate belonging to a forecast run."""

    __tablename__ = "forecast_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    forecast_run_id: Mapped[int] = mapped_column(ForeignKey("forecast_runs.id"), index=True, nullable=False)
    forecast_month: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_cost: Mapped[float] = mapped_column(Float, nullable=False)

    forecast_run: Mapped["ForecastRun"] = relationship(back_populates="points")
