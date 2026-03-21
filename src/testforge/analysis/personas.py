"""Persona derivation -- identify user types and their interaction patterns."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Persona:
    """A user persona derived from project analysis."""

    id: str
    name: str
    description: str
    goals: list[str] = field(default_factory=list)
    pain_points: list[str] = field(default_factory=list)
    tech_level: str = "intermediate"


def derive_personas(
    parsed_doc: dict[str, Any],
    adapter: Any | None = None,
) -> list[Persona]:
    """Derive user personas from a parsed document.

    Parameters
    ----------
    parsed_doc:
        Output from an input parser.
    adapter:
        Optional LLM adapter. If None, returns empty list.

    Returns
    -------
    list[Persona]:
        Derived user personas.
    """
    if adapter is None:
        return []

    text = _extract_text(parsed_doc)
    if not text.strip():
        return []

    prompt = f"""Analyze the following project documentation and identify distinct user personas.

Return a JSON array where each element has:
- "name": persona name (e.g. "Admin User", "New Customer")
- "description": brief description of this user type
- "goals": array of what this user wants to achieve
- "pain_points": array of frustrations or challenges
- "tech_level": "beginner", "intermediate", or "advanced"

DOCUMENT:
{text}

Respond with a JSON array only."""

    try:
        response = adapter.complete(prompt, max_tokens=2048)
        personas_data = _parse_json_array(response.text)
    except Exception as exc:
        logger.warning("Persona derivation failed: %s", exc)
        return []

    return [
        Persona(
            id=f"P-{i+1:03d}",
            name=p.get("name", f"Persona {i+1}"),
            description=p.get("description", ""),
            goals=p.get("goals", []),
            pain_points=p.get("pain_points", []),
            tech_level=p.get("tech_level", "intermediate"),
        )
        for i, p in enumerate(personas_data)
    ]


def _extract_text(parsed_doc: dict[str, Any]) -> str:
    """Extract plain text from a parsed document."""
    if "pages" in parsed_doc:
        return "\n\n".join(
            p.get("text", "") for p in parsed_doc["pages"] if p.get("text")
        )
    if "text" in parsed_doc:
        return parsed_doc["text"]
    if "content" in parsed_doc:
        return str(parsed_doc["content"])
    return ""


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
        if isinstance(result, dict) and "personas" in result:
            return result["personas"]
    except json.JSONDecodeError:
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except json.JSONDecodeError:
                pass

    return []
