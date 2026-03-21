"""Business rule extraction -- identify constraints and validation logic."""

from __future__ import annotations

import logging
from typing import Any

from testforge.core.project import BusinessRule
from testforge.llm.utils import extract_text_from_parsed_doc, parse_llm_json

logger = logging.getLogger(__name__)


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

    text = extract_text_from_parsed_doc(parsed_doc)
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
        rules_data = parse_llm_json(response.text, fallback_key="rules")
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
