"""Feature extraction -- identify testable features from parsed documents."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Feature:
    """A testable feature extracted from input documents."""

    id: str
    name: str
    description: str
    category: str = ""
    priority: str = "medium"
    tags: list[str] = field(default_factory=list)
    source: str = ""


def extract_features(
    parsed_doc: dict[str, Any],
    adapter: Any | None = None,
) -> list[Feature]:
    """Extract features from a parsed document using LLM analysis.

    Parameters
    ----------
    parsed_doc:
        Output from an input parser.
    adapter:
        Optional LLM adapter. If None, returns empty list.

    Returns
    -------
    list[Feature]:
        Extracted features.
    """
    if adapter is None:
        return []

    text = _extract_text(parsed_doc)
    if not text.strip():
        return []

    prompt = f"""Analyze the following document and extract all testable features.

Return a JSON array where each element has:
- "name": short feature name
- "description": what the feature does
- "category": feature category (e.g. "authentication", "navigation", "data")
- "priority": "high", "medium", or "low"
- "tags": array of relevant tags

DOCUMENT:
{text}

Respond with a JSON array only."""

    try:
        response = adapter.complete(prompt, max_tokens=2048)
        features_data = _parse_json_array(response.text)
    except Exception as exc:
        logger.warning("Feature extraction failed: %s", exc)
        return []

    source = parsed_doc.get("source", "")
    return [
        Feature(
            id=f"F-{i+1:03d}",
            name=f.get("name", f"Feature {i+1}"),
            description=f.get("description", ""),
            category=f.get("category", ""),
            priority=f.get("priority", "medium"),
            tags=f.get("tags", []),
            source=source,
        )
        for i, f in enumerate(features_data)
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
        if isinstance(result, dict) and "features" in result:
            return result["features"]
    except json.JSONDecodeError:
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except json.JSONDecodeError:
                pass

    return []
