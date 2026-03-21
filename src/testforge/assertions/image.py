"""Image assertions -- visual comparison and element detection."""

from __future__ import annotations

from typing import Any

from testforge.assertions.base import AssertionResult, BaseAssertion


class ImageMatchAssertion(BaseAssertion):
    """Assert that two images match within a tolerance."""

    def __init__(self, tolerance: float = 0.95) -> None:
        self.tolerance = tolerance

    def check(self, actual: Any, expected: Any, **kwargs: Any) -> AssertionResult:
        """Compare two images.

        Parameters
        ----------
        actual:
            Path to the actual screenshot.
        expected:
            Path to the expected reference image.
        """
        raise NotImplementedError(
            "Image comparison requires Pillow. Install 'testforge[vision]' to enable."
        )
