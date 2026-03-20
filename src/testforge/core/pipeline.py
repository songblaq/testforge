"""Main pipeline orchestrator -- coordinates all stages end to end."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from testforge.core.config import load_config


@dataclass
class PipelineResult:
    """Aggregated result of a full pipeline run."""

    project: str
    stages_completed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


def run_pipeline(
    project_dir: Path,
    *,
    stages: list[str] | None = None,
) -> PipelineResult:
    """Run the TestForge pipeline on *project_dir*.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.
    stages:
        Optional list of stages to execute.  Defaults to all stages.
    """
    config = load_config(project_dir)
    all_stages = ["analyze", "generate", "script", "run", "report"]
    requested = stages or all_stages
    result = PipelineResult(project=config.project_name)

    for stage in requested:
        if stage not in all_stages:
            result.errors.append(f"Unknown stage: {stage}")
            continue
        result.stages_completed.append(stage)

    return result
