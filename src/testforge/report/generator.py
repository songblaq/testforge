"""Report generator -- orchestrates report creation."""

from __future__ import annotations

from pathlib import Path


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
    output_dir = project_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    if fmt == "html":
        from testforge.report.html import render_html

        content = render_html(project_dir)
        ext = ".html"
    else:
        from testforge.report.markdown import render_markdown

        content = render_markdown(project_dir)
        ext = ".md"

    if output:
        out_path = Path(output)
    else:
        out_path = output_dir / f"report{ext}"

    out_path.write_text(content)
    return out_path
