"""Base class for execution engines."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EngineResult:
    """Result from a single engine execution."""

    engine: str
    case_id: str
    status: str  # passed, failed, skipped, error
    duration_ms: int = 0
    output: str = ""
    error: str | None = None
    artifacts: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == "passed"


class BaseEngine(ABC):
    """Abstract base for all execution engines."""

    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this engine is installed and usable."""

    @abstractmethod
    def execute(self, script_path: Path, case_id: str, **kwargs: Any) -> EngineResult:
        """Execute a test script and return results."""

    def setup(self, project_dir: Path) -> None:
        """One-time setup before running tests."""

    def teardown(self) -> None:
        """Cleanup after running tests."""
