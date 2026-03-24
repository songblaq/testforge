"""Shared dependencies for web routers."""
from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException


def resolve_project(project_path: str) -> Path:
    """Resolve and validate a project path with path-traversal protection."""
    # Block traversal attempts (e.g. ../../etc/passwd)
    if ".." in Path(project_path).parts:
        raise HTTPException(status_code=403, detail="Access denied: path traversal not allowed")
    p = Path(project_path).resolve()
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")
    if not (p / ".testforge" / "config.yaml").exists():
        raise HTTPException(status_code=400, detail=f"Not a TestForge project: {project_path}")
    return p
