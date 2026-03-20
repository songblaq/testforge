"""Script generator -- produces runnable test scripts from test cases."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def generate_scripts(project_dir: Path, framework: str = "playwright") -> list[dict[str, Any]]:
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

    return generators[framework](project_dir)


def _generate_playwright(project_dir: Path) -> list[dict[str, Any]]:
    """Generate Playwright test scripts."""
    from testforge.scripts.playwright import generate_playwright_scripts

    return generate_playwright_scripts(project_dir)
