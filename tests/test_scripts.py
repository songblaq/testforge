"""Tests for Playwright script generation."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from testforge.core.project import (
    AnalysisResult,
    BusinessRule,
    Feature,
    create_project,
    save_analysis,
    save_cases,
)
from testforge.llm.adapter import LLMAdapter, LLMResponse
from testforge.scripts.playwright import (
    _generate_skeleton_scripts,
    _is_valid_python,
    _sanitize_id,
    _skeleton_script,
    generate_playwright_scripts,
)
from testforge.scripts.generator import generate_scripts
from testforge.scripts.validator import validate_script


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_CASES = [
    {
        "id": "TC-F001-01",
        "title": "Verify Login",
        "description": "Validate that login works with email and password",
        "feature_id": "F-001",
        "preconditions": ["System is accessible", "User is authenticated"],
        "steps": [
            {"order": 1, "action": "Navigate to login page", "expected_result": "Login form is displayed", "input_data": ""},
            {"order": 2, "action": "Enter email and password", "expected_result": "Fields are populated", "input_data": "user@test.com / pass123"},
            {"order": 3, "action": "Click login button", "expected_result": "User is logged in and redirected to dashboard", "input_data": ""},
        ],
        "expected_result": "Login functions correctly as specified",
        "priority": "high",
        "tags": ["functional", "auth"],
    },
    {
        "id": "TC-F002-01",
        "title": "Verify Signup",
        "description": "Validate new user registration",
        "feature_id": "F-002",
        "preconditions": ["System is accessible"],
        "steps": [
            {"order": 1, "action": "Navigate to signup page", "expected_result": "Signup form is displayed", "input_data": ""},
            {"order": 2, "action": "Fill in registration form", "expected_result": "Form is completed", "input_data": ""},
            {"order": 3, "action": "Submit form", "expected_result": "Account created successfully", "input_data": ""},
        ],
        "expected_result": "Signup functions correctly",
        "priority": "high",
        "tags": ["functional", "auth"],
    },
]


def _make_mock_adapter(code_text: str) -> LLMAdapter:
    """Return a mock LLMAdapter that returns *code_text* for any complete() call."""
    adapter = MagicMock(spec=LLMAdapter)
    adapter.complete.return_value = LLMResponse(text=code_text, model="mock")
    return adapter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def project_with_cases(tmp_path: Path) -> Path:
    """Create a TestForge project with pre-populated test cases."""
    project_dir = tmp_path / "script-test-project"
    create_project(project_dir)
    save_cases(project_dir, SAMPLE_CASES)
    return project_dir


@pytest.fixture
def project_empty(tmp_path: Path) -> Path:
    """Create a TestForge project with no cases."""
    project_dir = tmp_path / "empty-project"
    create_project(project_dir)
    return project_dir


# ---------------------------------------------------------------------------
# Tests: Skeleton generation (no LLM)
# ---------------------------------------------------------------------------


class TestGeneratePlaywrightSkeleton:
    """Skeleton script generation without LLM."""

    def test_skeleton_returns_scripts_for_each_case(self, project_with_cases: Path) -> None:
        """One script entry is generated per test case."""
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            scripts = generate_playwright_scripts(project_with_cases)

        assert len(scripts) == len(SAMPLE_CASES)

    def test_skeleton_script_has_required_keys(self, project_with_cases: Path) -> None:
        """Each script entry has case_id, title, path, and source."""
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            scripts = generate_playwright_scripts(project_with_cases)

        required_keys = {"case_id", "title", "path", "source"}
        for script in scripts:
            missing = required_keys - set(script.keys())
            assert not missing, f"Script missing keys: {missing}"

    def test_skeleton_source_is_valid_python(self, project_with_cases: Path) -> None:
        """Generated skeleton scripts are syntactically valid Python."""
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            scripts = generate_playwright_scripts(project_with_cases)

        for script in scripts:
            assert _is_valid_python(script["source"]), (
                f"Script for {script['case_id']} is not valid Python"
            )

    def test_skeleton_contains_playwright_imports(self, project_with_cases: Path) -> None:
        """Skeleton scripts import playwright.sync_api."""
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            scripts = generate_playwright_scripts(project_with_cases)

        for script in scripts:
            assert "from playwright.sync_api import" in script["source"]

    def test_skeleton_contains_test_function(self, project_with_cases: Path) -> None:
        """Skeleton scripts define a test function."""
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            scripts = generate_playwright_scripts(project_with_cases)

        for script in scripts:
            assert "def test_" in script["source"]

    def test_skeleton_contains_page_goto(self, project_with_cases: Path) -> None:
        """Skeleton scripts include page.goto() call."""
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            scripts = generate_playwright_scripts(project_with_cases)

        for script in scripts:
            assert "page.goto(" in script["source"]

    def test_skeleton_contains_screenshot(self, project_with_cases: Path) -> None:
        """Skeleton scripts include screenshot capture."""
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            scripts = generate_playwright_scripts(project_with_cases)

        for script in scripts:
            assert "page.screenshot(" in script["source"]

    def test_skeleton_contains_step_comments(self, project_with_cases: Path) -> None:
        """Skeleton scripts contain step comments from the test case."""
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            scripts = generate_playwright_scripts(project_with_cases)

        first = scripts[0]["source"]
        assert "Step 1" in first
        assert "Navigate to login page" in first

    def test_no_cases_returns_empty(self, project_empty: Path) -> None:
        """No test cases produces an empty script list."""
        scripts = generate_playwright_scripts(project_empty)
        assert scripts == []

    def test_skeleton_path_uses_sanitized_id(self) -> None:
        """Script filenames are sanitized from case IDs."""
        scripts = _generate_skeleton_scripts(SAMPLE_CASES[:1], "http://localhost:3000")
        assert scripts[0]["path"] == "test_tc_f001_01.py"

    def test_custom_base_url(self, tmp_path: Path) -> None:
        """base_url from config.extra is used in skeleton scripts."""
        import yaml

        project_dir = tmp_path / "custom-url-project"
        create_project(project_dir)
        save_cases(project_dir, SAMPLE_CASES[:1])

        # Write config with custom base_url
        config_path = project_dir / ".testforge" / "config.yaml"
        with open(config_path) as f:
            data = yaml.safe_load(f)
        data["extra"] = {"base_url": "https://myapp.test"}
        with open(config_path, "w") as f:
            yaml.dump(data, f)

        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            scripts = generate_playwright_scripts(project_dir)

        assert "https://myapp.test" in scripts[0]["source"]


# ---------------------------------------------------------------------------
# Tests: LLM-powered generation (mocked)
# ---------------------------------------------------------------------------


class TestGeneratePlaywrightWithMockLLM:
    """LLM-powered script generation with a mocked adapter."""

    VALID_SCRIPT = '''\
"""Playwright test: Verify Login."""

import re

from playwright.sync_api import Page, expect


def test_tc_f001_01(page: Page) -> None:
    """Verify Login."""
    page.goto("http://localhost:3000")
    page.get_by_label("Email").fill("user@test.com")
    page.get_by_label("Password").fill("pass123")
    page.get_by_role("button", name="Login").click()
    expect(page).to_have_url(re.compile(r".*/dashboard"))
    page.screenshot(path="evidence/tc_f001_01.png")
'''

    def test_llm_generated_script_used(self, project_with_cases: Path) -> None:
        """When LLM succeeds with valid Python, its output is used."""
        mock_adapter = _make_mock_adapter(self.VALID_SCRIPT)

        with patch("testforge.llm.create_adapter", return_value=mock_adapter):
            scripts = generate_playwright_scripts(project_with_cases)

        assert len(scripts) == len(SAMPLE_CASES)
        # The first script should contain LLM-generated content
        assert "get_by_label" in scripts[0]["source"]

    def test_llm_called_per_case(self, project_with_cases: Path) -> None:
        """LLM adapter.complete() is called once per test case."""
        mock_adapter = _make_mock_adapter(self.VALID_SCRIPT)

        with patch("testforge.llm.create_adapter", return_value=mock_adapter):
            generate_playwright_scripts(project_with_cases)

        assert mock_adapter.complete.call_count == len(SAMPLE_CASES)

    def test_llm_invalid_syntax_falls_back_to_skeleton(self, project_with_cases: Path) -> None:
        """When LLM returns invalid Python, skeleton is used instead."""
        bad_code = "def broken(\n    this is not valid python"
        mock_adapter = _make_mock_adapter(bad_code)

        with patch("testforge.llm.create_adapter", return_value=mock_adapter):
            scripts = generate_playwright_scripts(project_with_cases)

        # Skeleton should be used instead
        for script in scripts:
            assert _is_valid_python(script["source"])
            assert "# TODO: implement step action" in script["source"]

    def test_llm_markdown_fenced_code_extracted(self, project_with_cases: Path) -> None:
        """LLM response wrapped in markdown fences is properly extracted."""
        fenced = f"```python\n{self.VALID_SCRIPT}\n```"
        mock_adapter = _make_mock_adapter(fenced)

        with patch("testforge.llm.create_adapter", return_value=mock_adapter):
            scripts = generate_playwright_scripts(project_with_cases)

        assert "get_by_label" in scripts[0]["source"]
        assert "```" not in scripts[0]["source"]

    def test_llm_exception_falls_back_to_skeleton(self, project_with_cases: Path) -> None:
        """When LLM adapter raises an exception, skeleton scripts are generated."""
        mock_adapter = MagicMock(spec=LLMAdapter)
        mock_adapter.complete.side_effect = RuntimeError("API error")

        with patch("testforge.llm.create_adapter", return_value=mock_adapter):
            scripts = generate_playwright_scripts(project_with_cases)

        assert len(scripts) == len(SAMPLE_CASES)
        for script in scripts:
            assert _is_valid_python(script["source"])


# ---------------------------------------------------------------------------
# Tests: AST validation
# ---------------------------------------------------------------------------


class TestPlaywrightASTValidation:
    """Verify generated scripts pass ast.parse validation."""

    def test_skeleton_scripts_pass_ast_parse(self) -> None:
        """All skeleton scripts are parseable by ast.parse."""
        scripts = _generate_skeleton_scripts(SAMPLE_CASES, "http://localhost:3000")
        for script in scripts:
            tree = ast.parse(script["source"])
            # Should contain at least one function definition
            func_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            assert len(func_defs) >= 1, f"No function def in {script['case_id']}"

    def test_skeleton_scripts_pass_validator(self, tmp_path: Path) -> None:
        """Skeleton scripts pass the scripts.validator validation."""
        scripts = _generate_skeleton_scripts(SAMPLE_CASES, "http://localhost:3000")
        for script in scripts:
            path = tmp_path / script["path"]
            path.write_text(script["source"], encoding="utf-8")
            result = validate_script(path)
            assert result.valid, f"Validation failed for {script['case_id']}: {result.errors}"

    def test_is_valid_python_rejects_bad_syntax(self) -> None:
        """_is_valid_python correctly rejects invalid Python."""
        assert not _is_valid_python("def broken(\n    invalid")
        assert not _is_valid_python("class Foo[")

    def test_is_valid_python_accepts_good_syntax(self) -> None:
        """_is_valid_python accepts valid Python code."""
        assert _is_valid_python("x = 1\n")
        assert _is_valid_python("def foo():\n    pass\n")


# ---------------------------------------------------------------------------
# Tests: File writing via scripts/generator.py
# ---------------------------------------------------------------------------


class TestGenerateScriptsWritesFiles:
    """Verify that generate_scripts writes scripts to the filesystem."""

    def test_scripts_written_to_disk(self, project_with_cases: Path) -> None:
        """generate_scripts writes .py files to the scripts/ directory."""
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            scripts = generate_scripts(project_with_cases)

        scripts_dir = project_with_cases / "scripts"
        for script in scripts:
            script_path = scripts_dir / script["path"]
            assert script_path.exists(), f"Script file missing: {script_path}"

    def test_written_files_contain_source(self, project_with_cases: Path) -> None:
        """Written script files contain the expected source code."""
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            scripts = generate_scripts(project_with_cases)

        scripts_dir = project_with_cases / "scripts"
        for script in scripts:
            content = (scripts_dir / script["path"]).read_text(encoding="utf-8")
            assert content == script["source"]

    def test_written_files_are_valid_python(self, project_with_cases: Path) -> None:
        """All written script files are syntactically valid Python."""
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            scripts = generate_scripts(project_with_cases)

        scripts_dir = project_with_cases / "scripts"
        for script in scripts:
            result = validate_script(scripts_dir / script["path"])
            assert result.valid, f"Invalid script: {result.errors}"

    def test_empty_project_no_files_written(self, project_empty: Path) -> None:
        """No files written when there are no test cases."""
        scripts = generate_scripts(project_empty)
        assert scripts == []
        # scripts/ dir exists from project creation but should have no .py files
        py_files = list((project_empty / "scripts").glob("*.py"))
        assert py_files == []

    def test_unsupported_framework_raises(self, project_with_cases: Path) -> None:
        """Unsupported framework raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported framework"):
            generate_scripts(project_with_cases, framework="selenium")


# ---------------------------------------------------------------------------
# Tests: Utility functions
# ---------------------------------------------------------------------------


class TestSanitizeId:
    """Test _sanitize_id helper."""

    def test_hyphens_replaced(self) -> None:
        assert _sanitize_id("TC-F001-01") == "tc_f001_01"

    def test_dots_replaced(self) -> None:
        assert _sanitize_id("TC.F001.01") == "tc_f001_01"

    def test_spaces_replaced(self) -> None:
        assert _sanitize_id("TC F001 01") == "tc_f001_01"

    def test_already_valid(self) -> None:
        assert _sanitize_id("tc_f001_01") == "tc_f001_01"
