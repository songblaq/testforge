"""Tests for the pipeline orchestrator."""

from __future__ import annotations

from pathlib import Path

from testforge.core.pipeline import run_pipeline


def test_pipeline_all_stages(tmp_project: Path) -> None:
    """Pipeline runs all stages without error."""
    result = run_pipeline(tmp_project)
    assert result.success
    assert result.stages_completed == ["analyze", "generate", "script", "run", "report"]


def test_pipeline_selected_stages(tmp_project: Path) -> None:
    """Pipeline runs only selected stages."""
    result = run_pipeline(tmp_project, stages=["analyze", "report"])
    assert result.success
    assert result.stages_completed == ["analyze", "report"]


def test_pipeline_unknown_stage(tmp_project: Path) -> None:
    """Pipeline reports error for unknown stages."""
    result = run_pipeline(tmp_project, stages=["analyze", "nonexistent"])
    assert not result.success
    assert any("nonexistent" in e for e in result.errors)
