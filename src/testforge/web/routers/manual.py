"""Manual test checklist session endpoints."""

from __future__ import annotations

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
