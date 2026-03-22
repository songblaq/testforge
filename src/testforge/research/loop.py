"""AutoResearch loop -- iterative test improvement through LLM-powered analysis."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from testforge.core.pipeline import run_pipeline
from testforge.report.generator import ReportRun, load_test_run

logger = logging.getLogger(__name__)


@dataclass
class IterationResult:
    """Result of a single research iteration."""

    iteration: int
    pass_rate: float
    total: int
    passed: int
    failed: int
    skipped: int
    improved_cases: list[str] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class ResearchSummary:
    """Summary of the full research loop."""

    project: str
    strategy: str
    max_iterations: int
    threshold: float
    iterations: list[IterationResult] = field(default_factory=list)
    converged: bool = False
    final_pass_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "strategy": self.strategy,
            "max_iterations": self.max_iterations,
            "threshold": self.threshold,
            "converged": self.converged,
            "final_pass_rate": self.final_pass_rate,
            "iterations": [
                {
                    "iteration": it.iteration,
                    "pass_rate": it.pass_rate,
                    "total": it.total,
                    "passed": it.passed,
                    "failed": it.failed,
                    "improved_cases": it.improved_cases,
                    "timestamp": it.timestamp,
                }
                for it in self.iterations
            ],
        }


def run_research(
    project_dir: Path,
    *,
    max_iterations: int = 3,
    threshold: float = 0.95,
    strategy: str = "fix-failed",
    inputs: list[str] | None = None,
) -> ResearchSummary:
    """Run the autonomous research loop.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.
    max_iterations:
        Maximum number of improvement iterations.
    threshold:
        Target pass rate (0.0 to 1.0). Loop stops when reached.
    strategy:
        Improvement strategy: fix-failed, expand-coverage, or both.
    inputs:
        Input files for the initial analysis.
    """
    from testforge.core.config import load_config

    config = load_config(project_dir)
    research_dir = project_dir / "research"
    research_dir.mkdir(parents=True, exist_ok=True)

    summary = ResearchSummary(
        project=config.project_name,
        strategy=strategy,
        max_iterations=max_iterations,
        threshold=threshold,
    )

    prev_pass_rate = 0.0

    for i in range(1, max_iterations + 1):
        logger.info("Research iteration %d/%d", i, max_iterations)

        # Save iteration workspace
        iter_dir = research_dir / f"iter-{i:03d}"
        iter_dir.mkdir(parents=True, exist_ok=True)

        # Run full pipeline
        stages = ["analyze", "generate", "script", "run", "report"]
        if i > 1:
            # After first iteration, only re-generate and re-run
            stages = ["generate", "script", "run", "report"]

        pipeline_result = run_pipeline(
            project_dir,
            stages=stages,
            inputs=inputs or [],
            report_format="html",
        )

        # Collect results
        test_run = load_test_run(project_dir)
        pass_rate = test_run.passed / test_run.total if test_run.total > 0 else 0.0

        iteration = IterationResult(
            iteration=i,
            pass_rate=pass_rate,
            total=test_run.total,
            passed=test_run.passed,
            failed=test_run.failed,
            skipped=test_run.skipped,
            timestamp=datetime.now().isoformat(),
        )

        # Analyze failures and attempt improvement
        if test_run.failed > 0 and strategy in ("fix-failed", "both"):
            improved = _analyze_and_improve(project_dir, test_run, iter_dir)
            iteration.improved_cases = improved

        summary.iterations.append(iteration)

        # Save iteration snapshot
        _save_iteration(iter_dir, iteration, test_run)

        # Convergence check
        if pass_rate >= threshold:
            logger.info("Target pass rate %.1f%% reached at iteration %d", threshold * 100, i)
            summary.converged = True
            summary.final_pass_rate = pass_rate
            break

        # Diminishing returns check
        improvement = pass_rate - prev_pass_rate
        if i > 1 and improvement < 0.01:
            logger.info("Diminishing returns (%.2f%% improvement). Stopping.", improvement * 100)
            summary.final_pass_rate = pass_rate
            break

        prev_pass_rate = pass_rate

    if not summary.converged:
        summary.final_pass_rate = summary.iterations[-1].pass_rate if summary.iterations else 0.0

    # Save summary
    summary_path = research_dir / "summary.json"
    summary_path.write_text(json.dumps(summary.to_dict(), indent=2, ensure_ascii=False))
    logger.info("Research summary saved to %s", summary_path)

    return summary


def _analyze_and_improve(
    project_dir: Path, test_run: ReportRun, iter_dir: Path
) -> list[str]:
    """Analyze failed tests and generate improved versions."""
    from testforge.research.analyzer import analyze_failures

    failed_cases = [r for r in test_run.results if r.status == "failed"]
    if not failed_cases:
        return []

    analysis = analyze_failures(project_dir, failed_cases)

    # Save analysis
    analysis_path = iter_dir / "failure-analysis.json"
    analysis_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False))

    return [a.get("case_id", "") for a in analysis if a.get("improvement_suggested")]


def _save_iteration(
    iter_dir: Path, iteration: IterationResult, test_run: ReportRun
) -> None:
    """Save iteration results to disk."""
    result = {
        "iteration": iteration.iteration,
        "pass_rate": iteration.pass_rate,
        "total": iteration.total,
        "passed": iteration.passed,
        "failed": iteration.failed,
        "skipped": iteration.skipped,
        "improved_cases": iteration.improved_cases,
        "timestamp": iteration.timestamp,
    }
    (iter_dir / "iteration-result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False)
    )
