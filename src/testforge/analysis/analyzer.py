"""LLM-based project analyzer -- orchestrates feature, persona, and rule extraction."""

from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any

from testforge.core.config import load_config
from testforge.core.project import (
    AnalysisResult,
    save_analysis,
)
from testforge.input.parser import parse
from testforge.llm.utils import parse_llm_json

logger = logging.getLogger(__name__)


def run_analysis(
    project_dir: Path,
    inputs: list[str],
    no_llm: bool = False,
) -> list[dict[str, Any]]:
    """Analyze input files and produce a structured feature list.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.
    inputs:
        List of file paths or URLs to analyze.
    no_llm:
        When True, skip LLM entirely and use offline extraction without warnings.

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

    # Skip LLM entirely when --no-llm is set
    if no_llm:
        analysis_result = _offline_analysis(parsed_docs)
        save_analysis(project_dir, analysis_result)
        return _analysis_to_doc_summaries(analysis_result, parsed_docs)

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
        import click as _click
        _click.echo(
            "[Warning] No LLM provider configured or available. "
            "Falling back to offline extraction (no features will be derived). "
            "Set ANTHROPIC_API_KEY / OPENAI_API_KEY or use --no-llm to suppress this warning.",
            err=True,
        )
        analysis_result = _offline_analysis(parsed_docs)
        save_analysis(project_dir, analysis_result)
        return _analysis_to_doc_summaries(analysis_result, parsed_docs)

    # Run LLM-powered analysis
    try:
        analysis_result = _llm_analysis(adapter, combined_text, parsed_docs)
    except Exception as exc:
        logger.warning("LLM analysis failed (%s), falling back to offline", exc)
        import click as _click
        _click.echo(
            f"[Warning] LLM analysis failed ({exc}). Falling back to offline extraction.",
            err=True,
        )
        analysis_result = _offline_analysis(parsed_docs)
        save_analysis(project_dir, analysis_result)
        return _analysis_to_doc_summaries(analysis_result, parsed_docs)

    # Persist results
    save_analysis(project_dir, analysis_result)

    # Return flat feature list for CLI compatibility
    return _analysis_to_doc_summaries(analysis_result, parsed_docs)


def _analysis_to_doc_summaries(
    analysis_result: AnalysisResult,
    parsed_docs: list[Any],
) -> list[dict[str, Any]]:
    """Flatten an analysis result into per-document CLI summaries."""
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


def _analyze_images(adapter: Any, image_docs: list[Any]) -> dict[str, Any]:
    """Analyze images using vision model to extract UI features and screens."""
    from testforge.input.parser import ParsedDocument

    images: list[dict[str, str]] = []
    for doc in image_docs:
        if isinstance(doc, ParsedDocument) and doc.raw:
            raw = doc.raw
            b64 = raw.get("base64") or raw.get("data")
            if b64:
                images.append({
                    "base64": b64 if isinstance(b64, str) else str(b64),
                    "media_type": raw.get("media_type", "image/png"),
                })

    if not images:
        return {"features": [], "screens": []}

    prompt = """Analyze these UI screenshots/mockups. Extract:
1. "features": UI features visible (name, description, priority)
2. "screens": screens/pages shown (name, description, url_pattern guess, elements list)

For elements, include: name, type (button/input/link/text/image/nav/form), description.
Return JSON object with "features" and "screens" arrays."""

    response = adapter.complete_with_images(prompt, images, max_tokens=4096)
    return parse_llm_json(response.text, expected_type="object")


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
    data = parse_llm_json(response.text, expected_type="object")

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

    # Analyze images with vision if available
    image_docs = [
        d for d in parsed_docs
        if isinstance(d, ParsedDocument) and d.source_type == "image"
    ]
    if image_docs and hasattr(adapter, "complete_with_images"):
        try:
            image_features = _analyze_images(adapter, image_docs)
            for f in image_features.get("features", []):
                features.append(
                    Feature(
                        id=f"F-{len(features) + 1:03d}",
                        name=f.get("name", "UI Element"),
                        description=f.get("description", ""),
                        category="ui",
                        priority=f.get("priority", "medium"),
                        tags=["vision", "ui"],
                        source="image-analysis",
                    )
                )
            for s in image_features.get("screens", []):
                screens.append(
                    Screen(
                        id=f"S-{len(screens) + 1:03d}",
                        name=s.get("name", "Screen"),
                        description=s.get("description", ""),
                        url_pattern=s.get("url_pattern", ""),
                        features=s.get("features", []),
                        elements=s.get("elements", []),
                    )
                )
        except Exception as exc:
            logger.warning("Image analysis failed: %s", exc)

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



def _offline_analysis(parsed_docs: list[Any]) -> AnalysisResult:
    """Fallback: produce minimal persisted analysis without LLM."""
    from testforge.core.project import AnalysisResult, BusinessRule, Feature
    from testforge.input.parser import ParsedDocument

    features: list[Feature] = []
    rules: list[BusinessRule] = []
    raw_sources: list[dict[str, Any]] = []

    for doc in parsed_docs:
        if isinstance(doc, ParsedDocument):
            source_path = doc.source_path
            source_type = doc.source_type
            headings = doc.headings
            text = doc.text
        else:
            source_path = doc.get("source", "")
            source_type = doc.get("type", "")
            headings = doc.get("headings", [])
            text = doc.get("text", "") or doc.get("content", "")

        raw_sources.append({"source": source_path, "type": source_type})

        feature_names = _extract_offline_feature_names(headings, text, source_path)
        for name in feature_names:
            features.append(
                Feature(
                    id=f"F-{len(features) + 1:03d}",
                    name=name,
                    description=_summarize_heading_context(text, name),
                    category=source_type,
                    priority="medium",
                    tags=["offline", source_type] if source_type else ["offline"],
                    source=source_path,
                )
            )

        for rule_text in _extract_offline_rules(text):
            rules.append(
                BusinessRule(
                    id=f"R-{len(rules) + 1:03d}",
                    name=rule_text[:80],
                    description=rule_text,
                    condition="documented constraint",
                    expected_behavior=rule_text,
                    source=source_path,
                )
            )

    return AnalysisResult(
        features=features,
        rules=rules,
        raw_sources=raw_sources,
    )


def _extract_offline_feature_names(headings: list[str], text: str, source_path: str) -> list[str]:
    """Derive a small set of feature names from headings or visible text."""
    cleaned = [h.strip() for h in headings if h.strip()]
    if cleaned:
        return cleaned[:12]

    candidates: list[str] = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("-*0123456789. ").strip()
        if 4 <= len(stripped) <= 80 and not stripped.startswith(("```", "|")):
            candidates.append(stripped)
        if len(candidates) >= 5:
            break

    if candidates:
        return candidates

    return [Path(source_path).stem.replace("-", " ").replace("_", " ").strip() or "Offline feature"]


def _summarize_heading_context(text: str, heading: str) -> str:
    """Return a short description for an offline-derived feature."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for idx, line in enumerate(lines):
        if heading.lower() in line.lower():
            for follow in lines[idx + 1:]:
                if follow and not follow.startswith("#"):
                    return follow[:200]
    return f"Offline-derived feature for {heading}"


def _extract_offline_rules(text: str) -> list[str]:
    """Extract rule-like sentences from plain text using simple keyword heuristics."""
    matches: list[str] = []
    seen: set[str] = set()
    keyword_re = re.compile(r"\b(must|should|required|cannot|must not|do not|error|invalid)\b", re.IGNORECASE)
    for raw_line in text.splitlines():
        line = raw_line.strip().lstrip("-* ").strip()
        if len(line) < 12 or len(line) > 200:
            continue
        if keyword_re.search(line) and line not in seen:
            matches.append(line)
            seen.add(line)
        if len(matches) >= 10:
            break
    return matches
