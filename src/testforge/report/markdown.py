"""Markdown report renderer."""

from __future__ import annotations

import string
from datetime import datetime
from typing import TYPE_CHECKING

from testforge.core.locale_strings import s
from testforge.report.generator import ReportRun

if TYPE_CHECKING:
    from testforge.coverage.tracker import CoverageReport


# ---------------------------------------------------------------------------
# Jinja2 template (with string.Template fallback)
# ---------------------------------------------------------------------------

_TEMPLATE = """\
# {{ lbl_report_title }}: {{ project }}

_Generated: {{ generated_at }}_

---

## {{ lbl_summary }}

| Metric | Value |
|--------|-------|
| {{ lbl_total_tests }}  | {{ total }} |
| {{ lbl_passed }} | {{ passed }} |
| {{ lbl_failed }} | {{ failed }} |
| {{ lbl_skipped }} | {{ skipped }} |
{% if pass_rate is not none %}| {{ lbl_pass_rate }} | {{ pass_rate }}% |{% endif %}

{% if coverage %}
## {{ lbl_coverage }}

| Metric | Value |
|--------|-------|
| {{ lbl_features_covered }} | {{ coverage.covered_features }}/{{ coverage.total_features }} ({{ "%.0f"|format(coverage.feature_coverage_pct) }}%) |
| {{ lbl_rules_covered }} | {{ coverage.covered_rules }}/{{ coverage.total_rules }} ({{ "%.0f"|format(coverage.rule_coverage_pct) }}%) |
{% if coverage.uncovered_features %}| {{ lbl_uncovered_features }} | {{ coverage.uncovered_features | join(", ") }} |{% endif %}
{% if coverage.uncovered_rules %}| {{ lbl_uncovered_rules }} | {{ coverage.uncovered_rules | join(", ") }} |{% endif %}

{% endif %}
{% if started_at or finished_at %}
## {{ lbl_execution_info }}

| Key | Value |
|-----|-------|
{% if started_at %}| Started | {{ started_at }} |{% endif %}
{% if finished_at %}| Finished | {{ finished_at }} |{% endif %}
{% for k, v in environment.items() %}| {{ k }} | {{ v }} |
{% endfor %}
{% endif %}

## {{ lbl_test_results }}

{% if results %}
{% for r in results %}
### {{ loop.index }}. {{ r.name }}

- **Status**: {{ status_badge(r.status) }}
- **ID**: `{{ r.id }}`
{% if r.duration_ms %}- **Duration**: {{ "%.0f"|format(r.duration_ms) }} ms{% endif %}
{% if r.tags %}- **Tags**: {{ r.tags | join(", ") }}{% endif %}
{% if r.steps %}

**Steps**:

{% for step in r.steps %}
{{ loop.index }}. {{ step.get("description", step.get("name", str(step))) }}{% if step.get("status") %} -- _{{ step["status"] }}_{% endif %}
{% endfor %}
{% endif %}
{% if r.error_message %}

**Error**:

```
{{ r.error_message }}
```
{% endif %}
{% if r.screenshot_paths %}

**{{ lbl_screenshots }}**:

{% for path in r.screenshot_paths %}
- `{{ path }}`
{% endfor %}
{% endif %}

---
{% endfor %}
{% else %}
_{{ lbl_no_results }}_
{% endif %}

{% if all_screenshots %}
## {{ lbl_evidence_gallery }}

{% for path in all_screenshots %}
- `{{ path }}`
{% endfor %}
{% endif %}

---
_{{ lbl_generated_by }}_
"""

_SIMPLE_TEMPLATE = """\
# $lbl_report_title: $project

_Generated: $generated_at

---

## $lbl_summary

| Metric | Value |
|--------|-------|
| $lbl_total_tests | $total |
| $lbl_passed | $passed |
| $lbl_failed | $failed |
| $lbl_skipped | $skipped |

$coverage_section
## $lbl_test_results

$results_section

---
_${lbl_generated_by}_
"""


def _status_badge(status: str, locale: str = "ko") -> str:
    badge_keys = {
        "passed": "status_passed",
        "failed": "status_failed",
        "skipped": "status_skipped",
    }
    key = badge_keys.get(status.lower())
    if key:
        return s(key, locale)
    return status.upper()


def _render_with_jinja2(
    test_run: ReportRun,
    coverage: "CoverageReport | None" = None,
    locale: str = "ko",
) -> str:
    """Render using Jinja2."""
    from jinja2 import Environment

    env = Environment(trim_blocks=True, lstrip_blocks=True)
    env.globals["status_badge"] = lambda st: _status_badge(st, locale)

    tmpl = env.from_string(_TEMPLATE)

    pass_rate = None
    if test_run.total > 0:
        pass_rate = round(test_run.passed / test_run.total * 100, 1)

    all_screenshots: list[str] = []
    for r in test_run.results:
        all_screenshots.extend(r.screenshot_paths)

    return tmpl.render(
        project=test_run.project,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total=test_run.total,
        passed=test_run.passed,
        failed=test_run.failed,
        skipped=test_run.skipped,
        pass_rate=pass_rate,
        started_at=test_run.started_at,
        finished_at=test_run.finished_at,
        environment=test_run.environment,
        results=test_run.results,
        all_screenshots=all_screenshots,
        coverage=coverage,
        none=None,
        lbl_report_title=s("report_title", locale),
        lbl_summary=s("summary", locale),
        lbl_coverage=s("coverage", locale),
        lbl_execution_info=s("execution_info", locale),
        lbl_test_results=s("test_results", locale),
        lbl_passed=s("passed", locale),
        lbl_failed=s("failed", locale),
        lbl_skipped=s("skipped", locale),
        lbl_total_tests=s("total_tests", locale),
        lbl_pass_rate=s("pass_rate", locale),
        lbl_no_results=s("no_results", locale),
        lbl_generated_by=s("generated_by", locale),
        lbl_screenshots=s("screenshots", locale),
        lbl_features_covered=s("features_covered", locale),
        lbl_rules_covered=s("rules_covered", locale),
        lbl_uncovered_features=s("uncovered_features", locale),
        lbl_uncovered_rules=s("uncovered_rules", locale),
        lbl_evidence_gallery=s("evidence_gallery", locale),
    )


def _render_simple(
    test_run: ReportRun,
    coverage: "CoverageReport | None" = None,
    locale: str = "ko",
) -> str:
    """Render using string.Template (no Jinja2 required)."""
    lines: list[str] = []
    for i, r in enumerate(test_run.results, 1):
        lines.append(f"### {i}. {r.name}")
        lines.append(f"- **Status**: {_status_badge(r.status)}")
        lines.append(f"- **ID**: `{r.id}`")
        if r.duration_ms:
            lines.append(f"- **Duration**: {r.duration_ms:.0f} ms")
        if r.tags:
            lines.append(f"- **Tags**: {', '.join(r.tags)}")
        if r.error_message:
            lines.append("")
            lines.append("**Error**:")
            lines.append("")
            lines.append("```")
            lines.append(r.error_message)
            lines.append("```")
        if r.screenshot_paths:
            lines.append("")
            lines.append(f"**{s('screenshots', locale)}**:")
            for path in r.screenshot_paths:
                lines.append(f"- `{path}`")
        lines.append("")
        lines.append("---")

    results_section = "\n".join(lines) if lines else f"_{s('no_results', locale)}_"

    coverage_section = ""
    if coverage is not None:
        uncovered_f = ", ".join(coverage.uncovered_features) if coverage.uncovered_features else "none"
        uncovered_r = ", ".join(coverage.uncovered_rules) if coverage.uncovered_rules else "none"
        coverage_section = (
            f"## {s('coverage', locale)}\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            f"| {s('features_covered', locale)} | {coverage.covered_features}/{coverage.total_features}"
            f" ({coverage.feature_coverage_pct:.0f}%) |\n"
            f"| {s('rules_covered', locale)} | {coverage.covered_rules}/{coverage.total_rules}"
            f" ({coverage.rule_coverage_pct:.0f}%) |\n"
            f"| {s('uncovered_features', locale)} | {uncovered_f} |\n"
            f"| {s('uncovered_rules', locale)} | {uncovered_r} |\n\n"
        )

    tmpl = string.Template(_SIMPLE_TEMPLATE)
    return tmpl.substitute(
        project=test_run.project,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total=test_run.total,
        passed=test_run.passed,
        failed=test_run.failed,
        skipped=test_run.skipped,
        coverage_section=coverage_section,
        results_section=results_section,
        lbl_report_title=s("report_title", locale),
        lbl_summary=s("summary", locale),
        lbl_total_tests=s("total_tests", locale),
        lbl_passed=s("passed", locale),
        lbl_failed=s("failed", locale),
        lbl_skipped=s("skipped", locale),
        lbl_test_results=s("test_results", locale),
        lbl_generated_by=s("generated_by", locale),
    )


def render_markdown(
    test_run: ReportRun,
    coverage: "CoverageReport | None" = None,
    locale: str = "ko",
) -> str:
    """Render a Markdown test report.

    Parameters
    ----------
    test_run:
        Aggregated test run data.
    coverage:
        Optional coverage report to include a Coverage section.
    locale:
        Locale code for report labels (e.g. "ko", "en").

    Returns
    -------
    str:
        Markdown content.
    """
    try:
        return _render_with_jinja2(test_run, coverage, locale)
    except ImportError:
        return _render_simple(test_run, coverage, locale)
