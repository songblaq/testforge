"""Script generator -- produces runnable test scripts from test cases."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def generate_scripts(
    project_dir: Path,
    framework: str = "playwright",
    no_llm: bool = False,
) -> list[dict[str, Any]]:
    """Generate automation scripts for a project.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.
    framework:
        Target framework (e.g. ``playwright``).

    Returns
    -------
    list[dict]:
        Generated script metadata.
    """
    generators = {
        "playwright": _generate_playwright,
    }

    if framework not in generators:
        raise ValueError(f"Unsupported framework: {framework}")

    scripts = generators[framework](project_dir, no_llm=no_llm)

    # Write generated scripts to the scripts/ directory
    if scripts:
        scripts_dir = project_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        for script in scripts:
            filename = script.get("path", "")
            source = script.get("source", "")
            if filename and source:
                out_path = scripts_dir / filename
                out_path.write_text(source, encoding="utf-8")
                logger.info("Wrote script: %s", out_path)

    return scripts


def _generate_playwright(project_dir: Path, no_llm: bool = False) -> list[dict[str, Any]]:
    """Generate Playwright test scripts."""
    from testforge.scripts.playwright import generate_playwright_scripts

    return generate_playwright_scripts(project_dir, no_llm=no_llm)
