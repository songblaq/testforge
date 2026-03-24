"""Script generation endpoints."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects", tags=["scripts"])


class ScriptRequest(BaseModel):
    force: bool = False
    no_llm: bool = False


@router.get("/{project_path:path}/scripts")
async def list_scripts(project_path: str):
    """List generated scripts with details."""
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    scripts_dir = p / "scripts"
    if not scripts_dir.exists():
        return {"scripts": [], "count": 0}

    scripts = []
    for f in sorted(scripts_dir.glob("*.py")):
        content = f.read_text(errors='replace')
        case_id = ""
        for line in content.split('\n')[:10]:
            if 'case_id' in line.lower() or 'test case' in line.lower():
                case_id = line.strip('# ').strip()
                break

        scripts.append({
            "name": f.name,
            "size": f.stat().st_size,
            "case_id": case_id,
            "lines": len(content.splitlines()),
            "preview": content[:500],
        })

    return {"scripts": scripts, "count": len(scripts)}


@router.post("/{project_path:path}/scripts")
async def generate_scripts(project_path: str, body: ScriptRequest):
    from testforge.scripts.generator import generate_scripts as _gen
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    scripts = _gen(p, no_llm=body.no_llm)
    return {"scripts": [str(s) for s in scripts], "count": len(scripts)}
