"""Test execution endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects", tags=["execution"])


class RunRequest(BaseModel):
    tags: list[str] = []
    parallel: int = 1


@router.post("/{project_path:path}/run")
async def run_tests(project_path: str, body: RunRequest):
    """Execute test scripts in a project."""
    from testforge.execution.runner import run_tests as _run

    p = Path(project_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")

    results = _run(p, body.tags or None, body.parallel)
    passed = sum(1 for r in results if r.get("status") == "passed")
    failed = len(results) - passed

    return {
        "results": results,
        "summary": {"total": len(results), "passed": passed, "failed": failed},
    }


@router.get("/{project_path:path}/run")
async def get_results(project_path: str):
    """Get most recent test run results."""
    from testforge.report.generator import load_test_run

    p = Path(project_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")

    run = load_test_run(p)
    return {
        "run": {
            "project": run.project,
            "total": run.total,
            "passed": run.passed,
            "failed": run.failed,
            "skipped": run.skipped,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
        }
    }
