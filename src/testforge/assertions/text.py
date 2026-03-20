"""Text assertions -- string matching and pattern validation."""

from __future__ import annotations

import re
from typing import Any

from testforge.assertions.base import AssertionResult, BaseAssertion


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
