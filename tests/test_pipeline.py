"""Tests for the pipeline orchestrator."""

from __future__ import annotations

from pathlib import Path

import testforge.core.pipeline as pipeline_module
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


def test_pipeline_no_llm_propagates(tmp_project: Path, monkeypatch) -> None:
    """Pipeline forwards no_llm to each stage runner."""
    seen: list[bool] = []

    def fake_stage(_project_dir: Path, **kwargs: object) -> dict[str, object]:
        seen.append(bool(kwargs.get("no_llm")))
        return {}

    monkeypatch.setattr(pipeline_module, "_run_analyze", fake_stage)
    monkeypatch.setattr(pipeline_module, "_run_generate", fake_stage)
    monkeypatch.setattr(pipeline_module, "_run_script", fake_stage)
    monkeypatch.setattr(pipeline_module, "_run_execute", fake_stage)
    monkeypatch.setattr(pipeline_module, "_run_report", fake_stage)

    result = run_pipeline(tmp_project, no_llm=True)

    assert result.success
    assert seen == [True, True, True, True, True]
