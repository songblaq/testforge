"""Business rule extraction -- identify constraints and validation logic."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BusinessRule:
    """A business rule extracted from project documents."""

    id: str
    name: str
    description: str
    condition: str = ""
    expected_behavior: str = ""
    source: str = ""


def extract_rules(
    parsed_doc: dict[str, Any],
    adapter: Any | None = None,
) -> list[BusinessRule]:
    """Extract business rules from a parsed document.

    Parameters
    ----------
    parsed_doc:
        Output from an input parser.
    adapter:
        Optional LLM adapter. If None, returns empty list.

    Returns
    -------
    list[BusinessRule]:
        Extracted business rules.
    """
    if adapter is None:
        return []

    text = _extract_text(parsed_doc)
    if not text.strip():
        return []

    prompt = f"""Analyze the following project documentation and extract all business rules, constraints, and validation logic.

Return a JSON array where each element has:
- "name": short rule name
- "description": what the rule enforces
- "condition": when this rule applies
- "expected_behavior": what should happen when the rule is triggered

DOCUMENT:
{text}

Respond with a JSON array only."""

    try:
        response = adapter.complete(prompt, max_tokens=2048)
        rules_data = _parse_json_array(response.text)
    except Exception as exc:
        logger.warning("Rule extraction failed: %s", exc)
        return []

    source = parsed_doc.get("source", "")
    return [
        BusinessRule(
            id=f"R-{i+1:03d}",
            name=r.get("name", f"Rule {i+1}"),
            description=r.get("description", ""),
            condition=r.get("condition", ""),
            expected_behavior=r.get("expected_behavior", ""),
            source=source,
        )
        for i, r in enumerate(rules_data)
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
        if isinstance(result, dict) and "rules" in result:
            return result["rules"]
    except json.JSONDecodeError:
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except json.JSONDecodeError:
                pass

    return []
