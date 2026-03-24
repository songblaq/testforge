"""Test execution endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from testforge.web.deps import resolve_project

router = APIRouter(prefix="/api/projects", tags=["execution"])


class RunRequest(BaseModel):
    tags: list[str] = []
    parallel: int = 1


@router.post("/{project_path:path}/run")
async def run_tests(project_path: str, body: RunRequest):
    """Execute test scripts in a project."""
    from testforge.execution.runner import run_tests as _run

    p = resolve_project(project_path)

    results = _run(p, body.tags or None, body.parallel)
    passed = sum(1 for r in results if r.get("status") == "passed")
    failed = len(results) - passed

    return {
        "results": results,
        "summary": {"total": len(results), "passed": passed, "failed": failed},
    }


@router.get("/{project_path:path}/runs")
async def list_runs(project_path: str):
    """List all test run history."""
    import json as _json
    from testforge.core.config import load_config

    p = resolve_project(project_path)
    config = load_config(p)
    output_dir = p / config.output_dir

    runs = []
    if output_dir.exists():
        for f in sorted(output_dir.glob("results*.json"), reverse=True):
            try:
                data = _json.loads(f.read_text())
                runs.append({
                    "file": f.name,
                    "started_at": data.get("started_at", ""),
                    "summary": data.get("summary", {}),
                    "result_count": len(data.get("results", [])),
                })
            except Exception:
                pass

    return {"runs": runs, "count": len(runs)}


@router.get("/{project_path:path}/run")
async def get_results(project_path: str):
    """Get most recent test run results."""
    import dataclasses
    from testforge.report.generator import load_test_run

    p = resolve_project(project_path)

    run = load_test_run(p)
    results = [dataclasses.asdict(r) for r in run.results] if run.results else []
    # Normalize field names to match the frontend (case_id, output)
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
