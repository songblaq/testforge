"""Analysis endpoints -- run and view analysis results."""

from __future__ import annotations

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


@router.post("/{project_path:path}/analysis/features")
async def add_feature(project_path: str, body: dict[str, Any]):
    """Add a single feature to analysis."""
    from testforge.core.project import AnalysisResult, load_analysis, save_analysis
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    analysis = load_analysis(p)
    if analysis is None:
        analysis = AnalysisResult(features=[], personas=[], rules=[])

    if not body.get("id"):
        body["id"] = f"F{len(analysis.features)+1:03d}"
    if not body.get("name"):
        raise HTTPException(status_code=400, detail="Feature name is required")

    analysis_dict = analysis.to_dict()
    analysis_dict["features"].append(body)
    result = AnalysisResult.from_dict(analysis_dict)
    save_analysis(p, result)
    return {"feature": body}


@router.put("/{project_path:path}/analysis/features/{feature_id}")
async def update_feature(project_path: str, feature_id: str, body: dict[str, Any]):
    """Update a single feature."""
    from testforge.core.project import AnalysisResult, load_analysis, save_analysis
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    analysis = load_analysis(p)
    if analysis is None:
        raise HTTPException(status_code=404, detail="No analysis results found")

    d = analysis.to_dict()
    found = False
    for f in d["features"]:
        if f.get("id") == feature_id:
            f.update(body)
            f["id"] = feature_id
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Feature {feature_id} not found")

    save_analysis(p, AnalysisResult.from_dict(d))
    return {"feature": next(f for f in d["features"] if f["id"] == feature_id)}


@router.delete("/{project_path:path}/analysis/features/{feature_id}")
async def delete_feature(project_path: str, feature_id: str):
    """Delete a single feature."""
    from testforge.core.project import AnalysisResult, load_analysis, save_analysis
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    analysis = load_analysis(p)
    if analysis is None:
        raise HTTPException(status_code=404, detail="No analysis results found")

    d = analysis.to_dict()
    original = len(d["features"])
    d["features"] = [f for f in d["features"] if f.get("id") != feature_id]

    if len(d["features"]) == original:
        raise HTTPException(status_code=404, detail=f"Feature {feature_id} not found")

    save_analysis(p, AnalysisResult.from_dict(d))
    return {"deleted": feature_id}


@router.post("/{project_path:path}/analysis/personas")
async def add_persona(project_path: str, body: dict[str, Any]):
    """Add a persona."""
    from testforge.core.project import AnalysisResult, load_analysis, save_analysis
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    analysis = load_analysis(p)
    if analysis is None:
        analysis = AnalysisResult(features=[], personas=[], rules=[])

    if not body.get("name"):
        raise HTTPException(status_code=400, detail="Persona name is required")

    if not body.get("id"):
        body["id"] = f"P{len(analysis.personas)+1:03d}"

    d = analysis.to_dict()
    d["personas"].append(body)
    save_analysis(p, AnalysisResult.from_dict(d))
    return {"persona": body}


@router.put("/{project_path:path}/analysis/personas/{persona_id}")
async def update_persona(project_path: str, persona_id: str, body: dict[str, Any]):
    """Update a persona."""
    from testforge.core.project import AnalysisResult, load_analysis, save_analysis
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    analysis = load_analysis(p)
    if analysis is None:
        raise HTTPException(status_code=404, detail="No analysis results found")

    d = analysis.to_dict()
    found = False
    for item in d["personas"]:
        if item.get("id") == persona_id:
            item.update(body)
            item["id"] = persona_id
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Persona {persona_id} not found")

    save_analysis(p, AnalysisResult.from_dict(d))
    return {"persona": next(i for i in d["personas"] if i["id"] == persona_id)}


@router.delete("/{project_path:path}/analysis/personas/{persona_id}")
async def delete_persona(project_path: str, persona_id: str):
    """Delete a persona."""
    from testforge.core.project import AnalysisResult, load_analysis, save_analysis
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    analysis = load_analysis(p)
    if analysis is None:
        raise HTTPException(status_code=404, detail="No analysis results found")

    d = analysis.to_dict()
    original = len(d["personas"])
    d["personas"] = [i for i in d["personas"] if i.get("id") != persona_id]

    if len(d["personas"]) == original:
        raise HTTPException(status_code=404, detail=f"Persona {persona_id} not found")

    save_analysis(p, AnalysisResult.from_dict(d))
    return {"deleted": persona_id}


@router.post("/{project_path:path}/analysis/rules")
async def add_rule(project_path: str, body: dict[str, Any]):
    """Add a business rule."""
    from testforge.core.project import AnalysisResult, load_analysis, save_analysis
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    analysis = load_analysis(p)
    if analysis is None:
        analysis = AnalysisResult(features=[], personas=[], rules=[])

    if not body.get("name"):
        raise HTTPException(status_code=400, detail="Rule name is required")

    if not body.get("id"):
        body["id"] = f"R{len(analysis.rules)+1:03d}"

    d = analysis.to_dict()
    d["rules"].append(body)
    save_analysis(p, AnalysisResult.from_dict(d))
    return {"rule": body}


@router.put("/{project_path:path}/analysis/rules/{rule_id}")
async def update_rule(project_path: str, rule_id: str, body: dict[str, Any]):
    """Update a business rule."""
    from testforge.core.project import AnalysisResult, load_analysis, save_analysis
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    analysis = load_analysis(p)
    if analysis is None:
        raise HTTPException(status_code=404, detail="No analysis results found")

    d = analysis.to_dict()
    found = False
    for item in d["rules"]:
        if item.get("id") == rule_id:
            item.update(body)
            item["id"] = rule_id
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    save_analysis(p, AnalysisResult.from_dict(d))
    return {"rule": next(i for i in d["rules"] if i["id"] == rule_id)}


@router.delete("/{project_path:path}/analysis/rules/{rule_id}")
async def delete_rule(project_path: str, rule_id: str):
    """Delete a business rule."""
    from testforge.core.project import AnalysisResult, load_analysis, save_analysis
    from testforge.web.deps import resolve_project

    p = resolve_project(project_path)
    analysis = load_analysis(p)
    if analysis is None:
        raise HTTPException(status_code=404, detail="No analysis results found")

    d = analysis.to_dict()
    original = len(d["rules"])
    d["rules"] = [i for i in d["rules"] if i.get("id") != rule_id]

    if len(d["rules"]) == original:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    save_analysis(p, AnalysisResult.from_dict(d))
    return {"deleted": rule_id}
