"""LLM response parsing utilities."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def parse_llm_json(
    text: str,
    expected_type: str = "array",
    fallback_key: str | None = None,
) -> list | dict:
    """Parse JSON from an LLM response, handling common formatting issues.

    Parameters
    ----------
    text:
        Raw LLM response text.
    expected_type:
        ``"array"`` to expect a JSON array, ``"object"`` to expect a JSON object.
    fallback_key:
        When ``expected_type`` is ``"array"``, if the parsed result is a dict,
        try extracting this key as the array (e.g. ``"features"``).

    Returns
    -------
    list | dict:
        Parsed JSON value. Returns ``[]`` for array type or ``{}`` for object
        type on failure.
    """
    cleaned = text.strip()

    # Strip markdown code fences if present
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        cleaned = "\n".join(lines)

    if expected_type == "object":
        try:
            result = json.loads(cleaned)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        # Try to extract a JSON object from surrounding text
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                result = json.loads(cleaned[start:end])
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass
        logger.warning("Failed to parse LLM response as JSON object")
        return {}

    # expected_type == "array"
    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and fallback_key and fallback_key in result:
            return result[fallback_key]
    except json.JSONDecodeError:
        pass

    # Try to extract a JSON array from surrounding text
    start = cleaned.find("[")
    end = cleaned.rfind("]") + 1
    if start >= 0 and end > start:
        try:
            result = json.loads(cleaned[start:end])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    logger.warning("Failed to parse LLM response as JSON array")
    return []


def extract_text_from_parsed_doc(parsed_doc: dict[str, Any]) -> str:
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
