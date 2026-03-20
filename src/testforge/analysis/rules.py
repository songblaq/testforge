"""Business rule extraction -- identify constraints and validation logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BusinessRule:
    """A business rule extracted from project documents."""

    id: str
    name: str
    description: str
    condition: str = ""
    expected_behavior: str = ""
    source: str = ""


def extract_rules(parsed_doc: dict[str, Any]) -> list[BusinessRule]:
    """Extract business rules from a parsed document.

    Parameters
    ----------
    parsed_doc:
        Output from an input parser.

    Returns
    -------
    list[BusinessRule]:
        Extracted business rules.
    """
    # Placeholder: LLM-powered rule extraction would happen here
    return []
