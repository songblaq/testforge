"""Manual test checklist generation."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from testforge.core.config import load_config
from testforge.core.project import load_analysis

logger = logging.getLogger(__name__)


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
        return asdict(self)


def generate_checklist(project_dir: Path) -> list[dict[str, Any]]:
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

    from testforge.llm import create_adapter

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
    items_data = _parse_json_array(response.text)

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


def _parse_json_array(text: str) -> list[dict[str, Any]]:
    """Parse a JSON array from LLM response."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except json.JSONDecodeError:
                pass

    return []
