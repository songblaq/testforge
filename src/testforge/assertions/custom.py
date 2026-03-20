"""Custom assertions -- user-defined assertion logic via callables."""

from __future__ import annotations

from typing import Any, Callable

from testforge.assertions.base import AssertionResult, BaseAssertion


class CustomAssertion(BaseAssertion):
    """Assertion backed by a user-provided callable.

    The callable should accept ``(actual, expected, **kwargs)`` and return a bool.
    """

    def __init__(self, fn: Callable[..., bool], description: str = "") -> None:
        self.fn = fn
        self.description = description or fn.__name__

    def check(self, actual: Any, expected: Any, **kwargs: Any) -> AssertionResult:
        """Run the custom check."""
        try:
            passed = self.fn(actual, expected, **kwargs)
        except Exception as exc:
            return AssertionResult(
                passed=False,
                message=f"Custom assertion {self.description!r} raised: {exc}",
                expected=expected,
                actual=actual,
            )

        return AssertionResult(
            passed=passed,
            message=f"Custom assertion {self.description!r}: {'passed' if passed else 'failed'}",
            expected=expected,
            actual=actual,
        )
