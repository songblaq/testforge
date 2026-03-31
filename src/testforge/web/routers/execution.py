"""Test execution endpoints with immutable run history."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from testforge.web.deps import resolve_project

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["execution"])
engines_router = APIRouter(prefix="/api", tags=["execution"])


class RunRequest(BaseModel):
    tags: list[str] = []
    parallel: int = Field(default=1, ge=1, le=16)
    engines: list[str] | None = None
    cross_validate: bool | None = None


@router.post("/{project_path:path}/run")
async def run_tests(project_path: str, body: RunRequest):
    """Execute test scripts and save immutable run record."""
    from testforge.core.config import load_config
    from testforge.execution.runner import run_tests as _run

    p = resolve_project(project_path)
    config = load_config(p)

    active_engines = body.engines if body.engines else config.execution_engines
    cv_enabled = body.cross_validate if body.cross_validate is not None else config.cross_validation

    results = _run(
        p,
        body.tags or None,
        body.parallel,
        engines=active_engines,
        engine_configs=config.engine_configs,
        cross_validate_enabled=cv_enabled,
    )

    for r in results:
        if "returncode" in r and "return_code" not in r:
            r["return_code"] = r.pop("returncode")
        if "duration" in r and "duration_ms" not in r:
            r["duration_ms"] = int(r.pop("duration") * 1000)

    test_rows = [r for r in results if r.get("case_id") != "__cross_validation__"]
    cv_rows = [r for r in results if r.get("case_id") == "__cross_validation__"]
    passed = sum(1 for r in test_rows if r.get("status") == "passed")
    failed = sum(1 for r in test_rows if r.get("status") == "failed")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    started_at = datetime.now(timezone.utc).isoformat()

    config = load_config(p)
    output_dir = p / config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    run_record = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(test_rows),
            "passed": passed,
            "failed": failed,
            "skipped": len(test_rows) - passed - failed,
        },
        "results": results,
        "cross_validation": cv_rows[0] if cv_rows else None,
        "environment": {
            "project": str(p),
            "tags": body.tags,
            "parallel": body.parallel,
            "engines": active_engines,
            "cross_validate": cv_enabled,
        },
    }

    run_file = output_dir / f"run_{run_id}.json"
    with open(run_file, "w") as f:
        json.dump(run_record, f, indent=2, ensure_ascii=False)

    also_latest = output_dir / "results.json"
    with open(also_latest, "w") as f:
        json.dump(run_record, f, indent=2, ensure_ascii=False)

    return {"run": run_record}


@router.get("/{project_path:path}/runs")
async def list_runs(project_path: str):
    """List all test run history (immutable)."""
    from testforge.core.config import load_config

    p = resolve_project(project_path)
    config = load_config(p)
    output_dir = p / config.output_dir

    runs = []
    if output_dir.exists():
        for f in sorted(output_dir.glob("run_*.json"), reverse=True):
            try:
                data = json.loads(f.read_text())
                runs.append({
                    "run_id": data.get("run_id", f.stem),
                    "file": f.name,
                    "started_at": data.get("started_at", ""),
                    "finished_at": data.get("finished_at", ""),
                    "summary": data.get("summary", {}),
                    "result_count": len(data.get("results", [])),
                    "environment": data.get("environment", {}),
                })
            except Exception as e:
                logger.warning("Skipping corrupt run file %s: %s", f.name, e)

        if not runs:
            for f in sorted(output_dir.glob("results*.json"), reverse=True):
                try:
                    data = json.loads(f.read_text())
                    runs.append({
                        "run_id": data.get("run_id", f.stem),
                        "file": f.name,
                        "started_at": data.get("started_at", ""),
                        "summary": data.get("summary", {}),
                        "result_count": len(data.get("results", [])),
                    })
                except Exception as e:
                    logger.warning("Skipping corrupt run file %s: %s", f.name, e)

    return {"runs": runs, "count": len(runs)}


@router.get("/{project_path:path}/runs/{run_id}")
async def get_run(project_path: str, run_id: str):
    """Get a specific run by ID."""
    from testforge.core.config import load_config

    p = resolve_project(project_path)
    config = load_config(p)
    output_dir = p / config.output_dir

    if ".." in run_id or "/" in run_id:
        raise HTTPException(status_code=400, detail="Invalid run_id")

    run_file = output_dir / f"run_{run_id}.json"
    if not run_file.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    data = json.loads(run_file.read_text())
    return {"run": data}


@engines_router.get("/engines")
async def list_engines():
    """List all registered engines and their availability."""
    from testforge.execution.engines.registry import all_engine_names, available_engines

    all_names = all_engine_names()
    avail = available_engines()
    return {
        "engines": [
            {"name": n, "available": n in avail}
            for n in all_names
        ],
    }


@router.get("/{project_path:path}/run")
async def get_results(project_path: str):
    """Get most recent test run results."""
    import dataclasses
    from testforge.report.generator import load_test_run

    p = resolve_project(project_path)

    run = load_test_run(p)
    results = [dataclasses.asdict(r) for r in run.results] if run.results else []
    for r in results:
        if "id" in r and "case_id" not in r:
            r["case_id"] = r["id"]
        if "error_message" in r and "output" not in r:
            r["output"] = r["error_message"]
    return {
        "run": {
            "project": run.project,
            "total": run.total,
            "passed": run.passed,
            "failed": run.failed,
            "skipped": run.skipped,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
            "results": results,
        }
    }
