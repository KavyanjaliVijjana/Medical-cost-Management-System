"""SQLAlchemy-aware execution boundary for the Medical Economics Advisor tools."""

from __future__ import annotations

import json
import re
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agent.advisor_tools import ToolEvidence
from app.services.alert_service import alert_service
from app.services.analytics_service import analytics_service
from app.services.driver_analysis_service import driver_analysis_service
from app.services.forecast_service import forecast_service
from app.services.recommendation_service import recommendation_service
from app.services.scenario_service import scenario_service


class ControlledAdvisorToolExecutor:
    """Only this adapter receives a session; agents see its database-free interface."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, tool: str, *, dataset_id: int, question: str) -> ToolEvidence:
        try:
            if tool == "analytics":
                return ToolEvidence(tool=tool, result=_dump(analytics_service.get_summary(self._db, dataset_id)))
            if tool == "forecast":
                return ToolEvidence(tool=tool, result=_dump(forecast_service.get_latest_forecast(self._db, dataset_id)))
            if tool == "cost_pressures":
                return ToolEvidence(
                    tool=tool,
                    result={
                        "drivers": [_dump(item) for item in driver_analysis_service.list(self._db, dataset_id)],
                        "alerts": [_dump(item) for item in alert_service.list(self._db, dataset_id)],
                    },
                )
            if tool == "recommendations":
                return ToolEvidence(
                    tool=tool,
                    result={"recommendations": [_recommendation_dump(item) for item in recommendation_service.list(self._db, dataset_id)]},
                )
            if tool == "scenario":
                department, reduction_pct = self._scenario_inputs(dataset_id, question)
                return ToolEvidence(
                    tool=tool,
                    result=_dump(scenario_service.create(self._db, dataset_id=dataset_id, department=department, reduction_pct=reduction_pct)),
                )
            return ToolEvidence(tool=tool, error="Unsupported advisor tool.")
        except HTTPException as error:
            return ToolEvidence(tool=tool, error=str(error.detail))

    def _scenario_inputs(self, dataset_id: int, question: str) -> tuple[str, float]:
        percentage = re.search(r"(\d+(?:\.\d+)?)\s*%", question)
        if percentage is None:
            raise HTTPException(status_code=422, detail="Include a reduction percentage for a scenario question.")
        reduction_pct = float(percentage.group(1))
        if not 0 < reduction_pct <= 100:
            raise HTTPException(status_code=422, detail="Scenario reduction percentage must be greater than 0 and no more than 100.")
        summary = analytics_service.get_summary(self._db, dataset_id)
        normalized_question = question.lower()
        department = next((item.department for item in summary.departments if item.department.lower() in normalized_question), None)
        if department is None:
            raise HTTPException(status_code=422, detail="Name a department available in the selected dataset for the scenario.")
        return department, reduction_pct


def _dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return {key: item for key, item in value.__dict__.items() if not key.startswith("_")}


def _recommendation_dump(value: Any) -> dict[str, Any]:
    result = _dump(value)
    evidence = result.get("supporting_evidence")
    if isinstance(evidence, str):
        result["supporting_evidence"] = json.loads(evidence)
    return result
