"""Custom assertions -- user-defined assertion logic via callables."""

from __future__ import annotations

from typing import Any, Callable

from testforge.assertions.base import AssertionPlugin, AssertionResult, BaseAssertion


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


# Registry of named custom functions: name -> callable
_CUSTOM_FN_REGISTRY: dict[str, Callable[..., bool]] = {}


def register_custom_assertion(name: str, fn: Callable[..., bool]) -> None:
    """Register a callable under *name* for use via CustomAssertionPlugin."""
    _CUSTOM_FN_REGISTRY[name] = fn


class CustomAssertionPlugin(AssertionPlugin):
    """Plugin that handles the ``custom`` assertion type.

    Looks up the function name from ``params["fn"]`` in the custom function
    registry, then delegates to :class:`CustomAssertion`.
    """

    @staticmethod
    def handles() -> list[str]:
        return ["custom"]

    def evaluate(
        self,
        assertion_type: str,
        params: dict[str, Any],
        context: dict[str, Any],
    ) -> AssertionResult:
        fn_name: str = params.get("fn", "")
        fn = _CUSTOM_FN_REGISTRY.get(fn_name)
        if fn is None:
            return AssertionResult(
                passed=False,
                message=f"Custom assertion function '{fn_name}' not registered",
                expected=params.get("expected"),
                actual=context,
            )

        actual = context.get("output", params.get("actual"))
        expected = params.get("expected")
        return CustomAssertion(fn, description=fn_name).check(actual, expected)
