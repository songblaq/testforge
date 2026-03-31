"""HTML report renderer — enhanced with charts, filters, search, dark mode."""

from __future__ import annotations

import base64
import html
from datetime import datetime
from pathlib import Path

from testforge.core.locale_strings import s
from testforge.report.generator import ReportRun


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


def _render_donut_svg(passed: int, failed: int, skipped: int, total: int, locale: str = "ko") -> str:
    """Render an inline SVG donut chart for test results."""
    if total == 0:
        return '<p><em>No test data for chart.</em></p>'

    radius = 60
    circumference = 2 * 3.14159 * radius
    cx, cy = 80, 80

    segments = []
    offset = 0

    for count, color, label in [
        (passed, "#28a745", s("passed", locale)),
        (failed, "#dc3545", s("failed", locale)),
        (skipped, "#ffc107", s("skipped", locale)),
    ]:
        if count == 0:
            continue
        pct = count / total
        dash = circumference * pct
        gap = circumference - dash
        segments.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" '
            f'stroke="{color}" stroke-width="20" '
            f'stroke-dasharray="{dash:.1f} {gap:.1f}" '
            f'stroke-dashoffset="{-offset:.1f}" />'
        )
        offset += dash

    legend_items = ""
    for count, color, label in [
        (passed, "#28a745", s("passed", locale)),
        (failed, "#dc3545", s("failed", locale)),
        (skipped, "#ffc107", s("skipped", locale)),
    ]:
        if count > 0:
            pct = count / total * 100
            legend_items += (
                f'<span style="margin-right:1rem;">'
                f'<span style="display:inline-block;width:12px;height:12px;'
                f'background:{color};border-radius:2px;margin-right:4px;'
                f'vertical-align:middle;"></span>'
                f'{label}: {count} ({pct:.0f}%)</span>'
            )

    return f"""\
<div style="display:flex;align-items:center;gap:2rem;flex-wrap:wrap;">
  <svg width="160" height="160" viewBox="0 0 160 160" style="transform:rotate(-90deg);">
    {chr(10).join(segments)}
    <circle cx="{cx}" cy="{cy}" r="45" fill="var(--bg-color, #f7f8fa)" />
  </svg>
  <div>
    <div style="font-size:2rem;font-weight:700;">{passed}/{total}</div>
    <div style="color:var(--muted-color,#888);">pass rate</div>
    <div style="margin-top:0.5rem;">{legend_items}</div>
  </div>
</div>"""


def _try_inline_screenshot(path: str) -> str:
    """Try to inline a screenshot as base64. Falls back to file path text."""
    p = Path(path)
    if not p.exists():
        return f'<li><code>{_e(path)}</code> <em>(file not found)</em></li>'

    suffix = p.suffix.lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "gif": "image/gif", "webp": "image/webp"}.get(suffix.lstrip("."), "")

    if not mime:
        return f'<li><code>{_e(path)}</code></li>'

    try:
        data = base64.b64encode(p.read_bytes()).decode("ascii")
        return (
            f'<li><img src="data:{mime};base64,{data}" alt="{_e(p.name)}" '
            f'style="max-width:100%;border:1px solid var(--border-color,#ddd);'
            f'border-radius:4px;margin:0.5rem 0;" /><br/>'
            f'<code>{_e(p.name)}</code></li>'
        )
    except Exception:
        return f'<li><code>{_e(path)}</code></li>'


def render_html(test_run: ReportRun, locale: str = "ko") -> str:
    """Render an enhanced HTML test report with charts, filters, search, dark mode."""
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pass_rate = (
        f"{test_run.passed / test_run.total * 100:.1f}%" if test_run.total > 0 else "N/A"
    )

    # ---- donut chart ----
    donut = _render_donut_svg(test_run.passed, test_run.failed, test_run.skipped, test_run.total, locale)

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
        cases_html = f"<p><em>{s('no_results', locale)}</em></p>"
    else:
        for i, r in enumerate(test_run.results, 1):
            sc = _status_class(r.status)
            label = _status_label(r.status)
            tags_html = (
                " ".join(f'<span class="tag">{_e(t)}</span>' for t in r.tags)
                if r.tags else ""
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
                items = "".join(_try_inline_screenshot(p) for p in r.screenshot_paths)
                screenshots_html = f"<h4>Screenshots</h4><ul class='screenshots'>{items}</ul>"

            duration_html = (
                f"<span class='duration'>{r.duration_ms:.0f} ms</span>" if r.duration_ms else ""
            )

            cases_html += f"""\
<section class="case {sc}" data-status="{sc}" data-name="{_e(r.name.lower())}">
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
        items = "".join(_try_inline_screenshot(p) for p in all_screenshots)
        gallery_html = f"<section><h2>Evidence Gallery</h2><ul class='screenshots'>{items}</ul></section>"

    # ---- env section ----
    env_section = ""
    if env_rows:
        env_section = f"""
<section>
  <h2>Execution Info</h2>
  <table><tr><th>Key</th><th>Value</th></tr>{env_rows}</table>
</section>"""

    return _wrap_html(
        project=test_run.project,
        generated_at=generated_at,
        pass_rate=pass_rate,
        donut=donut,
        summary_total=test_run.total,
        summary_passed=test_run.passed,
        summary_failed=test_run.failed,
        summary_skipped=test_run.skipped,
        env_section=env_section,
        cases_html=cases_html,
        gallery_html=gallery_html,
        lbl_summary=s("summary", locale),
        lbl_total_tests=s("total_tests", locale),
        lbl_passed=s("passed", locale),
        lbl_failed=s("failed", locale),
        lbl_skipped=s("skipped", locale),
        lbl_pass_rate=s("pass_rate", locale),
        lbl_test_results=s("test_results", locale),
    )


def _wrap_html(
    *,
    project: str,
    generated_at: str,
    pass_rate: str,
    donut: str,
    summary_total: int,
    summary_passed: int,
    summary_failed: int,
    summary_skipped: int,
    env_section: str,
    cases_html: str,
    gallery_html: str,
    lbl_summary: str = "Summary",
    lbl_total_tests: str = "Total Tests",
    lbl_passed: str = "Passed",
    lbl_failed: str = "Failed",
    lbl_skipped: str = "Skipped",
    lbl_pass_rate: str = "Pass Rate",
    lbl_test_results: str = "Test Results",
) -> str:
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TestForge Report: {_e(project)}</title>
    <style>
        :root {{
            --bg-color: #f7f8fa;
            --text-color: #1a1a2e;
            --card-bg: #fff;
            --border-color: #ddd;
            --muted-color: #888;
            --header-color: #2d2d5e;
            --table-header-bg: #f4f4f4;
        }}
        [data-theme="dark"] {{
            --bg-color: #1a1a2e;
            --text-color: #e0e0e0;
            --card-bg: #2d2d44;
            --border-color: #444;
            --muted-color: #999;
            --header-color: #b0b0e0;
            --table-header-bg: #333;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 2rem;
            background: var(--bg-color); color: var(--text-color);
            transition: background 0.3s, color 0.3s;
        }}
        .container {{ max-width: 960px; margin: 0 auto; }}
        h1 {{ color: var(--text-color); border-bottom: 2px solid var(--border-color); padding-bottom: 0.5rem; }}
        h2 {{ color: var(--header-color); margin-top: 2rem; }}
        h3 {{ margin: 0.5rem 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; background: var(--card-bg); }}
        th, td {{ border: 1px solid var(--border-color); padding: 0.5rem 1rem; text-align: left; }}
        th {{ background: var(--table-header-bg); font-weight: 600; }}
        .case {{ background: var(--card-bg); border-radius: 6px; padding: 1rem 1.5rem;
                  margin: 1rem 0; border-left: 4px solid #ccc; }}
        .case.passed {{ border-left-color: #28a745; }}
        .case.failed {{ border-left-color: #dc3545; }}
        .case.skipped {{ border-left-color: #ffc107; }}
        .badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px;
                  font-size: 0.8rem; font-weight: 700; margin-right: 0.5rem; }}
        .badge.passed {{ background: #d4edda; color: #155724; }}
        .badge.failed {{ background: #f8d7da; color: #721c24; }}
        .badge.skipped {{ background: #fff3cd; color: #856404; }}
        .case-id {{ font-size: 0.85rem; color: var(--muted-color); margin-right: 0.5rem; }}
        .duration {{ font-size: 0.85rem; color: var(--muted-color); margin-right: 0.5rem; }}
        .tag {{ display: inline-block; background: #e9ecef; color: #495057;
                padding: 0.1rem 0.4rem; border-radius: 3px; font-size: 0.8rem; margin-right: 0.3rem; }}
        pre.error {{ background: #fff3f3; border: 1px solid #f5c6cb; border-radius: 4px;
                     padding: 0.75rem; overflow-x: auto; font-size: 0.9rem; color: #721c24; }}
        [data-theme="dark"] pre.error {{ background: #3a2020; border-color: #5a3030; color: #f5c6cb; }}
        .summary-table td:last-child {{ font-weight: 600; }}
        footer {{ margin-top: 3rem; color: var(--muted-color); font-size: 0.85rem;
                  border-top: 1px solid var(--border-color); padding-top: 1rem; }}
        footer a {{ color: var(--muted-color); }}
        .screenshots {{ list-style: none; padding: 0; }}
        .screenshots li {{ margin: 0.5rem 0; }}
        .screenshots img {{ max-height: 300px; }}

        /* Toolbar */
        .toolbar {{ display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; margin: 1rem 0; }}
        .toolbar input {{ padding: 0.4rem 0.8rem; border: 1px solid var(--border-color);
                          border-radius: 4px; font-size: 0.9rem; background: var(--card-bg);
                          color: var(--text-color); min-width: 200px; }}
        .filter-btn {{ padding: 0.3rem 0.7rem; border: 1px solid var(--border-color);
                       border-radius: 4px; background: var(--card-bg); color: var(--text-color);
                       cursor: pointer; font-size: 0.85rem; }}
        .filter-btn.active {{ background: var(--header-color); color: #fff; border-color: var(--header-color); }}
        .theme-toggle {{ margin-left: auto; padding: 0.3rem 0.7rem; border: 1px solid var(--border-color);
                         border-radius: 4px; background: var(--card-bg); color: var(--text-color);
                         cursor: pointer; font-size: 0.85rem; }}
    </style>
</head>
<body>
<div class="container">
    <h1>TestForge Report: {_e(project)}</h1>
    <p><em>Generated: {_e(generated_at)}</em></p>

    <section>
        <h2>{_e(lbl_summary)}</h2>
        {donut}
        <table class="summary-table">
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>{_e(lbl_total_tests)}</td><td>{summary_total}</td></tr>
            <tr><td>{_e(lbl_passed)}</td><td style="color:#28a745;">{summary_passed}</td></tr>
            <tr><td>{_e(lbl_failed)}</td><td style="color:#dc3545;">{summary_failed}</td></tr>
            <tr><td>{_e(lbl_skipped)}</td><td style="color:#ffc107;">{summary_skipped}</td></tr>
            <tr><td>{_e(lbl_pass_rate)}</td><td>{_e(pass_rate)}</td></tr>
        </table>
    </section>
    {env_section}
    <section>
        <h2>{_e(lbl_test_results)}</h2>
        <div class="toolbar">
            <input type="text" id="search" placeholder="Search tests..." oninput="filterCases()" />
            <button class="filter-btn active" data-filter="all" onclick="setFilter('all')">All</button>
            <button class="filter-btn" data-filter="passed" onclick="setFilter('passed')">Passed</button>
            <button class="filter-btn" data-filter="failed" onclick="setFilter('failed')">Failed</button>
            <button class="filter-btn" data-filter="skipped" onclick="setFilter('skipped')">Skipped</button>
            <button class="theme-toggle" onclick="toggleTheme()">Dark/Light</button>
        </div>
        <div id="cases">
        {cases_html}
        </div>
    </section>
    {gallery_html}
    <footer>Generated by <a href="https://github.com/songblaq/testforge">TestForge</a></footer>
</div>
<script>
let activeFilter = 'all';
function setFilter(f) {{
    activeFilter = f;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.dataset.filter === f));
    filterCases();
}}
function filterCases() {{
    const q = document.getElementById('search').value.toLowerCase();
    document.querySelectorAll('.case').forEach(c => {{
        const matchFilter = activeFilter === 'all' || c.dataset.status === activeFilter;
        const matchSearch = !q || (c.dataset.name && c.dataset.name.includes(q));
        c.style.display = (matchFilter && matchSearch) ? '' : 'none';
    }});
}}
function toggleTheme() {{
    const html = document.documentElement;
    html.dataset.theme = html.dataset.theme === 'dark' ? '' : 'dark';
}}
// Auto dark mode
if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {{
    document.documentElement.dataset.theme = 'dark';
}}
</script>
</body>
</html>"""
