"""Test runner -- execute test scripts and aggregate results."""

from __future__ import annotations

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
    engines: list[str] | None = None,
    engine_configs: dict[str, dict[str, Any]] | None = None,
    cross_validate_enabled: bool = False,
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
    engines:
        List of engine names to use.  Defaults to ``["playwright"]`` (legacy
        pytest subprocess path).
    engine_configs:
        Per-engine configuration dicts keyed by engine name.
    cross_validate_enabled:
        When ``True`` and multiple engines are provided, compare results across
        engines and append a cross-validation summary entry.

    Returns
    -------
    list[dict]:
        Test execution results.
    """
    project_dir = project_dir.resolve()
    active_engines = engines or ["playwright"]

    # Legacy single-engine path (backward compat)
    if active_engines == ["playwright"]:
        return _run_tests_pytest(project_dir, tags=tags, parallel=parallel)

    # Multi-engine path via registry
    return _run_tests_multi_engine(
        project_dir,
        tags=tags,
        parallel=parallel,
        engines=active_engines,
        engine_configs=engine_configs or {},
        cross_validate_enabled=cross_validate_enabled,
    )


def _run_tests_pytest(
    project_dir: Path,
    tags: list[str] | None = None,
    parallel: int = 1,
) -> list[dict[str, Any]]:
    """Pytest runner -- runs all scripts in a single pytest session for efficiency."""
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

    if tags:
        scripts = [s for s in scripts if any(tag in s.stem for tag in tags)]

    if not scripts:
        return []

    # Run all scripts in a single pytest session with JUnit XML for per-test results
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        junit_path = tmp.name

    start = time.monotonic()
    cmd = [
        sys.executable, "-m", "pytest",
        *[str(s) for s in scripts],
        f"--junitxml={junit_path}",
        "-v", "--tb=short", "-q", "--no-header",
    ]
    workers = max(1, parallel)
    if workers > 1:
        cmd.extend(["-n", str(workers), "--dist=loadfile"])

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=max(120, len(scripts) * 5),
        cwd=str(project_dir),
    )
    total_duration = time.monotonic() - start

    results = _parse_junit_results(junit_path, scripts, total_duration, proc)

    # Clean up temp file
    try:
        Path(junit_path).unlink(missing_ok=True)
    except OSError:
        pass

    return results


def _parse_junit_results(
    junit_path: str,
    scripts: list[Path],
    total_duration: float,
    proc: subprocess.CompletedProcess[str],
) -> list[dict[str, Any]]:
    """Parse JUnit XML to extract per-test results."""
    import xml.etree.ElementTree as ET

    results: list[dict[str, Any]] = []
    script_map = {s.stem: s for s in scripts}

    try:
        tree = ET.parse(junit_path)
        root = tree.getroot()
        for testcase in root.iter("testcase"):
            name = testcase.get("name", "")
            duration = float(testcase.get("time", "0"))

            failure = testcase.find("failure")
            error = testcase.find("error")
            skipped_el = testcase.find("skipped")

            if failure is not None:
                status = "failed"
                err_msg = failure.get("message", "") or failure.text or ""
            elif error is not None:
                status = "error"
                err_msg = error.get("message", "") or error.text or ""
            elif skipped_el is not None:
                status = "skipped"
                err_msg = skipped_el.get("message", "")
            else:
                status = "passed"
                err_msg = ""

            case_id = name
            script_name = f"{name}.py"
            for stem, path in script_map.items():
                if stem in name or name in stem:
                    case_id = stem
                    script_name = path.name
                    break

            results.append({
                "case_id": case_id,
                "script_name": script_name,
                "status": status,
                "output": "",
                "stderr": err_msg,
                "duration": duration,
                "runner": "pytest",
            })
    except (ET.ParseError, FileNotFoundError):
        # Fallback: treat entire run as one result per script
        overall_status = "passed" if proc.returncode == 0 else "failed"
        per_script_dur = total_duration / max(len(scripts), 1)
        for script in scripts:
            results.append({
                "case_id": script.stem,
                "script_name": script.name,
                "status": overall_status,
                "output": proc.stdout,
                "stderr": proc.stderr,
                "duration": per_script_dur,
                "runner": "pytest",
            })

    return results


def _run_tests_multi_engine(
    project_dir: Path,
    engines: list[str],
    tags: list[str] | None = None,
    parallel: int = 1,
    engine_configs: dict[str, dict[str, Any]] | None = None,
    cross_validate_enabled: bool = False,
) -> list[dict[str, Any]]:
    """Run tests through multiple engines and optionally cross-validate."""
    from testforge.execution.engines.registry import get_engine
    from testforge.execution.engines.cross_validator import cross_validate, format_cross_validation_report

    engine_configs = engine_configs or {}

    scripts_dir = project_dir / "scripts"
    if not scripts_dir.exists():
        return []

    scripts = sorted(
        p for p in scripts_dir.glob("*.py") if p.name != "conftest.py"
    )
    if tags:
        scripts = [s for s in scripts if any(tag in s.stem for tag in tags)]

    results: list[dict[str, Any]] = []
    results_by_engine: dict[str, list[Any]] = {}

    for engine_name in engines:
        cfg = engine_configs.get(engine_name, {})
        try:
            engine = get_engine(engine_name, **cfg)
        except ValueError as exc:
            logger.warning("Skipping unknown engine %s: %s", engine_name, exc)
            continue

        engine_results = []
        for script in scripts:
            case_id = script.stem
            er = engine.execute(script, case_id)
            engine_results.append(er)
            results.append({
                "case_id": case_id,
                "script_name": script.name,
                "status": er.status,
                "output": er.output,
                "stderr": er.error,
                "duration": er.duration_ms / 1000.0,
                "runner": engine_name,
                "engine": engine_name,
            })
        results_by_engine[engine_name] = engine_results

    if cross_validate_enabled and len(results_by_engine) > 1:
        cv_results = cross_validate(results_by_engine)
        report = format_cross_validation_report(cv_results)
        disagree = sum(1 for r in cv_results if not r.all_agree)
        results.append({
            "case_id": "__cross_validation__",
            "status": "disagree" if disagree > 0 else "agree",
            "cross_validation_report": report,
            "total_cases": len(cv_results),
            "agreed": len(cv_results) - disagree,
            "disagreed": disagree,
            "runner": "cross_validator",
        })

    return results
