"""Tests for the assertion registry and built-in assertion plugins."""

from __future__ import annotations

import pytest

# Import assertion modules to trigger plugin auto-registration
import testforge.assertions.api  # noqa: F401
import testforge.assertions.custom  # noqa: F401
import testforge.assertions.file  # noqa: F401
import testforge.assertions.text  # noqa: F401
from testforge.assertions.base import ASSERTION_REGISTRY, AssertionResult
from testforge.assertions.custom import register_custom_assertion
from testforge.assertions.image import ImageMatchAssertion


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestAssertionRegistry:
    def test_text_plugins_registered(self):
        assert "text_contains" in ASSERTION_REGISTRY
        assert "text_matches" in ASSERTION_REGISTRY

    def test_api_plugins_registered(self):
        assert "status_code" in ASSERTION_REGISTRY
        assert "json_path" in ASSERTION_REGISTRY

    def test_file_plugins_registered(self):
        assert "file_exists" in ASSERTION_REGISTRY
        assert "file_size" in ASSERTION_REGISTRY

    def test_custom_plugin_registered(self):
        assert "custom" in ASSERTION_REGISTRY


# ---------------------------------------------------------------------------
# TextAssertionPlugin
# ---------------------------------------------------------------------------


class TestTextAssertionPlugin:
    def _plugin(self):
        return ASSERTION_REGISTRY["text_contains"]()

    def test_text_contains_pass(self):
        plugin = self._plugin()
        result = plugin.evaluate(
            "text_contains",
            {"expected": "hello"},
            {"output": "hello world"},
        )
        assert result.passed
        assert "contains" in result.message

    def test_text_contains_fail(self):
        plugin = self._plugin()
        result = plugin.evaluate(
            "text_contains",
            {"expected": "missing"},
            {"output": "hello world"},
        )
        assert not result.passed

    def test_text_matches_pass(self):
        plugin = ASSERTION_REGISTRY["text_matches"]()
        result = plugin.evaluate(
            "text_matches",
            {"expected": r"\d{3}"},
            {"output": "code 404 error"},
        )
        assert result.passed

    def test_text_matches_fail(self):
        plugin = ASSERTION_REGISTRY["text_matches"]()
        result = plugin.evaluate(
            "text_matches",
            {"expected": r"^\d+$"},
            {"output": "not a number"},
        )
        assert not result.passed


# ---------------------------------------------------------------------------
# ApiAssertionPlugin
# ---------------------------------------------------------------------------


class TestApiAssertionPlugin:
    def test_status_code_pass(self):
        plugin = ASSERTION_REGISTRY["status_code"]()
        result = plugin.evaluate(
            "status_code",
            {"expected": 200},
            {"status_code": 200},
        )
        assert result.passed

    def test_status_code_fail(self):
        plugin = ASSERTION_REGISTRY["status_code"]()
        result = plugin.evaluate(
            "status_code",
            {"expected": 200},
            {"status_code": 404},
        )
        assert not result.passed

    def test_json_path_pass(self):
        plugin = ASSERTION_REGISTRY["json_path"]()
        result = plugin.evaluate(
            "json_path",
            {"path": "data.id", "expected": 42},
            {"body": {"data": {"id": 42}}},
        )
        assert result.passed

    def test_json_path_fail(self):
        plugin = ASSERTION_REGISTRY["json_path"]()
        result = plugin.evaluate(
            "json_path",
            {"path": "data.id", "expected": 99},
            {"body": {"data": {"id": 42}}},
        )
        assert not result.passed

    def test_json_path_missing(self):
        plugin = ASSERTION_REGISTRY["json_path"]()
        result = plugin.evaluate(
            "json_path",
            {"path": "missing.key", "expected": "x"},
            {"body": {}},
        )
        assert not result.passed
        assert "not found" in result.message


# ---------------------------------------------------------------------------
# FileAssertionPlugin
# ---------------------------------------------------------------------------


class TestFileAssertionPlugin:
    def test_file_exists_pass(self, tmp_path):
        f = tmp_path / "sample.txt"
        f.write_text("hello")
        plugin = ASSERTION_REGISTRY["file_exists"]()
        result = plugin.evaluate("file_exists", {}, {"path": str(f)})
        assert result.passed

    def test_file_exists_fail(self, tmp_path):
        plugin = ASSERTION_REGISTRY["file_exists"]()
        result = plugin.evaluate("file_exists", {}, {"path": str(tmp_path / "nope.txt")})
        assert not result.passed

    def test_file_size_pass(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(b"x" * 100)
        plugin = ASSERTION_REGISTRY["file_size"]()
        result = plugin.evaluate(
            "file_size",
            {"expected": (50, 200)},
            {"path": str(f)},
        )
        assert result.passed

    def test_file_size_fail(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(b"x" * 100)
        plugin = ASSERTION_REGISTRY["file_size"]()
        result = plugin.evaluate(
            "file_size",
            {"expected": (200, 500)},
            {"path": str(f)},
        )
        assert not result.passed


# ---------------------------------------------------------------------------
# CustomAssertionPlugin
# ---------------------------------------------------------------------------


class TestCustomAssertionPlugin:
    def test_custom_pass(self):
        register_custom_assertion("always_true", lambda actual, expected: True)
        plugin = ASSERTION_REGISTRY["custom"]()
        result = plugin.evaluate("custom", {"fn": "always_true"}, {})
        assert result.passed

    def test_custom_fail(self):
        register_custom_assertion("always_false", lambda actual, expected: False)
        plugin = ASSERTION_REGISTRY["custom"]()
        result = plugin.evaluate("custom", {"fn": "always_false"}, {})
        assert not result.passed

    def test_custom_unregistered(self):
        plugin = ASSERTION_REGISTRY["custom"]()
        result = plugin.evaluate("custom", {"fn": "nonexistent_fn_xyz"}, {})
        assert not result.passed
        assert "not registered" in result.message


# ---------------------------------------------------------------------------
# ImageMatchAssertion
# ---------------------------------------------------------------------------


class TestImageMatchAssertion:
    def test_raises_with_helpful_message(self):
        with pytest.raises(NotImplementedError, match="testforge\\[vision\\]"):
            ImageMatchAssertion().check("actual.png", "expected.png")


# ---------------------------------------------------------------------------
# Unknown assertion type (registry miss)
# ---------------------------------------------------------------------------


class TestUnknownAssertionType:
    def test_missing_type_returns_none(self):
        assert ASSERTION_REGISTRY.get("nonexistent_type_xyz") is None
