"""Thin, database-free specialist wrappers over controlled Advisor tools."""

from __future__ import annotations

from dataclasses import dataclass

from app.agent.advisor_tools import AdvisorToolExecutor, ToolEvidence


SUPERVISOR_NAME = "Medical Economics Supervisor Agent"
TREND_FORECAST_SPECIALIST = "Trend & Forecast Specialist"
COST_PRESSURE_ACTION_SPECIALIST = "Cost Pressure & Action Specialist"
SCENARIO_SPECIALIST = "Scenario Specialist"


@dataclass(frozen=True)
class SpecialistTask:
    specialist: str
    tools: tuple[str, ...]


@dataclass
class SpecialistResult:
    specialist: str
    evidence: list[ToolEvidence]


class TrendForecastSpecialist:
    name = TREND_FORECAST_SPECIALIST
    _supported_tools = {"analytics", "forecast"}

    def analyze(self, executor: AdvisorToolExecutor, *, dataset_id: int, question: str, tools: tuple[str, ...]) -> SpecialistResult:
        return SpecialistResult(self.name, [executor.execute(tool, dataset_id=dataset_id, question=question) for tool in tools if tool in self._supported_tools])


class CostPressureActionSpecialist:
    name = COST_PRESSURE_ACTION_SPECIALIST
    _supported_tools = {"cost_pressures", "recommendations"}

    def analyze(self, executor: AdvisorToolExecutor, *, dataset_id: int, question: str, tools: tuple[str, ...]) -> SpecialistResult:
        return SpecialistResult(self.name, [executor.execute(tool, dataset_id=dataset_id, question=question) for tool in tools if tool in self._supported_tools])


class ScenarioSpecialist:
    name = SCENARIO_SPECIALIST

    def analyze(self, executor: AdvisorToolExecutor, *, dataset_id: int, question: str, tools: tuple[str, ...]) -> SpecialistResult:
        return SpecialistResult(self.name, [executor.execute("scenario", dataset_id=dataset_id, question=question)])
