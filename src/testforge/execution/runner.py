"""Test runner -- execute test scripts and aggregate results."""

from __future__ import annotations

from pathlib import Path
from typing import Any


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
    # Placeholder: discover and execute test scripts, collect evidence
    _ = tags, parallel
    return []
