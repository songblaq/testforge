"""Test runner -- execute test scripts and aggregate results."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from testforge.execution.evidence import Evidence, EvidenceCollector

logger = logging.getLogger(__name__)


@dataclass
class CaseResult:
    """Result of a single test case execution."""

    case_id: str
    status: str  # passed, failed, skipped, error
    duration_ms: int = 0
    output: str = ""
    error: str | None = None
    evidence: list[Evidence] = field(default_factory=list)
    assertions: list[dict[str, Any]] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == "passed"


@dataclass
class TestRun:
    """Aggregated result of a test suite run."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration_ms: int = 0
    results: list[CaseResult] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.failed == 0 and self.errors == 0


class TestRunner:
    """Executes test scripts and aggregates results."""

    def __init__(self, config: Any, connector: Any) -> None:
        self.config = config
        self.connector = connector
        evidence_dir = Path(
            getattr(config, "evidence_dir", "evidence")
            if not isinstance(config, dict)
            else config.get("evidence_dir", "evidence")
        )
        self._collector = EvidenceCollector(evidence_dir)

    def run_case(self, script_path: str, case_id: str) -> CaseResult:
        """Execute a single test case.

        Parameters
        ----------
        script_path:
            Path to the test script to execute.
        case_id:
            Identifier for this test case.

        Returns
        -------
        CaseResult:
            Execution result including status, output, and evidence.
        """
        start = time.monotonic()
        try:
            raw = self.connector.execute(script_path)
            duration_ms = int((time.monotonic() - start) * 1000)

            status = raw.get("status", "failed")
            output = raw.get("output", "")
            error = raw.get("stderr") if raw.get("returncode", 0) != 0 else None

            # Collect log evidence
            evidence = []
            if output:
                ev = self._collector.add_log(case_id, output, step="stdout")
                evidence.append(ev)

            return CaseResult(
                case_id=case_id,
                status=status,
                duration_ms=duration_ms,
                output=output,
                error=error,
                evidence=evidence,
            )
        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.exception("Case %s raised an exception", case_id)
            return CaseResult(
                case_id=case_id,
                status="error",
                duration_ms=duration_ms,
                error=str(exc),
            )

    def run_suite(self, scripts: list[tuple[str, str]], mode: str = "full") -> TestRun:
        """Execute a list of test cases and aggregate results.

        Parameters
        ----------
        scripts:
            List of ``(script_path, case_id)`` tuples.
        mode:
            ``"smoke"`` runs only MUST-priority cases (those whose case_id
            contains ``"must"``).  ``"full"`` runs everything.

        Returns
        -------
        TestRun:
            Aggregated run result.
        """
        run = TestRun()
        suite_start = time.monotonic()

        for script_path, case_id in scripts:
            if mode == "smoke" and "must" not in case_id.lower():
                result = CaseResult(case_id=case_id, status="skipped")
                run.skipped += 1
            else:
                result = self.run_case(script_path, case_id)
                if result.status == "passed":
                    run.passed += 1
                elif result.status == "failed":
                    run.failed += 1
                elif result.status == "error":
                    run.errors += 1
                else:
                    run.skipped += 1

            run.results.append(result)
            run.total += 1

        run.duration_ms = int((time.monotonic() - suite_start) * 1000)
        return run


def run_tests(
    project_dir: Path,
    tags: list[str] | None = None,
    parallel: int = 1,
) -> list[dict[str, Any]]:
    """Execute test scripts in a project.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.
    tags:
        Optional tag filter.
    parallel:
        Number of parallel workers.

    Returns
    -------
    list[dict]:
        Test execution results.
    """
    # Discover test scripts under project_dir/scripts/
    scripts_dir = project_dir / "scripts"
    if not scripts_dir.exists():
        return []

    _ = tags, parallel
    results: list[dict[str, Any]] = []
    for script in sorted(scripts_dir.glob("*.py")):
        from testforge.execution.connectors.shell import ShellConnector

        connector = ShellConnector(cwd=str(project_dir))
        with connector:
            raw = connector.execute(f"python {script}")
        results.append({"case_id": script.stem, **raw})

    return results
