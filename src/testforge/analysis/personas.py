"""Persona derivation -- identify user types and their interaction patterns."""

from __future__ import annotations

import logging
from typing import Any

from testforge.core.project import Persona
from testforge.llm.utils import extract_text_from_parsed_doc, parse_llm_json

logger = logging.getLogger(__name__)


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

    text = extract_text_from_parsed_doc(parsed_doc)
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
        personas_data = parse_llm_json(response.text, fallback_key="personas")
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
