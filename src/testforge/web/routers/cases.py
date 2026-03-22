"""Test case generation and management endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects", tags=["cases"])


class GenerateRequest(BaseModel):
    case_type: str = "all"


@router.post("/{project_path:path}/cases")
async def generate_cases(project_path: str, body: GenerateRequest):
    """Generate test cases for a project."""
    from testforge.cases.generator import generate_cases as _generate

    p = Path(project_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")

    try:
        cases = _generate(p, body.case_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"cases": cases, "count": len(cases)}


@router.get("/{project_path:path}/cases")
async def get_cases(project_path: str):
    """Get generated test cases."""
    from testforge.core.project import load_cases

    p = Path(project_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")

    cases = load_cases(p)
    if not cases:
        raise HTTPException(status_code=404, detail="No test cases found")

    return {"cases": cases, "count": len(cases)}


@router.put("/{project_path:path}/cases")
async def update_cases(project_path: str, body: list[dict[str, Any]]):
    """Update test cases (bulk edit/approve)."""
    from testforge.core.project import save_cases

    p = Path(project_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")

    save_cases(p, body)
    return {"cases": body, "count": len(body)}
