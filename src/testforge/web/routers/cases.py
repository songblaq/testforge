"""Test case generation and management endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from testforge.web.deps import resolve_project

router = APIRouter(prefix="/api/projects", tags=["cases"])


class GenerateRequest(BaseModel):
    case_type: str = "all"
    no_llm: bool = False


@router.post("/{project_path:path}/cases")
async def generate_cases(project_path: str, body: GenerateRequest):
    """Generate test cases for a project."""
    from testforge.cases.generator import generate_cases as _generate

    p = resolve_project(project_path)

    try:
        cases = _generate(p, body.case_type, no_llm=body.no_llm)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"cases": cases, "count": len(cases)}


@router.get("/{project_path:path}/cases")
async def get_cases(project_path: str):
    """Get generated test cases."""
    from testforge.core.project import load_cases

    p = resolve_project(project_path)

    cases = load_cases(p)
    if not cases:
        raise HTTPException(status_code=404, detail="No test cases found")

    return {"cases": cases, "count": len(cases)}


@router.get("/{project_path:path}/cases/{case_id}/scripts")
async def get_case_scripts(project_path: str, case_id: str):
    """Get scripts mapped to a specific case."""
    p = resolve_project(project_path)
    scripts_dir = p / "scripts"
    if not scripts_dir.exists():
        return {"scripts": [], "count": 0, "case_id": case_id}

    matched = []
    for f in scripts_dir.glob("*.py"):
        content = f.read_text(errors="replace")
        if case_id.lower().replace("-", "_") in f.stem.lower() or case_id in content:
            matched.append({
                "name": f.name,
                "size": f.stat().st_size,
                "lines": len(content.splitlines()),
            })
    return {"scripts": matched, "count": len(matched), "case_id": case_id}


@router.put("/{project_path:path}/cases")
async def update_cases(project_path: str, body: list[dict[str, Any]]):
    """Update test cases (bulk edit/approve)."""
    from testforge.core.project import save_cases

    p = resolve_project(project_path)

    save_cases(p, body)
    return {"cases": body, "count": len(body)}
