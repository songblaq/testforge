"""API assertions -- HTTP response validation."""

from __future__ import annotations

from typing import Any

from testforge.assertions.base import AssertionPlugin, AssertionResult, BaseAssertion


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
        ``path`` keyword argument specifies the JSON path (dot-notation).
        """
        path: str = kwargs.get("path", "")
        if not path:
            return AssertionResult(
                passed=False,
                message="JSON path assertion requires a 'path' argument",
                expected=expected,
                actual=actual,
            )

        # Simple dot-notation traversal (e.g. "data.user.id")
        node: Any = actual
        try:
            for key in path.split("."):
                if isinstance(node, dict):
                    node = node[key]
                elif isinstance(node, list):
                    node = node[int(key)]
                else:
                    raise KeyError(key)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            return AssertionResult(
                passed=False,
                message=f"JSON path '{path}' not found: {exc}",
                expected=expected,
                actual=actual,
            )

        passed = node == expected
        return AssertionResult(
            passed=passed,
            message=f"JSON path '{path}': {node!r} {'==' if passed else '!='} {expected!r}",
            expected=expected,
            actual=node,
        )


class ApiAssertionPlugin(AssertionPlugin):
    """Plugin that handles status_code and json_path assertion types."""

    @staticmethod
    def handles() -> list[str]:
        return ["status_code", "json_path"]

    def evaluate(
        self,
        assertion_type: str,
        params: dict[str, Any],
        context: dict[str, Any],
    ) -> AssertionResult:
        actual = context.get("response", params.get("actual"))
        expected = params.get("expected")

        if assertion_type == "status_code":
            status_code = (
                actual.status_code
                if hasattr(actual, "status_code")
                else context.get("status_code", actual)
            )
            return StatusCodeAssertion().check(status_code, expected)

        if assertion_type == "json_path":
            body = (
                actual.json()
                if hasattr(actual, "json")
                else context.get("body", actual)
            )
            return JsonPathAssertion().check(body, expected, path=params.get("path", ""))

        return AssertionResult(
            passed=False,
            message=f"ApiAssertionPlugin: unknown type '{assertion_type}'",
        )
