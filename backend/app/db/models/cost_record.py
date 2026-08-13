from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CostRecord(Base):
    """Canonical medical-cost row; optional dimensions remain nullable."""

    __tablename__ = "cost_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True, nullable=False)
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    patient_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    service_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    medicine_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    lab_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    treatment_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    insurance_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    site_of_care: Mapped[str | None] = mapped_column(String(120), nullable=True)
    drug_category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unit_cost: Mapped[float | None] = mapped_column(Float, nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="cost_records")
