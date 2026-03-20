"""Project management -- create, list, and manage TestForge projects."""

from __future__ import annotations

from pathlib import Path

from testforge.core.config import TestForgeConfig, save_config


def create_project(project_dir: Path) -> Path:
    """Create a new TestForge project with default structure."""
    project_dir.mkdir(parents=True, exist_ok=True)

    subdirs = ["inputs", "output", "evidence", "scripts", "cases"]
    for subdir in subdirs:
        (project_dir / subdir).mkdir(exist_ok=True)

    config = TestForgeConfig(project_name=project_dir.name)
    save_config(project_dir, config)

    return project_dir


def list_projects(base_dir: Path | None = None) -> list[str]:
    """List TestForge projects found under *base_dir* (default: cwd)."""
    base = base_dir or Path.cwd()
    projects: list[str] = []

    for candidate in base.iterdir():
        if candidate.is_dir() and (candidate / ".testforge" / "config.yaml").exists():
            projects.append(candidate.name)

    return sorted(projects)
