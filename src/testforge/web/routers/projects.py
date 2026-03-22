"""Project CRUD endpoints."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    directory: str = "."
    provider: str = "anthropic"
    model: str = ""


class ProjectOut(BaseModel):
    name: str
    path: str
    has_analysis: bool = False
    has_cases: bool = False
    has_report: bool = False


def _project_info(project_dir: Path) -> dict[str, Any]:
    """Build project info dict from a project directory."""
    from testforge.core.config import load_config

    config = load_config(project_dir)
    return {
        "name": config.project_name or project_dir.name,
        "path": str(project_dir),
        "has_analysis": (project_dir / config.analysis_dir / "analysis.json").exists(),
        "has_cases": (project_dir / config.cases_dir / "cases.json").exists(),
        "has_report": (project_dir / config.output_dir / "report.md").exists()
        or (project_dir / config.output_dir / "report.html").exists(),
    }


def _resolve_project(project_path: str) -> Path:
    """Resolve and validate a project path."""
    p = Path(project_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")
    if not (p / ".testforge" / "config.yaml").exists():
        raise HTTPException(
            status_code=400, detail=f"Not a TestForge project: {project_path}"
        )
    return p


@router.post("")
async def create_project(body: ProjectCreate):
    """Create a new TestForge project."""
    from testforge.core.config import TestForgeConfig, save_config
    from testforge.core.project import create_project as _create

    project_dir = Path(body.directory) / body.name
    if project_dir.exists():
        raise HTTPException(status_code=409, detail=f"Directory already exists: {project_dir}")

    _create(project_dir)

    if body.provider != "anthropic" or body.model:
        config = TestForgeConfig(
            project_name=body.name,
            llm_provider=body.provider,
            llm_model=body.model,
        )
        save_config(project_dir, config)

    return {"project": _project_info(project_dir)}


@router.get("")
async def list_projects(directory: str = Query(".", description="Base directory to scan")):
    """List TestForge projects in a directory."""
    from testforge.core.project import list_projects as _list

    base = Path(directory)
    if not base.exists():
        raise HTTPException(status_code=404, detail=f"Directory not found: {directory}")

    names = _list(base)
    projects = []
    for name in names:
        project_dir = base / name
        try:
            projects.append(_project_info(project_dir))
        except Exception:
            projects.append({"name": name, "path": str(project_dir)})

    return {"projects": projects}


@router.get("/{project_path:path}/info")
async def get_project(project_path: str):
    """Get details for a specific project."""
    p = _resolve_project(project_path)
    return {"project": _project_info(p)}


@router.delete("/{project_path:path}")
async def delete_project(project_path: str):
    """Delete a TestForge project."""
    p = _resolve_project(project_path)
    shutil.rmtree(p)
    return {"deleted": str(p)}
