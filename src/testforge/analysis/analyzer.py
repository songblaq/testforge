"""LLM-based project analyzer -- orchestrates feature, persona, and rule extraction."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from testforge.core.config import load_config
from testforge.core.project import (
    AnalysisResult,
    save_analysis,
)
from testforge.input.parser import parse

logger = logging.getLogger(__name__)


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
    config = load_config(project_dir)

    # Parse all input documents
    from testforge.input.parser import ParsedDocument
    parsed_docs: list[ParsedDocument] = []
    for inp in inputs:
        try:
            parsed_docs.append(parse(inp))
        except Exception as exc:
            logger.warning("Failed to parse %s: %s", inp, exc)

    if not parsed_docs:
        logger.info("No documents parsed; returning empty analysis")
        return []

    # Build combined text for LLM analysis
    combined_text = _build_combined_text(parsed_docs)

    # Create LLM adapter
    from testforge.llm import create_adapter

    adapter_kwargs: dict[str, Any] = {}
    if config.llm_model:
        adapter_kwargs["model"] = config.llm_model

    try:
        adapter = create_adapter(config.llm_provider, **adapter_kwargs)
    except (ValueError, ImportError) as exc:
        logger.warning("LLM adapter unavailable (%s), using offline extraction", exc)
        return _offline_analysis(parsed_docs)

    # Run LLM-powered analysis
    try:
        analysis_result = _llm_analysis(adapter, combined_text, parsed_docs)
    except Exception as exc:
        logger.warning("LLM analysis failed (%s), falling back to offline", exc)
        return _offline_analysis(parsed_docs)

    # Persist results
    save_analysis(project_dir, analysis_result)

    # Return flat feature list for CLI compatibility
    from testforge.input.parser import ParsedDocument
    return [
        {
            "source": doc.source_path if isinstance(doc, ParsedDocument) else doc.get("source", ""),
            "type": doc.source_type if isinstance(doc, ParsedDocument) else doc.get("type", ""),
            "features": [f.name for f in analysis_result.features],
            "personas": [p.name for p in analysis_result.personas],
            "rules": [r.name for r in analysis_result.rules],
        }
        for doc in parsed_docs
    ]


def _build_combined_text(parsed_docs: list[Any]) -> str:
    """Flatten parsed documents into a single text block for LLM consumption."""
    from testforge.input.parser import ParsedDocument
    parts: list[str] = []
    for doc in parsed_docs:
        if isinstance(doc, ParsedDocument):
            source = doc.source_path
            doc_type = doc.source_type
            parts.append(f"--- Document: {source} (type: {doc_type}) ---")
            if doc.pages:
                for page in doc.pages:
                    text = page.get("text", "").strip()
                    if text:
                        parts.append(f"[Page {page.get('page', '?')}]\n{text}")
            elif doc.text:
                parts.append(doc.text)
        else:
            # legacy dict path
            source = doc.get("source", "unknown")
            doc_type = doc.get("type", "unknown")
            parts.append(f"--- Document: {source} (type: {doc_type}) ---")
            if "pages" in doc:
                for page in doc["pages"]:
                    text = page.get("text", "").strip()
                    if text:
                        parts.append(f"[Page {page.get('page', '?')}]\n{text}")
            elif "text" in doc:
                parts.append(doc["text"])
            elif "content" in doc:
                parts.append(str(doc["content"]))

    return "\n\n".join(parts)


def _llm_analysis(
    adapter: Any,
    combined_text: str,
    parsed_docs: list[Any],
) -> AnalysisResult:
    """Run full LLM-powered analysis over the combined document text."""
    from testforge.analysis.features import extract_features
    from testforge.analysis.personas import derive_personas
    from testforge.analysis.rules import extract_rules
    from testforge.core.project import Feature, Persona, BusinessRule, Screen
    from testforge.input.parser import ParsedDocument

    prompt = _build_analysis_prompt(combined_text)
    response = adapter.complete(prompt, max_tokens=4096)

    # Parse structured JSON from LLM response
    data = _parse_json_response(response.text)

    features = [
        Feature(
            id=f"F-{i+1:03d}",
            name=f.get("name", f"Feature {i+1}"),
            description=f.get("description", ""),
            category=f.get("category", ""),
            priority=f.get("priority", "medium"),
            screens=f.get("screens", []),
            tags=f.get("tags", []),
            source=f.get("source", ""),
        )
        for i, f in enumerate(data.get("features", []))
    ]

    screens = [
        Screen(
            id=f"S-{i+1:03d}",
            name=s.get("name", f"Screen {i+1}"),
            description=s.get("description", ""),
            url_pattern=s.get("url_pattern", ""),
            features=s.get("features", []),
            elements=s.get("elements", []),
        )
        for i, s in enumerate(data.get("screens", []))
    ]

    personas = [
        Persona(
            id=f"P-{i+1:03d}",
            name=p.get("name", f"Persona {i+1}"),
            description=p.get("description", ""),
            goals=p.get("goals", []),
            pain_points=p.get("pain_points", []),
            tech_level=p.get("tech_level", "intermediate"),
        )
        for i, p in enumerate(data.get("personas", []))
    ]

    rules = [
        BusinessRule(
            id=f"R-{i+1:03d}",
            name=r.get("name", f"Rule {i+1}"),
            description=r.get("description", ""),
            condition=r.get("condition", ""),
            expected_behavior=r.get("expected_behavior", ""),
            source=r.get("source", ""),
        )
        for i, r in enumerate(data.get("rules", []))
    ]

    return AnalysisResult(
        features=features,
        screens=screens,
        personas=personas,
        rules=rules,
        raw_sources=[{"source": d.source_path if isinstance(d, ParsedDocument) else d.get("source", "")} for d in parsed_docs],
    )


def _build_analysis_prompt(combined_text: str) -> str:
    """Build the analysis prompt for the LLM."""
    return f"""You are a QA analyst. Analyze the following project documentation and extract structured information.

Return ONLY a JSON object with these keys:
- "features": array of objects with keys: name, description, category, priority (high/medium/low), screens (array of screen names), tags (array)
- "screens": array of objects with keys: name, description, url_pattern, features (array of feature names), elements (array of {{name, type, description}})
- "personas": array of objects with keys: name, description, goals (array), pain_points (array), tech_level (beginner/intermediate/advanced)
- "rules": array of objects with keys: name, description, condition, expected_behavior

Be thorough but concise. Extract all testable features, user-facing screens, user personas, and business rules.

DOCUMENTATION:
{combined_text}

Respond with valid JSON only, no markdown fences."""


def _parse_json_response(text: str) -> dict[str, Any]:
    """Parse JSON from LLM response, handling common formatting issues."""
    cleaned = text.strip()

    # Strip markdown code fences if present
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except json.JSONDecodeError:
                pass

    logger.warning("Failed to parse LLM response as JSON")
    return {"features": [], "screens": [], "personas": [], "rules": []}


def _offline_analysis(parsed_docs: list[Any]) -> list[dict[str, Any]]:
    """Fallback: produce minimal analysis without LLM when adapter is unavailable."""
    from testforge.input.parser import ParsedDocument
    results: list[dict[str, Any]] = []
    for doc in parsed_docs:
        results.append({
            "source": doc.source_path if isinstance(doc, ParsedDocument) else doc.get("source", ""),
            "type": doc.source_type if isinstance(doc, ParsedDocument) else doc.get("type", ""),
            "features": [],
            "personas": [],
            "rules": [],
        })
    return results
