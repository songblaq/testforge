"""API assertions -- HTTP response validation."""

from __future__ import annotations

from typing import Any

from testforge.assertions.base import AssertionResult, BaseAssertion


class StatusCodeAssertion(BaseAssertion):
    """Assert HTTP response status code."""

    def check(self, actual: Any, expected: Any, **kwargs: Any) -> AssertionResult:
        """Check that the status code matches."""
        passed = int(actual) == int(expected)
        return AssertionResult(
            passed=passed,
            message=f"Status code {'matches' if passed else 'mismatch'}: {actual} vs {expected}",
            expected=expected,
            actual=actual,
        )


class JsonPathAssertion(BaseAssertion):
    """Assert a value at a JSON path."""

    def check(self, actual: Any, expected: Any, **kwargs: Any) -> AssertionResult:
        """Check a JSON path value.

        *actual* should be the full JSON response body (dict).
        *expected* should be the expected value.
        ``path`` keyword argument specifies the JSON path.
        """
        path = kwargs.get("path", "")
        # Placeholder: would use jsonpath-ng or similar
        return AssertionResult(
            passed=False,
            message=f"JSON path assertion not yet implemented (path={path})",
            expected=expected,
            actual=actual,
        )
