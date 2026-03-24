"""Tests for the TestForge research loop."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from testforge.cli import cli
from testforge.core.project import create_project, save_cases
from testforge.research.improver import apply_improvements
from testforge.research.loop import _append_results_ledger
from testforge.research.loop import ResearchNoOpError


def test_apply_improvements_updates_cases(tmp_path: Path) -> None:
    project_dir = tmp_path / "research-project"
    create_project(project_dir)
    save_cases(
        project_dir,
        [
            {
                "id": "TC-001",
                "title": "Example",
                "description": "Original description",
                "tags": [],
            }
        ],
    )

    changed = apply_improvements(
        project_dir,
        [
            {
                "case_id": "TC-001",
                "error_message": "Assertion failed",
                "llm_analysis": "Strengthen expectations",
                "improvement_suggested": True,
            }
        ],
        iteration=1,
    )

    assert changed == ["TC-001"]
    cases = json.loads((project_dir / "cases" / "cases.json").read_text())
    assert "research-improved" in cases[0]["tags"]
    assert "Strengthen expectations" in cases[0]["description"]
    assert cases[0]["research_history"][0]["iteration"] == 1


def test_append_results_ledger_creates_tsv(tmp_path: Path) -> None:
    from testforge.research.loop import IterationResult, ResearchSummary

    ledger_dir = tmp_path / "ledger"
    summary = ResearchSummary(project="demo", strategy="fix-failed", max_iterations=3, threshold=0.95)
    iteration = IterationResult(
        iteration=1,
        pass_rate=0.75,
        total=4,
        passed=3,
        failed=1,
        skipped=0,
        improved_cases=["TC-001"],
        timestamp="2026-03-22T00:00:00",
    )

    _append_results_ledger(tmp_path, summary, iteration, ledger_dir)
    text = (ledger_dir / "testforge-results.tsv").read_text()
    assert "timestamp\tproject\titeration" in text
    assert "demo\t1\t0.7500" in text
    assert "\tbaseline\t0.0000\tledger\t" in text


def test_research_cli_invokes_runner(tmp_path: Path, monkeypatch) -> None:
    project_dir = tmp_path / "cli-project"
    create_project(project_dir)

    called: dict[str, object] = {}

    class DummySummary:
        iterations = [1]
        final_pass_rate = 0.91
        converged = False

    def fake_run_research(*args, **kwargs):
        called["args"] = args
        called["kwargs"] = kwargs
        return DummySummary()

    monkeypatch.setattr("testforge.research.loop.run_research", fake_run_research)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "research",
            str(project_dir),
            "--max-iter",
            "2",
            "--threshold",
            "0.9",
            "--ledger-dir",
            str(tmp_path / "ledgers"),
            "--plaza-runtime",
            "codex",
        ],
    )

    assert result.exit_code == 0
    assert "Research complete" in result.output
    assert called["kwargs"]["max_iterations"] == 2
    assert called["kwargs"]["threshold"] == 0.9
    assert called["kwargs"]["plaza_runtime"] == "codex"


def test_research_cli_exits_nonzero_on_noop(tmp_path: Path, monkeypatch) -> None:
    project_dir = tmp_path / "noop-project"
    create_project(project_dir)

    def fake_run_research(*args, **kwargs):
        raise ResearchNoOpError("no meaningful work")

    monkeypatch.setattr("testforge.research.loop.run_research", fake_run_research)

    runner = CliRunner()
    result = runner.invoke(cli, ["research", str(project_dir)])
    assert result.exit_code == 1
    assert "Research no-op" in result.output


def test_research_cli_forwards_no_llm(tmp_path: Path, monkeypatch) -> None:
    project_dir = tmp_path / "offline-project"
    create_project(project_dir)

    seen: dict[str, object] = {}

    class DummySummary:
        iterations = [1]
        final_pass_rate = 1.0
        converged = True

    def fake_run_research(*args, **kwargs):
        seen.update(kwargs)
        return DummySummary()

    monkeypatch.setattr("testforge.research.loop.run_research", fake_run_research)

    runner = CliRunner()
    result = runner.invoke(cli, ["--no-llm", "research", str(project_dir)])

    assert result.exit_code == 0
    assert seen["no_llm"] is True
