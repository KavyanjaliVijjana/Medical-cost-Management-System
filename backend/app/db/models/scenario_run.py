from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ScenarioRun(Base):
    """A persisted, deterministic department-reduction what-if calculation."""

    __tablename__ = "scenario_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True, nullable=False)
    forecast_run_id: Mapped[int] = mapped_column(ForeignKey("forecast_runs.id"), index=True, nullable=False)
    department: Mapped[str] = mapped_column(String(255), nullable=False)
    department_cost_share_pct: Mapped[float] = mapped_column(Float, nullable=False)
    reduction_pct: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_projected_cost: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_reduction_amount: Mapped[float] = mapped_column(Float, nullable=False)
    scenario_projected_cost: Mapped[float] = mapped_column(Float, nullable=False)
    impact_pct: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    dataset: Mapped["Dataset"] = relationship(back_populates="scenario_runs")
    forecast_run: Mapped["ForecastRun"] = relationship(back_populates="scenario_runs")
