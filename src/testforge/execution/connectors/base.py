"""Base connector interface for test execution targets."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Abstract base class for execution connectors."""

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
