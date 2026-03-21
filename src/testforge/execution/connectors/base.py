"""Base connector interface for test execution targets."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectorResult:
    """Result of a connector execute() call."""

    success: bool
    response: Any
    duration_ms: int
    error: str | None = None
    artifacts: list[str] = field(default_factory=list)


class TargetConnector(ABC):
    """Abstract base for connectors that return :class:`ConnectorResult`."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection.  Returns True on success."""

    @abstractmethod
    def execute(self, action: dict[str, Any]) -> ConnectorResult:
        """Execute an action and return a structured result."""

    def cleanup(self) -> None:
        """Optional teardown hook."""

    def __enter__(self) -> TargetConnector:
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        self.cleanup()


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
