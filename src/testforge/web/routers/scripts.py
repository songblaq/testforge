"""Script generation and management endpoints."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from testforge.web.deps import load_mappings, save_mappings

router = APIRouter(prefix="/api/projects", tags=["scripts"])


class ScriptRequest(BaseModel):
    force: bool = False
    no_llm: bool = False
    mode: Literal["generate", "regenerate"] = "generate"


class ScriptUpdate(BaseModel):
    content: str


class MappingEntry(BaseModel):
    case_id: str
    script_name: str
    source: str = "manual"  # manual | generated | approved


@router.get("/{project_path:path}/scripts")
async def list_scripts(project_path: str):
    """List generated scripts with details and authoritative mappings."""
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    scripts_dir = p / "scripts"
    if not scripts_dir.exists():
        return {"scripts": [], "count": 0}

    mappings = load_mappings(p)
    script_to_cases = {}
    for m in mappings:
        sn = m.get("script_name", "")
        if sn not in script_to_cases:
            script_to_cases[sn] = []
        script_to_cases[sn].append({
            "case_id": m.get("case_id", ""),
            "source": m.get("source", "unknown"),
        })

    scripts = []
    for f in sorted(scripts_dir.glob("*.py")):
        content = f.read_text(errors='replace')
        case_id = ""
        for line in content.split('\n')[:10]:
            if 'case_id' in line.lower() or 'test case' in line.lower():
                case_id = line.strip('# ').strip()
                break

        mapped_cases = script_to_cases.get(f.name, [])
        if not mapped_cases and case_id:
            mapped_cases = [{"case_id": case_id, "source": "heuristic"}]

        scripts.append({
            "name": f.name,
            "size": f.stat().st_size,
            "case_id": case_id,
            "lines": len(content.splitlines()),
            "preview": content[:500],
            "mapped_cases": mapped_cases,
        })

    return {"scripts": scripts, "count": len(scripts)}


@router.get("/{project_path:path}/scripts/{script_name}")
async def get_script_content(project_path: str, script_name: str):
    """Get full script content."""
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    script_path = p / "scripts" / script_name

    if ".." in script_name or "/" in script_name:
        raise HTTPException(status_code=400, detail="Invalid script name")
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script {script_name} not found")

    content = script_path.read_text(errors="replace")
    return {
        "name": script_name,
        "content": content,
        "lines": len(content.splitlines()),
        "size": script_path.stat().st_size,
    }


@router.put("/{project_path:path}/scripts/{script_name}")
async def update_script(project_path: str, script_name: str, body: ScriptUpdate):
    """Update script content."""
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    script_path = p / "scripts" / script_name

    if ".." in script_name or "/" in script_name:
        raise HTTPException(status_code=400, detail="Invalid script name")
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script {script_name} not found")

    script_path.write_text(body.content, encoding="utf-8")
    return {
        "name": script_name,
        "lines": len(body.content.splitlines()),
        "size": len(body.content.encode("utf-8")),
    }


@router.delete("/{project_path:path}/scripts/{script_name}")
async def delete_script(project_path: str, script_name: str):
    """Delete a script file."""
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    script_path = p / "scripts" / script_name

    if ".." in script_name or "/" in script_name:
        raise HTTPException(status_code=400, detail="Invalid script name")
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script {script_name} not found")

    script_path.unlink()

    mappings = load_mappings(p)
    mappings = [m for m in mappings if m.get("script_name") != script_name]
    save_mappings(p, mappings)

    return {"deleted": script_name}


@router.post("/{project_path:path}/scripts")
async def generate_scripts(project_path: str, body: ScriptRequest):
    from testforge.scripts.generator import generate_scripts as _gen
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    scripts = _gen(p, no_llm=body.no_llm)

    _auto_create_mappings(p)

    return {"scripts": [str(s) for s in scripts], "count": len(scripts)}


# --- Mapping management ---

@router.get("/{project_path:path}/mappings")
async def get_mappings(project_path: str):
    """Get all case↔script mappings."""
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    mappings = load_mappings(p)
    return {"mappings": mappings, "count": len(mappings)}


@router.post("/{project_path:path}/mappings")
async def add_mapping(project_path: str, body: MappingEntry):
    """Add a case↔script mapping."""
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    mappings = load_mappings(p)

    for m in mappings:
        if m.get("case_id") == body.case_id and m.get("script_name") == body.script_name:
            raise HTTPException(status_code=409, detail="Mapping already exists")

    mappings.append(body.model_dump())
    save_mappings(p, mappings)
    return {"mapping": body.model_dump(), "total": len(mappings)}


@router.delete("/{project_path:path}/mappings")
async def remove_mapping(project_path: str, case_id: str, script_name: str):
    """Remove a case↔script mapping."""
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    mappings = load_mappings(p)

    original = len(mappings)
    mappings = [m for m in mappings if not (m.get("case_id") == case_id and m.get("script_name") == script_name)]

    if len(mappings) == original:
        raise HTTPException(status_code=404, detail="Mapping not found")

    save_mappings(p, mappings)
    return {"deleted": True, "remaining": len(mappings)}


# --- Helpers ---


def _auto_create_mappings(project_dir):
    """Auto-generate mappings from script filenames after generation."""
    from testforge.core.project import load_cases

    scripts_dir = project_dir / "scripts"
    if not scripts_dir.exists():
        return

    cases = load_cases(project_dir)
    case_ids = {c.get("id", "").lower().replace("-", "_"): c.get("id", "") for c in cases}

    mappings = load_mappings(project_dir)
    existing = {(m["case_id"], m["script_name"]) for m in mappings}

    for f in scripts_dir.glob("*.py"):
        stem = f.stem.lower()
        for normalized, original_id in case_ids.items():
            if normalized in stem:
                if (original_id, f.name) not in existing:
                    mappings.append({
                        "case_id": original_id,
                        "script_name": f.name,
                        "source": "generated",
                    })
                    existing.add((original_id, f.name))

    save_mappings(project_dir, mappings)
