"""Manual test checklist generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def generate_checklist(project_dir: Path) -> list[dict[str, Any]]:
    """Generate manual test checklists for human testers.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.

    Returns
    -------
    list[dict]:
        Manual test checklist items.
    """
    # Placeholder: LLM generates manual checklist from features + business rules
    return []
