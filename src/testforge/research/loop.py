"""AutoResearch loop -- iterative test improvement through LLM-powered analysis."""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from testforge.core.pipeline import run_pipeline
from testforge.core.project import load_cases, save_cases
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
    decision: str = "baseline"
    best_pass_rate_so_far: float = 0.0
    summary_path: str = ""
    iteration_path: str = ""


class ResearchNoOpError(RuntimeError):
    """Raised when a research run completes no meaningful work."""


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
    status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "strategy": self.strategy,
            "max_iterations": self.max_iterations,
            "threshold": self.threshold,
            "converged": self.converged,
            "final_pass_rate": self.final_pass_rate,
            "status": self.status,
            "iterations": [
                {
                    "iteration": it.iteration,
                    "pass_rate": it.pass_rate,
                    "total": it.total,
                    "passed": it.passed,
                    "failed": it.failed,
                    "skipped": it.skipped,
                    "improved_cases": it.improved_cases,
                    "timestamp": it.timestamp,
                    "decision": it.decision,
                    "best_pass_rate_so_far": it.best_pass_rate_so_far,
                    "summary_path": it.summary_path,
                    "iteration_path": it.iteration_path,
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
    ledger_dir: Path | None = None,
    plaza_runtime: str | None = None,
    no_llm: bool = False,
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
    best_pass_rate = -1.0
    pending_snapshot: list[dict[str, Any]] | None = None
    plaza_start_title = "TestForge research start"
    _plaza_log(
        "status",
        plaza_start_title,
        f"{config.project_name}: strategy={strategy}, max_iterations={max_iterations}, threshold={threshold}",
        runtime=plaza_runtime,
    )

    for i in range(1, max_iterations + 1):
        logger.info("Research iteration %d/%d", i, max_iterations)

        # Save iteration workspace
        iter_dir = research_dir / f"iter-{i:03d}"
        iter_dir.mkdir(parents=True, exist_ok=True)

        # Run full pipeline
        stages = ["analyze", "generate", "script", "run", "report"]
        if i > 1:
            if strategy in ("fix-failed", "both"):
                # Improvement stage mutates saved cases directly; regenerate scripts
                # from the updated cases rather than rebuilding cases from scratch.
                stages = ["script", "run", "report"]
            else:
                stages = ["generate", "script", "run", "report"]

        pipeline_result = run_pipeline(
            project_dir,
            stages=stages,
            inputs=inputs or [],
            no_llm=no_llm,
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
        iteration.iteration_path = str(iter_dir / "iteration-result.json")

        if test_run.total == 0:
            iteration.decision = "no-op"
            iteration.best_pass_rate_so_far = max(best_pass_rate, 0.0)
            summary.iterations.append(iteration)
            _save_iteration(iter_dir, iteration, test_run)
            _append_results_ledger(project_dir, summary, iteration, ledger_dir)
            summary.status = "no-op"
            summary.final_pass_rate = best_pass_rate if best_pass_rate >= 0 else 0.0
            summary_path = research_dir / "summary.json"
            summary_path.write_text(json.dumps(summary.to_dict(), indent=2, ensure_ascii=False))
            _plaza_log(
                "alert",
                "TestForge research no-op",
                f"{config.project_name}: zero test results, no meaningful experiment was produced",
                runtime=plaza_runtime,
            )
            raise ResearchNoOpError(
                "Research run produced zero test results; refusing to report a successful experiment"
            )

        if pending_snapshot is not None and pass_rate <= best_pass_rate:
            _restore_cases(project_dir, pending_snapshot)
            iteration.decision = "discard"
            pending_snapshot = None
        elif best_pass_rate < 0 or pass_rate > best_pass_rate:
            iteration.decision = "keep" if best_pass_rate >= 0 else "baseline"
            best_pass_rate = pass_rate
            pending_snapshot = None

        # Analyze failures and attempt improvement only when there is another
        # iteration to validate the mutated state.
        can_mutate = i < max_iterations and not summary.converged
        if test_run.failed > 0 and strategy in ("fix-failed", "both") and can_mutate:
            pending_snapshot = _snapshot_cases(project_dir)
            improved = _analyze_and_improve(project_dir, test_run, iter_dir)
            iteration.improved_cases = improved

        iteration.best_pass_rate_so_far = max(best_pass_rate, pass_rate)
        summary.iterations.append(iteration)
        _append_results_ledger(project_dir, summary, iteration, ledger_dir)
        _plaza_log(
            "status",
            f"TestForge research iter {i}",
            f"{config.project_name}: pass_rate={pass_rate:.3f}, decision={iteration.decision}, improved_cases={len(iteration.improved_cases)}",
            runtime=plaza_runtime,
        )

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
    if plaza_runtime and _plaza_check(plaza_start_title, runtime=plaza_runtime):
        _plaza_log(
            "done",
            "TestForge research done",
            f"{config.project_name}: converged={summary.converged}, final_pass_rate={summary.final_pass_rate:.3f}",
            runtime=plaza_runtime,
        )
    else:
        _plaza_log(
            "alert",
            "TestForge research log mismatch",
            f"{config.project_name}: start record not found in Plaza before done logging",
            runtime=plaza_runtime,
        )

    return summary


def _analyze_and_improve(
    project_dir: Path, test_run: ReportRun, iter_dir: Path
) -> list[str]:
    """Analyze failed tests and generate improved versions."""
    from testforge.research.analyzer import analyze_failures
    from testforge.research.improver import apply_improvements

    failed_cases = [r for r in test_run.results if r.status == "failed"]
    if not failed_cases:
        return []

    analysis = analyze_failures(project_dir, failed_cases)

    # Save analysis
    analysis_path = iter_dir / "failure-analysis.json"
    analysis_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False))

    return apply_improvements(
        project_dir,
        analysis,
        iteration=_infer_iteration(iter_dir),
    )


def _infer_iteration(iter_dir: Path) -> int:
    try:
        return int(iter_dir.name.split("-")[-1])
    except Exception:
        return 0


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
        "decision": iteration.decision,
        "best_pass_rate_so_far": iteration.best_pass_rate_so_far,
    }
    (iter_dir / "iteration-result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False)
    )


def _append_results_ledger(
    project_dir: Path,
    summary: ResearchSummary,
    iteration: IterationResult,
    ledger_dir: Path | None,
) -> None:
    target_dir = ledger_dir or (project_dir / "research")
    target_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = target_dir / "testforge-results.tsv"
    if not ledger_path.exists():
        ledger_path.write_text(
            "timestamp\tproject\titeration\tpass_rate\tpassed\tfailed\tskipped\timproved_cases\tdecision\tbest_pass_rate_so_far\tplaza_runtime\tsummary_path\titeration_path\tconverged\tstrategy\n",
            encoding="utf-8",
        )

    row = (
        f"{iteration.timestamp}\t{summary.project}\t{iteration.iteration}\t"
        f"{iteration.pass_rate:.4f}\t{iteration.passed}\t{iteration.failed}\t"
        f"{iteration.skipped}\t{len(iteration.improved_cases)}\t"
        f"{iteration.decision}\t{iteration.best_pass_rate_so_far:.4f}\t"
        f"{(ledger_dir.name if ledger_dir else 'project')}\t"
        f"{project_dir / 'research' / 'summary.json'}\t{iteration.iteration_path}\t"
        f"{str(summary.converged).lower()}\t{summary.strategy}\n"
    )
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(row)


def _snapshot_cases(project_dir: Path) -> list[dict[str, Any]] | None:
    cases = load_cases(project_dir)
    return json.loads(json.dumps(cases)) if cases else None


def _restore_cases(project_dir: Path, snapshot: list[dict[str, Any]] | None) -> None:
    if snapshot is None:
        return
    save_cases(project_dir, snapshot)


def _plaza_log(kind: str, title: str, body: str, *, runtime: str | None) -> bool:
    if not runtime:
        return False
    try:
        result = subprocess.run(
            [
                "aria",
                "khala",
                "plaza-log",
                "--type",
                kind,
                "--title",
                title,
                "--body",
                body,
                "--runtime",
                runtime,
                "--tags",
                "testforge,research",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        logger.debug("Plaza log skipped", exc_info=True)
        return False


def _plaza_check(title_fragment: str, *, runtime: str | None, minutes: int = 180) -> bool:
    if not runtime:
        return False
    try:
        result = subprocess.run(
            [
                "aria",
                "khala",
                "plaza-check",
                "--minutes",
                str(minutes),
                "--runtime",
                runtime,
                "--contains",
                title_fragment,
                "--require",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        logger.debug("Plaza check skipped", exc_info=True)
        return False
