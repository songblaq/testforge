"""Manual test checklist generation and session workflow."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from testforge.core.config import load_config
from testforge.core.project import load_analysis
from testforge.llm import create_adapter
from testforge.llm.utils import parse_llm_json


def _parse_json_array(text: str) -> list:
    """Backward-compatible shim; delegates to parse_llm_json."""
    return parse_llm_json(text)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Session workflow
# ---------------------------------------------------------------------------

_MANUAL_DIR = ".testforge/manual"


def _manual_dir(project_dir: Path) -> Path:
    return project_dir / _MANUAL_DIR


def _active_session_path(project_dir: Path) -> Path:
    return _manual_dir(project_dir) / "active-session.json"


@dataclass
class ChecklistSession:
    """State of an in-progress manual test session."""

    session_id: str
    started_at: str
    items: list[dict[str, Any]] = field(default_factory=list)
    results: dict[str, dict[str, Any]] = field(default_factory=dict)
    finished_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChecklistSession":
        return cls(
            session_id=data["session_id"],
            started_at=data["started_at"],
            items=data.get("items", []),
            results=data.get("results", {}),
            finished_at=data.get("finished_at", ""),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def start_session(project_dir: Path, no_llm: bool = False) -> ChecklistSession:
    """Start a new manual test checklist session.

    Generates checklist items and saves a session JSON to
    ``{project_dir}/.testforge/manual/active-session.json``.

    Returns the new session object.
    """
    items = generate_checklist(project_dir, no_llm=no_llm)
    session = ChecklistSession(
        session_id=str(uuid.uuid4()),
        started_at=_now_iso(),
        items=items,
    )
    _save_session(project_dir, session)
    return session


def check_item(
    project_dir: Path,
    item_id: str,
    status: str,
    note: str = "",
) -> ChecklistSession:
    """Record a pass/fail result for *item_id* in the active session.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.
    item_id:
        Checklist item ID (e.g. ``"CL-001"``).
    status:
        ``"pass"`` or ``"fail"``.
    note:
        Optional tester note.

    Returns the updated session.
    """
    session = _load_active_session(project_dir)
    session.results[item_id] = {
        "status": status,
        "note": note,
        "checked_at": _now_iso(),
    }
    _save_session(project_dir, session)
    return session


def session_progress(project_dir: Path) -> dict[str, Any]:
    """Return progress statistics for the active session.

    Returns a dict with keys: ``total``, ``checked``, ``passed``, ``failed``,
    ``pending``, ``percent``.
    """
    session = _load_active_session(project_dir)
    total = len(session.items)
    checked = len(session.results)
    passed = sum(1 for r in session.results.values() if r.get("status") == "pass")
    failed = sum(1 for r in session.results.values() if r.get("status") == "fail")
    pending = total - checked
    percent = round(checked / total * 100) if total else 0
    return {
        "total": total,
        "checked": checked,
        "passed": passed,
        "failed": failed,
        "pending": pending,
        "percent": percent,
    }


def finish_session(project_dir: Path) -> Path:
    """Finish the active session and persist the final report.

    Writes a timestamped result file to
    ``{project_dir}/.testforge/manual/{session_id}.json`` and removes the
    active-session pointer.

    Returns the path of the saved report.
    """
    session = _load_active_session(project_dir)
    session.finished_at = _now_iso()

    manual_dir = _manual_dir(project_dir)
    manual_dir.mkdir(parents=True, exist_ok=True)
    result_path = manual_dir / f"{session.session_id}.json"
    result_path.write_text(json.dumps(session.to_dict(), indent=2, ensure_ascii=False))

    active_path = _active_session_path(project_dir)
    if active_path.exists():
        active_path.unlink()

    return result_path


def _save_session(project_dir: Path, session: ChecklistSession) -> None:
    manual_dir = _manual_dir(project_dir)
    manual_dir.mkdir(parents=True, exist_ok=True)
    _active_session_path(project_dir).write_text(
        json.dumps(session.to_dict(), indent=2, ensure_ascii=False)
    )


def _load_active_session(project_dir: Path) -> ChecklistSession:
    active_path = _active_session_path(project_dir)
    if not active_path.exists():
        raise FileNotFoundError(
            f"No active session found in {project_dir}. Run 'testforge manual start' first."
        )
    data = json.loads(active_path.read_text())
    return ChecklistSession.from_dict(data)


@dataclass
class ChecklistItem:
    """A single item in a manual test checklist."""

    id: str
    title: str
    description: str
    category: str = ""
    feature_id: str = ""
    check_steps: list[str] = field(default_factory=list)
    pass_criteria: str = ""
    priority: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["steps"] = [
            {
                "order": i + 1,
                "action": step,
                "expected_result": self.pass_criteria,
                "input_data": "",
            }
            for i, step in enumerate(self.check_steps)
        ]
        return d


def generate_checklist(project_dir: Path, no_llm: bool = False) -> list[dict[str, Any]]:
    """Generate manual test checklists for human testers.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.

    Returns
    -------
    list[dict]:
        Manual test checklist items.
    """
    config = load_config(project_dir)
    analysis = load_analysis(project_dir)

    if analysis is None or not analysis.features:
        logger.info("No analysis results; skipping checklist generation")
        return []

    if no_llm:
        return _generate_skeleton_checklist(analysis)

    adapter_kwargs: dict[str, Any] = {}
    if config.llm_model:
        adapter_kwargs["model"] = config.llm_model

    try:
        adapter = create_adapter(config.llm_provider, **adapter_kwargs)
    except (ValueError, ImportError) as exc:
        logger.warning("LLM unavailable (%s), generating skeleton checklist", exc)
        return _generate_skeleton_checklist(analysis)

    try:
        return _llm_generate_checklist(adapter, analysis)
    except Exception as exc:
        logger.warning("LLM generation failed (%s), generating skeleton checklist", exc)
        return _generate_skeleton_checklist(analysis)


def _llm_generate_checklist(adapter: Any, analysis: Any) -> list[dict[str, Any]]:
    """Use LLM to generate a detailed manual test checklist."""
    features_text = "\n".join(
        f"- {f.id}: {f.name} -- {f.description}" for f in analysis.features
    )

    rules_text = "\n".join(
        f"- {r.id}: {r.name} -- {r.description}" for r in analysis.rules
    ) or "No specific business rules."

    prompt = f"""You are a QA engineer creating a manual test checklist for human testers.

FEATURES:
{features_text}

BUSINESS RULES:
{rules_text}

Generate a comprehensive manual test checklist. Each item should be:
- "id": unique checklist ID (e.g. "CL-001")
- "title": short checklist item title
- "description": what to check
- "category": category (e.g. "UI", "functionality", "accessibility", "performance")
- "feature_id": related feature ID
- "check_steps": array of step-by-step instructions for the tester
- "pass_criteria": clear criteria for pass/fail
- "priority": "high", "medium", or "low"

Include checks for: UI consistency, accessibility, error handling, edge cases, cross-browser.
Return a JSON array only."""

    response = adapter.complete(prompt, max_tokens=4096)
    items_data = parse_llm_json(response.text)

    items: list[dict[str, Any]] = []
    for i, item in enumerate(items_data):
        cl = ChecklistItem(
            id=item.get("id", f"CL-{i+1:03d}"),
            title=item.get("title", f"Checklist Item {i+1}"),
            description=item.get("description", ""),
            category=item.get("category", ""),
            feature_id=item.get("feature_id", ""),
            check_steps=item.get("check_steps", []),
            pass_criteria=item.get("pass_criteria", ""),
            priority=item.get("priority", "medium"),
        )
        items.append(cl.to_dict())

    return items


def _generate_skeleton_checklist(analysis: Any) -> list[dict[str, Any]]:
    """Generate minimal skeleton checklist without LLM."""
    items: list[dict[str, Any]] = []
    for i, feature in enumerate(analysis.features):
        cl = ChecklistItem(
            id=f"CL-{i+1:03d}",
            title=f"Manual check: {feature.name}",
            description=f"Verify {feature.name} manually: {feature.description}",
            category="functionality",
            feature_id=feature.id,
            check_steps=[
                f"Navigate to the {feature.name} area",
                "Verify all UI elements are displayed correctly",
                "Perform the primary action and observe results",
                "Check error handling with invalid input",
            ],
            pass_criteria=f"{feature.name} behaves as documented",
            priority=feature.priority,
        )
        items.append(cl.to_dict())
    return items
