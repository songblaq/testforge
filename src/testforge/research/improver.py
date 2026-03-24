"""Apply failure-analysis suggestions back into saved test cases."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from testforge.core.project import load_cases, save_cases


def apply_improvements(
    project_dir: Path,
    analysis: list[dict[str, Any]],
    *,
    iteration: int,
) -> list[str]:
    """Apply analysis suggestions to saved cases.

    The current implementation keeps the mutation scope intentionally small:
    it enriches matching cases with research history and failure context so the
    next script-generation step receives better guidance.
    """
    cases = load_cases(project_dir)
    if not cases:
        return []

    by_case_id = {a.get("case_id", ""): a for a in analysis if a.get("case_id")}
    changed: list[str] = []
    timestamp = datetime.now().isoformat(timespec="seconds")

    for case in cases:
        case_id = case.get("id", "")
        suggestion = by_case_id.get(case_id)
        if not suggestion or not suggestion.get("improvement_suggested"):
            continue

        note = suggestion.get("llm_analysis", "").strip()
        if not note:
            continue

        history = case.setdefault("research_history", [])
        history.append(
            {
                "iteration": iteration,
                "timestamp": timestamp,
                "error_message": suggestion.get("error_message", ""),
                "analysis": note,
            }
        )

        description = case.get("description", "")
        research_note = (
            f"\n\n[Research iteration {iteration}] "
            f"Failure context: {suggestion.get('error_message', '')}\n"
            f"Suggested improvement: {note}"
        )
        case["description"] = f"{description}{research_note}".strip()

        tags = case.setdefault("tags", [])
        if "research-improved" not in tags:
            tags.append("research-improved")

        changed.append(case_id)

    if changed:
        save_cases(project_dir, cases)

    return changed
