"""LLM-based project analyzer -- orchestrates feature, persona, and rule extraction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from testforge.input.parser import parse


def run_analysis(project_dir: Path, inputs: list[str]) -> list[dict[str, Any]]:
    """Analyze input files and produce a structured feature list.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.
    inputs:
        List of file paths or URLs to analyze.

    Returns
    -------
    list[dict]:
        Extracted features with metadata.
    """
    parsed_docs: list[dict[str, Any]] = []
    for inp in inputs:
        parsed_docs.append(parse(inp))

    # Placeholder: in a full implementation, each parsed doc would be sent
    # to the LLM for feature extraction, persona derivation, and rule analysis.
    features: list[dict[str, Any]] = []
    for doc in parsed_docs:
        features.append({
            "source": doc.get("source", ""),
            "type": doc.get("type", ""),
            "features": [],
            "personas": [],
            "rules": [],
        })

    return features
