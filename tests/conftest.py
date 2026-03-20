"""Shared test fixtures for TestForge."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal TestForge project in a temp directory."""
    from testforge.core.project import create_project

    project_dir = tmp_path / "test-project"
    create_project(project_dir)
    return project_dir
