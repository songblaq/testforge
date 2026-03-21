"""Report generator -- orchestrates report creation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class TestCaseResult:
    """Result for a single test case."""

    id: str
    name: str
    status: str  # passed, failed, skipped
    duration_ms: float = 0.0
    error_message: str = ""
    screenshot_paths: list[str] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class ReportRun:
    """Aggregated result of a full test execution."""

    __test__ = False  # prevent pytest from collecting this as a test class

    project: str
    started_at: str = ""
    finished_at: str = ""
    environment: dict[str, str] = field(default_factory=dict)
    results: list[TestCaseResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == "passed")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == "failed")

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.status == "skipped")

    @classmethod
    def from_results_json(cls, project: str, path: Path) -> "ReportRun":
        """Load a ReportRun from a results.json file produced by the run stage."""
        with open(path) as f:
            data = json.load(f)

        results = []
        for item in data.get("results", data if isinstance(data, list) else []):
            results.append(
                TestCaseResult(
                    id=item.get("id", ""),
                    name=item.get("name", item.get("id", "")),
                    status=item.get("status", "skipped"),
                    duration_ms=float(item.get("duration_ms", 0)),
                    error_message=item.get("error_message", item.get("error", "")),
                    screenshot_paths=item.get("screenshot_paths", item.get("screenshots", [])),
                    steps=item.get("steps", []),
                    tags=item.get("tags", []),
                )
            )

        return cls(
            project=project,
            started_at=data.get("started_at", "") if isinstance(data, dict) else "",
            finished_at=data.get("finished_at", "") if isinstance(data, dict) else "",
            environment=data.get("environment", {}) if isinstance(data, dict) else {},
            results=results,
        )


# Backward-compatible alias (pytest warning fix: class was renamed from TestRun)
TestRun = ReportRun


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_test_run(project_dir: Path) -> ReportRun:
    """Load test run results from project output directory.

    Falls back to an empty ReportRun when no results file exists.
    """
    from testforge.core.config import load_config

    config = load_config(project_dir)
    results_path = project_dir / config.output_dir / "results.json"

    if results_path.exists():
        return ReportRun.from_results_json(config.project_name, results_path)

    return ReportRun(
        project=config.project_name,
        started_at=datetime.now().isoformat(),
    )


def generate_report(
    project_dir: Path,
    fmt: str = "markdown",
    output: str | None = None,
) -> Path:
    """Generate a test report.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.
    fmt:
        Report format: ``markdown`` or ``html``.
    output:
        Optional output file path.

    Returns
    -------
    Path:
        Path to the generated report.
    """
    from testforge.core.config import load_config

    config = load_config(project_dir)
    output_dir = project_dir / config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    test_run = load_test_run(project_dir)

    if fmt == "html":
        from testforge.report.html import render_html

        content = render_html(test_run)
        ext = ".html"
    else:
        from testforge.report.markdown import render_markdown

        content = render_markdown(test_run)
        ext = ".md"

    if output:
        out_path = Path(output)
    else:
        out_path = output_dir / f"report{ext}"

    out_path.write_text(content, encoding="utf-8")
    return out_path
