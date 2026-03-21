"""HTML report renderer."""

from __future__ import annotations

import html
from datetime import datetime

from testforge.report.generator import TestRun


def _status_class(status: str) -> str:
    return {"passed": "passed", "failed": "failed", "skipped": "skipped"}.get(
        status.lower(), ""
    )


def _status_label(status: str) -> str:
    return {"passed": "PASSED", "failed": "FAILED", "skipped": "SKIPPED"}.get(
        status.lower(), status.upper()
    )


def _e(text: str) -> str:
    """HTML-escape a string."""
    return html.escape(str(text))


def render_html(test_run: TestRun) -> str:
    """Render an HTML test report.

    Parameters
    ----------
    test_run:
        Aggregated test run data.

    Returns
    -------
    str:
        HTML content.
    """
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pass_rate = (
        f"{test_run.passed / test_run.total * 100:.1f}%" if test_run.total > 0 else "N/A"
    )

    # ---- environment rows ----
    env_rows = ""
    if test_run.started_at:
        env_rows += f"<tr><td>Started</td><td>{_e(test_run.started_at)}</td></tr>\n"
    if test_run.finished_at:
        env_rows += f"<tr><td>Finished</td><td>{_e(test_run.finished_at)}</td></tr>\n"
    for k, v in test_run.environment.items():
        env_rows += f"<tr><td>{_e(k)}</td><td>{_e(v)}</td></tr>\n"

    # ---- test case sections ----
    cases_html = ""
    all_screenshots: list[str] = []

    if not test_run.results:
        cases_html = "<p><em>No test results available.</em></p>"
    else:
        for i, r in enumerate(test_run.results, 1):
            sc = _status_class(r.status)
            label = _status_label(r.status)
            tags_html = (
                " ".join(f'<span class="tag">{_e(t)}</span>' for t in r.tags)
                if r.tags
                else ""
            )

            steps_html = ""
            if r.steps:
                step_items = ""
                for step in r.steps:
                    desc = step.get("description", step.get("name", str(step)))
                    step_status = step.get("status", "")
                    suffix = f' <em>({_e(step_status)})</em>' if step_status else ""
                    step_items += f"<li>{_e(desc)}{suffix}</li>\n"
                steps_html = f"<h4>Steps</h4><ol>{step_items}</ol>"

            error_html = ""
            if r.error_message:
                error_html = f"<h4>Error</h4><pre class='error'>{_e(r.error_message)}</pre>"

            screenshots_html = ""
            if r.screenshot_paths:
                all_screenshots.extend(r.screenshot_paths)
                items = "".join(
                    f"<li><code>{_e(p)}</code></li>" for p in r.screenshot_paths
                )
                screenshots_html = f"<h4>Screenshots</h4><ul>{items}</ul>"

            duration_html = (
                f"<span class='duration'>{r.duration_ms:.0f} ms</span>" if r.duration_ms else ""
            )

            cases_html += f"""\
<section class="case {sc}">
  <h3>{i}. {_e(r.name)}</h3>
  <p>
    <span class="badge {sc}">{label}</span>
    <code class="case-id">{_e(r.id)}</code>
    {duration_html}
    {tags_html}
  </p>
  {steps_html}
  {error_html}
  {screenshots_html}
</section>
"""

    # ---- evidence gallery ----
    gallery_html = ""
    if all_screenshots:
        items = "".join(f"<li><code>{_e(p)}</code></li>" for p in all_screenshots)
        gallery_html = f"<section><h2>Evidence Gallery</h2><ul>{items}</ul></section>"

    # ---- env section ----
    env_section = ""
    if env_rows:
        env_section = f"""
<section>
  <h2>Execution Info</h2>
  <table>
    <tr><th>Key</th><th>Value</th></tr>
    {env_rows}
  </table>
</section>"""

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TestForge Report: {_e(test_run.project)}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 2rem; background: #f7f8fa; color: #1a1a2e;
        }}
        .container {{ max-width: 960px; margin: 0 auto; }}
        h1 {{ color: #1a1a2e; border-bottom: 2px solid #e0e0e0; padding-bottom: 0.5rem; }}
        h2 {{ color: #2d2d5e; margin-top: 2rem; }}
        h3 {{ margin: 0.5rem 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; background: #fff; }}
        th, td {{ border: 1px solid #ddd; padding: 0.5rem 1rem; text-align: left; }}
        th {{ background: #f4f4f4; font-weight: 600; }}
        .case {{ background: #fff; border-radius: 6px; padding: 1rem 1.5rem;
                  margin: 1rem 0; border-left: 4px solid #ccc; }}
        .case.passed {{ border-left-color: #28a745; }}
        .case.failed {{ border-left-color: #dc3545; }}
        .case.skipped {{ border-left-color: #ffc107; }}
        .badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px;
                  font-size: 0.8rem; font-weight: 700; margin-right: 0.5rem; }}
        .badge.passed {{ background: #d4edda; color: #155724; }}
        .badge.failed {{ background: #f8d7da; color: #721c24; }}
        .badge.skipped {{ background: #fff3cd; color: #856404; }}
        .case-id {{ font-size: 0.85rem; color: #666; margin-right: 0.5rem; }}
        .duration {{ font-size: 0.85rem; color: #888; margin-right: 0.5rem; }}
        .tag {{ display: inline-block; background: #e9ecef; color: #495057;
                padding: 0.1rem 0.4rem; border-radius: 3px; font-size: 0.8rem;
                margin-right: 0.3rem; }}
        pre.error {{ background: #fff3f3; border: 1px solid #f5c6cb; border-radius: 4px;
                     padding: 0.75rem; overflow-x: auto; font-size: 0.9rem; color: #721c24; }}
        .summary-table td:last-child {{ font-weight: 600; }}
        footer {{ margin-top: 3rem; color: #888; font-size: 0.85rem; border-top: 1px solid #e0e0e0; padding-top: 1rem; }}
        footer a {{ color: #666; }}
    </style>
</head>
<body>
<div class="container">
    <h1>TestForge Report: {_e(test_run.project)}</h1>
    <p><em>Generated: {_e(generated_at)}</em></p>

    <section>
        <h2>Summary</h2>
        <table class="summary-table">
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Tests</td><td>{test_run.total}</td></tr>
            <tr><td>Passed</td><td class="passed">{test_run.passed}</td></tr>
            <tr><td>Failed</td><td class="failed">{test_run.failed}</td></tr>
            <tr><td>Skipped</td><td>{test_run.skipped}</td></tr>
            <tr><td>Pass Rate</td><td>{_e(pass_rate)}</td></tr>
        </table>
    </section>
    {env_section}
    <section>
        <h2>Test Results</h2>
        {cases_html}
    </section>
    {gallery_html}
    <footer>Generated by <a href="https://github.com/songblaq/testforge">TestForge</a></footer>
</div>
</body>
</html>"""
