"""Text assertions -- string matching and pattern validation."""

from __future__ import annotations

import re
from typing import Any

from testforge.assertions.base import AssertionPlugin, AssertionResult, BaseAssertion


class ContainsAssertion(BaseAssertion):
    """Assert that text contains a substring."""

    def check(self, actual: Any, expected: Any, **kwargs: Any) -> AssertionResult:
        """Check substring containment."""
        text = str(actual)
        substring = str(expected)
        passed = substring in text
        return AssertionResult(
            passed=passed,
            message=f"Text {'contains' if passed else 'does not contain'}: {substring!r}",
            expected=expected,
            actual=actual,
        )


class RegexAssertion(BaseAssertion):
    """Assert that text matches a regex pattern."""

    def check(self, actual: Any, expected: Any, **kwargs: Any) -> AssertionResult:
        """Check regex match."""
        text = str(actual)
        pattern = str(expected)
        match = re.search(pattern, text)
        passed = match is not None
        return AssertionResult(
            passed=passed,
            message=f"Regex {'matches' if passed else 'no match'}: {pattern!r}",
            expected=expected,
            actual=actual,
        )


class TextAssertionPlugin(AssertionPlugin):
    """Plugin that handles text_contains and text_matches assertion types."""

    @staticmethod
    def handles() -> list[str]:
        return ["text_contains", "text_matches"]

    def evaluate(
        self,
        assertion_type: str,
        params: dict[str, Any],
        context: dict[str, Any],
    ) -> AssertionResult:
        actual = context.get("output", params.get("actual", ""))
        expected = params.get("expected", "")

        if assertion_type == "text_contains":
            return ContainsAssertion().check(actual, expected)

        if assertion_type == "text_matches":
            return RegexAssertion().check(actual, expected)

        return AssertionResult(
            passed=False,
            message=f"TextAssertionPlugin: unknown type '{assertion_type}'",
        )
