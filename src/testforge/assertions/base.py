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
