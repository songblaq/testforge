"""Analysis endpoints -- run and view analysis results."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects", tags=["analysis"])


class AnalysisRequest(BaseModel):
    inputs: list[str] = []
    no_llm: bool = False


@router.post("/{project_path:path}/analysis")
async def run_analysis(project_path: str, body: AnalysisRequest):
    """Run analysis on a project."""
    from testforge.analysis.analyzer import run_analysis as _analyze
    from testforge.core.config import load_config
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)

    inputs = body.inputs
    if not inputs:
        config = load_config(p)
        input_dir = p / config.input_dir
        if input_dir.exists():
            inputs = [
                str(f) for f in input_dir.iterdir()
                if f.is_file() and not f.name.startswith(".")
            ]

    if not inputs:
        raise HTTPException(status_code=400, detail="No input files found or specified")

    results = _analyze(p, inputs, no_llm=body.no_llm)
    return {"results": results, "source_count": len(results)}


@router.get("/{project_path:path}/analysis")
async def get_analysis(project_path: str):
    """Get analysis results for a project."""
    from testforge.core.project import load_analysis
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)

    analysis = load_analysis(p)
    if analysis is None:
        raise HTTPException(status_code=404, detail="No analysis results found")

    return {"analysis": analysis.to_dict()}


@router.put("/{project_path:path}/analysis")
async def update_analysis(project_path: str, body: dict[str, Any]):
    """Update analysis results (edit features, personas, rules)."""
    from testforge.core.project import AnalysisResult, save_analysis
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)

    result = AnalysisResult.from_dict(body)
    save_analysis(p, result)
    return {"analysis": result.to_dict()}
