"""Test runner -- execute test scripts and aggregate results."""

from __future__ import annotations

import concurrent.futures
import logging
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from testforge.assertions.base import ASSERTION_REGISTRY, AssertionResult
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
class RunnerTestRun:
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


# Canonical alias used by report generation
TestRun = RunnerTestRun


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

    def _evaluate_assertions(
        self,
        assertion_defs: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> tuple[list[AssertionResult], bool]:
        """Evaluate a list of assertion definitions against *context*.

        Returns
        -------
        tuple[list[AssertionResult], bool]:
            All assertion results and whether every assertion passed.
        """
        # Ensure plugins are registered by importing the assertion modules.
        import testforge.assertions.api  # noqa: F401
        import testforge.assertions.custom  # noqa: F401
        import testforge.assertions.file  # noqa: F401
        import testforge.assertions.text  # noqa: F401

        results: list[AssertionResult] = []
        all_passed = True
        for a in assertion_defs:
            atype = a.get("type", "")
            params = a.get("params", {})
            plugin_cls = ASSERTION_REGISTRY.get(atype)
            if plugin_cls is None:
                result = AssertionResult(
                    passed=False,
                    message=f"Unknown assertion type: {atype!r}",
                )
            else:
                try:
                    result = plugin_cls().evaluate(atype, params, context)
                except Exception as exc:
                    result = AssertionResult(
                        passed=False,
                        message=f"Assertion {atype!r} raised: {exc}",
                    )
            results.append(result)
            if not result.passed:
                all_passed = False
        return results, all_passed

    def run_case(
        self,
        script_path: str,
        case_id: str,
        assertions: list[dict[str, Any]] | None = None,
    ) -> CaseResult:
        """Execute a single test case.

        Parameters
        ----------
        script_path:
            Path to the test script to execute.
        case_id:
            Identifier for this test case.
        assertions:
            Optional list of assertion definitions.  Each entry is a dict with
            ``type`` and ``params`` keys.

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

            # Evaluate assertions if provided
            assertion_results: list[AssertionResult] = []
            if assertions:
                context: dict[str, Any] = {"output": output, "raw": raw}
                assertion_results, all_passed = self._evaluate_assertions(
                    assertions, context
                )
                if not all_passed:
                    status = "failed"

            return CaseResult(
                case_id=case_id,
                status=status,
                duration_ms=duration_ms,
                output=output,
                error=error,
                evidence=evidence,
                assertions=[
                    {
                        "passed": r.passed,
                        "message": r.message,
                        "expected": r.expected,
                        "actual": r.actual,
                    }
                    for r in assertion_results
                ],
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

    def run_suite(
        self,
        scripts: list[tuple[str, str]] | list[tuple[str, str, list[dict[str, Any]]]],
        mode: str = "full",
    ) -> TestRun:
        """Execute a list of test cases and aggregate results.

        Parameters
        ----------
        scripts:
            List of ``(script_path, case_id)`` or
            ``(script_path, case_id, assertions)`` tuples.
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

        for entry in scripts:
            script_path, case_id = entry[0], entry[1]
            assertions: list[dict[str, Any]] | None = entry[2] if len(entry) > 2 else None  # type: ignore[misc]

            if mode == "smoke" and "must" not in case_id.lower():
                result = CaseResult(case_id=case_id, status="skipped")
                run.skipped += 1
            else:
                result = self.run_case(script_path, case_id, assertions=assertions)
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
    project_dir = project_dir.resolve()

    # Discover test scripts under project_dir/scripts/
    scripts_dir = project_dir / "scripts"
    if not scripts_dir.exists():
        return []

    conftest = scripts_dir / "conftest.py"
    if not conftest.exists():
        try:
            from testforge.scripts.playwright import PLAYWRIGHT_CONFTEST_PY
            conftest.write_text(PLAYWRIGHT_CONFTEST_PY, encoding="utf-8")
        except ImportError:
            pass

    scripts = sorted(
        p for p in scripts_dir.glob("*.py") if p.name != "conftest.py"
    )

    # Filter by tags: keep scripts whose stem contains any of the requested tags
    if tags:
        scripts = [s for s in scripts if any(tag in s.stem for tag in tags)]

    def _run_one(script: Path) -> dict[str, Any]:
        start = time.monotonic()
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(script),
                "-v",
                "--tb=short",
                "-q",
                "--no-header",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(project_dir),
        )
        duration = time.monotonic() - start
        # pytest exit codes: 0=passed, 1=failed, 2=interrupted, 3=internal error,
        # 4=command line error, 5=no tests collected
        if result.returncode == 0:
            status = "passed"
        elif result.returncode in (4, 5):
            status = "skipped"
        else:
            status = "failed"
        return {
            "case_id": script.stem,
            "script_name": script.name,
            "status": status,
            "output": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "duration": duration,
            "runner": "pytest",
        }

    results: list[dict[str, Any]] = []
    workers = max(1, parallel)
    if workers == 1:
        for script in scripts:
            results.append(_run_one(script))
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_run_one, s): s for s in scripts}
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

    return results
