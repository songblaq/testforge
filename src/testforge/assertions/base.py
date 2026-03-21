"""Base assertion interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AssertionResult:
    """Result of an assertion check."""

    passed: bool
    message: str
    expected: Any = None
    actual: Any = None


class BaseAssertion(ABC):
    """Abstract base class for assertions."""

    @abstractmethod
    def check(self, actual: Any, expected: Any, **kwargs: Any) -> AssertionResult:
        """Perform the assertion check.

        Returns
        -------
        AssertionResult:
            Whether the assertion passed and details.
        """


# ---------------------------------------------------------------------------
# Plugin registry
# ---------------------------------------------------------------------------

ASSERTION_REGISTRY: dict[str, type[AssertionPlugin]] = {}


class AssertionPlugin(ABC):
    """Abstract base for assertion plugins registered in ASSERTION_REGISTRY."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Auto-register concrete (non-abstract) subclasses
        if not getattr(cls, "__abstractmethods__", None):
            for key in cls.handles():
                ASSERTION_REGISTRY[key] = cls

    @staticmethod
    @abstractmethod
    def handles() -> list[str]:
        """Return the assertion type keys this plugin handles."""

    @abstractmethod
    def evaluate(
        self,
        assertion_type: str,
        params: dict[str, Any],
        context: dict[str, Any],
    ) -> AssertionResult:
        """Evaluate the assertion and return a result."""
