"""Manual test checklist session endpoints."""

from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from testforge.web.deps import resolve_project

router = APIRouter(prefix="/api/projects", tags=["manual"])


class CheckItemRequest(BaseModel):
    status: Literal["pass", "fail", "pending"] = "pass"
    note: str = ""


class StartSessionRequest(BaseModel):
    no_llm: bool = False


@router.post("/{project_path:path}/manual/start")
async def start_session(project_path: str, body: StartSessionRequest | None = None):
    """Start a new manual test checklist session."""
    from testforge.cases.checklist import start_session as _start

    p = resolve_project(project_path)

    session = _start(p, no_llm=body.no_llm if body else False)
    return {
        "session_id": session.session_id,
        "items": session.items,
        "item_count": len(session.items),
    }


@router.put("/{project_path:path}/manual/check/{item_id}")
async def check_item(project_path: str, item_id: str, body: CheckItemRequest):
    """Record pass/fail for a checklist item."""
    from testforge.cases.checklist import check_item as _check

    p = resolve_project(project_path)

    try:
        session = _check(p, item_id, body.status, body.note)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {
        "item_id": item_id,
        "status": body.status,
        "checked": len(session.results),
        "total": len(session.items),
    }


@router.get("/{project_path:path}/manual/progress")
async def get_progress(project_path: str):
    """Get progress of the active manual test session."""
    from testforge.cases.checklist import session_progress

    p = resolve_project(project_path)

    try:
        progress = session_progress(p)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {"progress": progress}


@router.post("/{project_path:path}/manual/finish")
async def finish_session(project_path: str):
    """Finish the active session and save the final report."""
    from testforge.cases.checklist import finish_session as _finish

    p = resolve_project(project_path)

    try:
        report_path = _finish(p)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {"report_path": str(report_path)}


@router.get("/{project_path:path}/manual/sessions")
async def list_sessions(project_path: str):
    """List all completed manual QA sessions."""
    p = resolve_project(project_path)
    manual_dir = p / ".testforge" / "manual"
    sessions = []
    if manual_dir.exists():
        for f in sorted(manual_dir.glob("*.json"), reverse=True):
            if f.name == "active-session.json":
                continue
            try:
                data = json.loads(f.read_text())
                total = len(data.get("items", []))
                results = data.get("results", {})
                passed = sum(1 for r in results.values() if r.get("status") == "pass")
                failed = sum(1 for r in results.values() if r.get("status") == "fail")
                sessions.append(
                    {
                        "session_id": data.get("session_id", f.stem),
                        "started_at": data.get("started_at", ""),
                        "finished_at": data.get("finished_at", ""),
                        "total": total,
                        "passed": passed,
                        "failed": failed,
                    }
                )
            except Exception:
                continue
    return {"sessions": sessions}


@router.get("/{project_path:path}/manual/sessions/{session_id}")
async def get_session(project_path: str, session_id: str):
    """Get a specific completed session."""
    p = resolve_project(project_path)
    session_path = p / ".testforge" / "manual" / f"{session_id}.json"
    if not session_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    data = json.loads(session_path.read_text())
    return {"session": data}
