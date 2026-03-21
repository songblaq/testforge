"""Main pipeline orchestrator -- coordinates all stages end to end."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from testforge.core.config import load_config

logger = logging.getLogger(__name__)


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
    inputs: list[str] | None = None,
    case_type: str = "all",
    script_framework: str = "playwright",
    tags: list[str] | None = None,
    parallel: int = 1,
    report_format: str = "markdown",
    report_output: str | None = None,
) -> PipelineResult:
    """Run the TestForge pipeline on *project_dir*.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.
    stages:
        Optional list of stages to execute.  Defaults to all stages.
    inputs:
        Input files/URLs for the analyze stage.
    case_type:
        Test case type for the generate stage.
    script_framework:
        Framework for script generation.
    tags:
        Filter tags for the run stage.
    parallel:
        Number of parallel workers for the run stage.
    report_format:
        Output format for the report stage.
    report_output:
        Custom output path for the report.
    """
    config = load_config(project_dir)
    all_stages = ["analyze", "generate", "script", "run", "report"]
    requested = stages or all_stages
    result = PipelineResult(project=config.project_name)

    stage_runners = {
        "analyze": _run_analyze,
        "generate": _run_generate,
        "script": _run_script,
        "run": _run_execute,
        "report": _run_report,
    }

    for stage in requested:
        if stage not in all_stages:
            result.errors.append(f"Unknown stage: {stage}")
            continue

        try:
            runner = stage_runners[stage]
            stage_result = runner(
                project_dir,
                config=config,
                inputs=inputs or [],
                case_type=case_type,
                script_framework=script_framework,
                tags=tags or [],
                parallel=parallel,
                report_format=report_format,
                report_output=report_output,
            )
            result.stages_completed.append(stage)
            result.summary[stage] = stage_result
        except Exception as exc:
            logger.exception("Stage %s failed", stage)
            result.errors.append(f"Stage {stage} failed: {exc}")
            break  # stop on first failure

    return result


def _run_analyze(project_dir: Path, **kwargs: Any) -> dict[str, Any]:
    """Execute the analysis stage."""
    from testforge.analysis.analyzer import run_analysis

    inputs = kwargs.get("inputs", [])
    features = run_analysis(project_dir, inputs)
    return {"features_extracted": len(features)}


def _run_generate(project_dir: Path, **kwargs: Any) -> dict[str, Any]:
    """Execute the case generation stage."""
    from testforge.cases.generator import generate_cases

    case_type = kwargs.get("case_type", "all")
    cases = generate_cases(project_dir, case_type)
    return {"cases_generated": len(cases)}


def _run_script(project_dir: Path, **kwargs: Any) -> dict[str, Any]:
    """Execute the script generation stage."""
    from testforge.scripts.generator import generate_scripts

    framework = kwargs.get("script_framework", "playwright")
    scripts = generate_scripts(project_dir, framework)
    return {"scripts_generated": len(scripts)}


def _run_execute(project_dir: Path, **kwargs: Any) -> dict[str, Any]:
    """Execute the test run stage."""
    from testforge.execution.runner import run_tests

    tags = kwargs.get("tags", [])
    parallel = kwargs.get("parallel", 1)
    results = run_tests(project_dir, tags, parallel)
    passed = sum(1 for r in results if r.get("status") == "passed")
    return {"total": len(results), "passed": passed, "failed": len(results) - passed}


def _run_report(project_dir: Path, **kwargs: Any) -> dict[str, Any]:
    """Execute the report generation stage."""
    from testforge.report.generator import generate_report

    fmt = kwargs.get("report_format", "markdown")
    output = kwargs.get("report_output")
    path = generate_report(project_dir, fmt, output)
    return {"report_path": str(path)}
