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
    input_dir = project_dir / config.input_dir
    input_count = len([f for f in input_dir.iterdir() if f.is_file() and not f.name.startswith(".")]) if input_dir.exists() else 0
    scripts_dir = project_dir / "scripts"
    script_count = len(list(scripts_dir.glob("*.py"))) if scripts_dir.exists() else 0

    return {
        "name": config.project_name or project_dir.name,
        "path": str(project_dir),
        "has_analysis": (project_dir / config.analysis_dir / "analysis.json").exists(),
        "has_cases": (project_dir / config.cases_dir / "cases.json").exists(),
        "has_scripts": script_count > 0,
        "has_report": (project_dir / config.output_dir / "report.md").exists()
        or (project_dir / config.output_dir / "report.html").exists(),
        "input_count": input_count,
        "script_count": script_count,
    }


def _resolve_project(project_path: str) -> Path:
    """Resolve and validate a project path with path-traversal protection."""
    from testforge.web.deps import resolve_project
    return resolve_project(project_path)


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


@router.get("/{project_path:path}/overview")
async def get_overview(project_path: str):
    """Get project overview with pipeline status."""
    import json as _json

    p = _resolve_project(project_path)
    from testforge.core.config import load_config
    config = load_config(p)

    input_dir = p / config.input_dir
    input_count = len([f for f in input_dir.iterdir() if f.is_file() and not f.name.startswith(".")]) if input_dir.exists() else 0

    analysis_path = p / config.analysis_dir / "analysis.json"
    has_analysis = analysis_path.exists()
    analysis_summary: dict = {}
    if has_analysis:
        data = _json.loads(analysis_path.read_text())
        analysis_summary = {
            "features": len(data.get("features", [])),
            "personas": len(data.get("personas", [])),
            "rules": len(data.get("rules", [])),
        }

    cases_path = p / config.cases_dir / "cases.json"
    has_cases = cases_path.exists()
    cases_summary: dict = {}
    if has_cases:
        cases = _json.loads(cases_path.read_text())
        cases_summary = {
            "total": len(cases),
            "functional": sum(1 for c in cases if c.get("type", c.get("case_type", "")) == "functional" or "TC-F" in c.get("id", "")),
            "usecase": sum(1 for c in cases if "UC-" in c.get("id", "")),
            "checklist": sum(1 for c in cases if "CL-" in c.get("id", "")),
            "crud": sum(1 for c in cases if "crud" in c.get("tags", [])),
        }

    scripts_dir = p / "scripts"
    script_count = len(list(scripts_dir.glob("*.py"))) if scripts_dir.exists() else 0

    results_path = p / config.output_dir / "results.json"
    has_run = results_path.exists()
    run_summary: dict = {}
    if has_run:
        data = _json.loads(results_path.read_text())
        run_summary = data.get("summary", {})
        run_summary["started_at"] = data.get("started_at", "")

    has_report = (p / config.output_dir / "report.md").exists() or (p / config.output_dir / "report.html").exists()

    return {
        "pipeline": [
            {"stage": "inputs", "status": "done" if input_count > 0 else "empty", "count": input_count},
            {"stage": "analysis", "status": "done" if has_analysis else "empty", "summary": analysis_summary},
            {"stage": "cases", "status": "done" if has_cases else "empty", "summary": cases_summary},
            {"stage": "scripts", "status": "done" if script_count > 0 else "empty", "count": script_count},
            {"stage": "execution", "status": "done" if has_run else "empty", "summary": run_summary},
            {"stage": "report", "status": "done" if has_report else "empty"},
        ],
        "project_name": config.project_name or p.name,
        "project_path": str(p),
    }


@router.get("/{project_path:path}/config")
async def get_project_config(project_path: str):
    """Get LLM and project configuration."""
    from testforge.core.config import load_config

    p = _resolve_project(project_path)
    config = load_config(p)
    return {
        "config": {
            "project_name": config.project_name,
            "llm_provider": config.llm_provider,
            "llm_model": config.llm_model,
            "version": config.version,
        }
    }


class ConfigUpdate(BaseModel):
    llm_provider: str | None = None
    llm_model: str | None = None
    project_name: str | None = None


@router.put("/{project_path:path}/config")
async def update_project_config(project_path: str, body: ConfigUpdate):
    """Update LLM provider, model, or project name."""
    from testforge.core.config import load_config, save_config

    p = _resolve_project(project_path)
    config = load_config(p)

    SUPPORTED_PROVIDERS = ("anthropic", "openai", "ollama", "google", "agent")
    if body.llm_provider is not None:
        if body.llm_provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported provider '{body.llm_provider}'. Supported: {SUPPORTED_PROVIDERS}",
            )
        config.llm_provider = body.llm_provider
    if body.llm_model is not None:
        config.llm_model = body.llm_model
    if body.project_name is not None:
        if not body.project_name.strip():
            raise HTTPException(status_code=400, detail="project_name cannot be empty")
        config.project_name = body.project_name.strip()

    save_config(p, config)
    return {
        "config": {
            "project_name": config.project_name,
            "llm_provider": config.llm_provider,
            "llm_model": config.llm_model,
        }
    }


@router.get("/{project_path:path}/config/test")
async def test_llm_connection(project_path: str):
    """Test LLM provider connectivity for a project."""
    from testforge.core.config import load_config

    p = _resolve_project(project_path)
    config = load_config(p)

    provider = config.llm_provider
    model = config.llm_model or "(default)"

    # Lightweight connectivity check per provider
    try:
        if provider == "ollama":
            import urllib.request
            req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
            req.read()
            status = "connected"
            message = f"Ollama reachable at localhost:11434 — model: {model}"
        elif provider == "anthropic":
            import os
            key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not key:
                status = "warning"
                message = "ANTHROPIC_API_KEY not set — LLM calls will fail"
            else:
                status = "configured"
                message = f"Anthropic API key found — model: {model or 'claude-3-5-sonnet-latest'}"
        elif provider == "openai":
            import os
            key = os.environ.get("OPENAI_API_KEY", "")
            if not key:
                status = "warning"
                message = "OPENAI_API_KEY not set — LLM calls will fail"
            else:
                status = "configured"
                message = f"OpenAI API key found — model: {model or 'gpt-4o'}"
        elif provider == "agent":
            from testforge.llm.agent import detect_agent_runtime

            runtime = detect_agent_runtime()
            if runtime:
                status = "connected"
                message = f"Agent runtime detected: {runtime}"
            else:
                status = "warning"
                message = (
                    "No agent runtime detected. Run TestForge inside Cursor, Claude Code, etc."
                )
        else:
            status = "unknown"
            message = f"Provider '{provider}' — manual check required"
    except Exception as exc:
        status = "error"
        message = str(exc)

    return {
        "provider": provider,
        "model": model,
        "status": status,
        "message": message,
    }


@router.delete("/{project_path:path}")
async def delete_project(project_path: str):
    """Delete a TestForge project."""
    p = _resolve_project(project_path)
    shutil.rmtree(p)
    return {"deleted": str(p)}
