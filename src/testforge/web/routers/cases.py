"""Test case generation and management endpoints."""

from __future__ import annotations

import json
import uuid
from pathlib import PurePosixPath
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from testforge.web.deps import load_mappings, resolve_project, save_mappings

router = APIRouter(prefix="/api/projects", tags=["cases"])


class GenerateRequest(BaseModel):
    case_type: str = "all"
    no_llm: bool = False
    mode: Literal["generate", "regenerate", "new_version"] = "generate"


class CaseCreate(BaseModel):
    title: str
    description: str = ""
    feature_id: str = ""
    priority: str = "medium"
    type: str = "functional"
    tags: list[str] = []
    preconditions: list[str] = []
    steps: list[dict[str, str]] = []
    expected_result: str = ""
    rule_ids: list[str] = []
    status: str = "draft"


class CaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    feature_id: str | None = None
    priority: str | None = None
    type: str | None = None
    tags: list[str] | None = None
    preconditions: list[str] | None = None
    steps: list[dict[str, str]] | None = None
    expected_result: str | None = None
    rule_ids: list[str] | None = None
    status: str | None = None


class BulkDeleteRequest(BaseModel):
    case_ids: list[str]


@router.post("/{project_path:path}/cases")
async def generate_cases(project_path: str, body: GenerateRequest):
    """Generate test cases for a project."""
    from testforge.cases.generator import generate_cases as _generate
    from testforge.core.project import load_cases

    p = resolve_project(project_path)

    if body.mode == "regenerate":
        existing = load_cases(p)
        if existing:
            backup_path = p / "cases" / "cases_backup.json"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            with open(backup_path, "w") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)

    try:
        cases = _generate(p, body.case_type, no_llm=body.no_llm)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"cases": cases, "count": len(cases), "mode": body.mode}


@router.get("/{project_path:path}/cases")
async def get_cases(project_path: str):
    """Get generated test cases."""
    from testforge.core.project import load_cases

    p = resolve_project(project_path)
    cases = load_cases(p)
    if not cases:
        return {"cases": [], "count": 0}
    return {"cases": cases, "count": len(cases)}


@router.post("/{project_path:path}/cases/item")
async def create_case(project_path: str, body: CaseCreate):
    """Create a single test case manually."""
    from testforge.core.project import load_cases, save_cases

    p = resolve_project(project_path)
    cases = load_cases(p)

    new_case = body.model_dump()
    new_case["id"] = f"TC-{uuid.uuid4().hex[:8].upper()}"
    cases.append(new_case)
    save_cases(p, cases)

    return {"case": new_case, "count": len(cases)}


@router.put("/{project_path:path}/cases/item/{case_id}")
async def update_case(project_path: str, case_id: str, body: CaseUpdate):
    """Update a single test case."""
    from testforge.core.project import load_cases, save_cases

    p = resolve_project(project_path)
    cases = load_cases(p)

    found = None
    for c in cases:
        if c.get("id") == case_id:
            found = c
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    updates = body.model_dump(exclude_none=True)
    found.update(updates)
    save_cases(p, cases)

    return {"case": found}


@router.delete("/{project_path:path}/cases/item/{case_id}")
async def delete_case(project_path: str, case_id: str):
    """Delete a single test case."""
    from testforge.core.project import load_cases, save_cases

    p = resolve_project(project_path)
    cases = load_cases(p)

    original_count = len(cases)
    cases = [c for c in cases if c.get("id") != case_id]

    if len(cases) == original_count:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    save_cases(p, cases)
    mappings = load_mappings(p)
    filtered = [m for m in mappings if m.get("case_id") != case_id]
    save_mappings(p, filtered)
    return {"deleted": case_id, "remaining": len(cases)}


@router.get("/{project_path:path}/cases/{case_id}/scripts")
async def get_case_scripts(project_path: str, case_id: str):
    """Get scripts mapped to a specific case (authoritative mapping)."""
    p = resolve_project(project_path)
    mappings = load_mappings(p)

    mapped_script_names = []
    for m in mappings:
        if m.get("case_id") == case_id:
            mapped_script_names.append(m.get("script_name", ""))

    scripts_dir = p / "scripts"
    matched = []
    if scripts_dir.exists():
        scripts_dir_resolved = scripts_dir.resolve()
        for name in mapped_script_names:
            if not isinstance(name, str) or not name:
                continue
            safe_name = PurePosixPath(name).name
            if safe_name != name or ".." in name:
                continue
            f = scripts_dir / safe_name
            resolved = f.resolve()
            if not resolved.is_relative_to(scripts_dir_resolved):
                continue
            if resolved.exists() and resolved.is_file():
                content = resolved.read_text(errors="replace")
                matched.append({
                    "name": resolved.name,
                    "size": resolved.stat().st_size,
                    "lines": len(content.splitlines()),
                    "mapping_source": "authoritative",
                })

        if not matched:
            for f in scripts_dir.glob("*.py"):
                resolved = f.resolve()
                if not resolved.is_relative_to(scripts_dir_resolved):
                    continue
                if not resolved.is_file():
                    continue
                content = resolved.read_text(errors="replace")
                if case_id.lower().replace("-", "_") in f.stem.lower() or case_id in content:
                    matched.append({
                        "name": resolved.name,
                        "size": resolved.stat().st_size,
                        "lines": len(content.splitlines()),
                        "mapping_source": "heuristic",
                    })

    return {"scripts": matched, "count": len(matched), "case_id": case_id}


@router.put("/{project_path:path}/cases")
async def update_cases(project_path: str, body: list[dict[str, Any]]):
    """Update test cases (bulk edit/approve)."""
    from testforge.core.project import save_cases

    p = resolve_project(project_path)
    save_cases(p, body)
    return {"cases": body, "count": len(body)}


@router.post("/{project_path:path}/cases/bulk-delete")
async def bulk_delete_cases(project_path: str, body: BulkDeleteRequest):
    """Delete multiple test cases at once."""
    from testforge.core.project import load_cases, save_cases

    p = resolve_project(project_path)
    cases = load_cases(p)

    id_set = set(body.case_ids)
    remaining = [c for c in cases if c.get("id") not in id_set]
    deleted_count = len(cases) - len(remaining)

    save_cases(p, remaining)
    mappings = load_mappings(p)
    filtered = [m for m in mappings if m.get("case_id") not in id_set]
    save_mappings(p, filtered)
    return {"deleted_count": deleted_count, "remaining": len(remaining)}
