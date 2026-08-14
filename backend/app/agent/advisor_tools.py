"""Database-free contracts between advisor agents and controlled tool execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ToolEvidence:
    tool: str
    result: dict[str, Any] | None = None
    error: str | None = None


class AdvisorToolExecutor(Protocol):
    """Controlled boundary implemented outside the agent package."""

    def execute(self, tool: str, *, dataset_id: int, question: str) -> ToolEvidence: ...
