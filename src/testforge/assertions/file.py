"""File assertions -- file existence, content, and size validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from testforge.assertions.base import AssertionResult, BaseAssertion


class FileExistsAssertion(BaseAssertion):
    """Assert that a file exists."""

    def check(self, actual: Any, expected: Any, **kwargs: Any) -> AssertionResult:
        """Check file existence.  *actual* is the file path."""
        path = Path(str(actual))
        passed = path.exists()
        return AssertionResult(
            passed=passed,
            message=f"File {'exists' if passed else 'not found'}: {path}",
            expected="exists",
            actual="exists" if passed else "missing",
        )


class FileSizeAssertion(BaseAssertion):
    """Assert that a file size is within a range."""

    def check(self, actual: Any, expected: Any, **kwargs: Any) -> AssertionResult:
        """Check file size.

        *actual* is the file path.  *expected* is ``(min_bytes, max_bytes)``.
        """
        path = Path(str(actual))
        if not path.exists():
            return AssertionResult(passed=False, message=f"File not found: {path}")

        size = path.stat().st_size
        min_size, max_size = expected
        passed = min_size <= size <= max_size
        return AssertionResult(
            passed=passed,
            message=f"File size {size} bytes {'in' if passed else 'out of'} range [{min_size}, {max_size}]",
            expected=expected,
            actual=size,
        )
