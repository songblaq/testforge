"""Base connector interface for test execution targets."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectorResult:
    """Result of a connector execute() call.

    NOTE: Currently unused by production connectors (which use plain dicts).
    Kept for future migration to a typed result API.
    """

    success: bool
    response: Any
    duration_ms: int
    error: str | None = None
    artifacts: list[str] = field(default_factory=list)


class BaseConnector(ABC):
    """Abstract base class for execution connectors (legacy dict-based API)."""

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the target."""

    @abstractmethod
    def execute(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a command on the target.

        Returns
        -------
        dict:
            Execution result with ``status``, ``output``, and ``duration`` keys.
        """

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection."""

    def __enter__(self) -> BaseConnector:
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        self.disconnect()
