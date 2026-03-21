"""Feature extraction -- identify testable features from parsed documents."""

from __future__ import annotations

import logging
from typing import Any

from testforge.core.project import Feature
from testforge.llm.utils import extract_text_from_parsed_doc, parse_llm_json

logger = logging.getLogger(__name__)


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

    text = extract_text_from_parsed_doc(parsed_doc)
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
        features_data = parse_llm_json(response.text, fallback_key="features")
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
