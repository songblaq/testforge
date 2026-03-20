"""Feature extraction -- identify testable features from parsed documents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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


def extract_features(parsed_doc: dict[str, Any]) -> list[Feature]:
    """Extract features from a parsed document using LLM analysis.

    Parameters
    ----------
    parsed_doc:
        Output from an input parser.

    Returns
    -------
    list[Feature]:
        Extracted features.
    """
    # Placeholder: LLM-powered extraction would happen here
    return []
