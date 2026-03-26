"""Tests for execution runner path handling."""

from __future__ import annotations

from pathlib import Path

from testforge.execution.runner import run_tests


def test_run_tests_with_relative_project_path(tmp_project: Path, monkeypatch) -> None:
    """run_tests resolves relative project paths before invoking scripts."""
    script_path = tmp_project / "scripts" / "test_ok.py"
    script_path.write_text("def test_ok():\n    print('ok')\n    assert True\n", encoding="utf-8")

    monkeypatch.chdir(tmp_project.parent)
    results = run_tests(Path(tmp_project.name))

    assert len(results) == 1
    assert results[0]["status"] == "passed"
    assert "ok" in results[0]["output"]
