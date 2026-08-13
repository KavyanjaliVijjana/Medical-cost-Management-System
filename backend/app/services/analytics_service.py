from collections import defaultdict
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.cost_record import CostRecord
from app.db.models.dataset import Dataset
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.analytics import AnalyticsSummaryResponse, DepartmentAnalytics, MonthlyTrendPoint, OverallMetrics


@dataclass
class Aggregate:
    total_cost: float = 0.0
    patient_count: int = 0


class AnalyticsService:
    """Deterministic historical cost calculations for completed canonical datasets."""

    def __init__(self) -> None:
        self.repository = DatasetRepository()

    def get_summary(self, db: Session, dataset_id: int) -> AnalyticsSummaryResponse:
        dataset = self.repository.get_dataset(db, dataset_id)
        if dataset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

        records = self.repository.list_all_records(db, dataset_id)
        monthly = self._monthly_trend(records)
        departments = self._department_breakdown(records)
        metrics = self._overall_metrics(monthly, records)
        return AnalyticsSummaryResponse(
            dataset=dataset,
            metrics=metrics,
            monthly_trend=monthly,
            departments=departments,
            highest_cost_department=departments[0] if departments else None,
        )

    def _overall_metrics(self, monthly: list[MonthlyTrendPoint], records: list[CostRecord]) -> OverallMetrics:
        total_cost = sum(record.total_cost for record in records)
        total_patients = sum(record.patient_count for record in records)
        latest = monthly[-1] if monthly else None
        previous = monthly[-2] if len(monthly) > 1 else None
        return OverallMetrics(
            total_medical_cost=_round(total_cost),
            total_patient_count=total_patients,
            average_monthly_cost=_round(total_cost / len(monthly)) if monthly else None,
            average_monthly_patient_count=_round(total_patients / len(monthly)) if monthly else None,
            cost_per_patient=_safe_divide(total_cost, total_patients),
            latest_month=latest.month if latest else None,
            latest_month_cost=latest.total_cost if latest else None,
            previous_month=previous.month if previous else None,
            previous_month_cost=previous.total_cost if previous else None,
            month_over_month_cost_change_pct=latest.month_over_month_cost_change_pct if latest else None,
        )

    def _monthly_trend(self, records: list[CostRecord]) -> list[MonthlyTrendPoint]:
        aggregated: dict[str, Aggregate] = defaultdict(Aggregate)
        for record in records:
            month = record.record_date.strftime("%Y-%m")
            aggregate = aggregated[month]
            aggregate.total_cost += record.total_cost
            aggregate.patient_count += record.patient_count

        points: list[MonthlyTrendPoint] = []
        previous_cost: float | None = None
        for month in sorted(aggregated):
            aggregate = aggregated[month]
            points.append(
                MonthlyTrendPoint(
                    month=month,
                    total_cost=_round(aggregate.total_cost),
                    patient_count=aggregate.patient_count,
                    cost_per_patient=_safe_divide(aggregate.total_cost, aggregate.patient_count),
                    month_over_month_cost_change_pct=_percent_change(aggregate.total_cost, previous_cost),
                )
            )
            previous_cost = aggregate.total_cost
        return points

    def _department_breakdown(self, records: list[CostRecord]) -> list[DepartmentAnalytics]:
        aggregated: dict[str, Aggregate] = defaultdict(Aggregate)
        total_cost = sum(record.total_cost for record in records)
        for record in records:
            aggregate = aggregated[record.department]
            aggregate.total_cost += record.total_cost
            aggregate.patient_count += record.patient_count

        departments = [
            DepartmentAnalytics(
                department=department,
                total_cost=_round(aggregate.total_cost),
                patient_count=aggregate.patient_count,
                cost_per_patient=_safe_divide(aggregate.total_cost, aggregate.patient_count),
                contribution_pct=_percent_of_total(aggregate.total_cost, total_cost),
            )
            for department, aggregate in aggregated.items()
        ]
        return sorted(departments, key=lambda department: department.total_cost, reverse=True)


def _round(value: float) -> float:
    return round(value, 2)


def _safe_divide(numerator: float, denominator: int) -> float | None:
    return _round(numerator / denominator) if denominator else None


def _percent_change(current: float, previous: float | None) -> float | None:
    if previous is None or previous == 0:
        return None
    return _round(((current - previous) / previous) * 100)


def _percent_of_total(value: float, total: float) -> float | None:
    if total == 0:
        return None
    return _round((value / total) * 100)


analytics_service = AnalyticsService()
