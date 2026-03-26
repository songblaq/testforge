"""Shared dependencies for web routers."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import HTTPException


def resolve_project(project_path: str) -> Path:
    """Resolve and validate a project path with path-traversal protection."""
    # Block traversal attempts (e.g. ../../etc/passwd)
    if ".." in Path(project_path).parts:
        raise HTTPException(status_code=403, detail="Access denied: path traversal not allowed")
    p = Path(project_path).resolve()
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {Path(project_path).name}")
    if not (p / ".testforge" / "config.yaml").exists():
        raise HTTPException(status_code=400, detail=f"Not a TestForge project: {project_path}")
    return p


def load_mappings(project_dir: Path) -> list:
    """Load case-script mappings from .testforge/mappings.json."""
    mappings_file = project_dir / ".testforge" / "mappings.json"
    if mappings_file.exists():
        return json.loads(mappings_file.read_text())
    return []


def save_mappings(project_dir: Path, mappings: list) -> None:
    """Save case-script mappings to .testforge/mappings.json."""
    mappings_file = project_dir / ".testforge" / "mappings.json"
    mappings_file.parent.mkdir(parents=True, exist_ok=True)
    mappings_file.write_text(json.dumps(mappings, indent=2, ensure_ascii=False), encoding="utf-8")
