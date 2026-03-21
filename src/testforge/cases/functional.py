"""Functional test case generation."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from testforge.core.config import load_config
from testforge.core.project import load_analysis

logger = logging.getLogger(__name__)


@dataclass
class TestStep:
    """A single step in a functional test case."""

    order: int
    action: str
    expected_result: str
    input_data: str = ""


@dataclass
class FunctionalTestCase:
    """A functional test case derived from a feature."""

    id: str
    title: str
    description: str
    feature_id: str = ""
    preconditions: list[str] = field(default_factory=list)
    steps: list[TestStep] = field(default_factory=list)
    expected_result: str = ""
    priority: str = "medium"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def generate_functional_cases(project_dir: Path) -> list[dict[str, Any]]:
    """Generate functional test cases from analysis results.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.

    Returns
    -------
    list[dict]:
        Functional test case definitions.
    """
    config = load_config(project_dir)
    analysis = load_analysis(project_dir)

    if analysis is None or not analysis.features:
        logger.info("No analysis results found; skipping functional case generation")
        return []

    # Try LLM-powered generation
    from testforge.llm import create_adapter

    adapter_kwargs: dict[str, Any] = {}
    if config.llm_model:
        adapter_kwargs["model"] = config.llm_model

    try:
        adapter = create_adapter(config.llm_provider, **adapter_kwargs)
    except (ValueError, ImportError) as exc:
        logger.warning("LLM unavailable (%s), generating skeleton cases", exc)
        return _generate_skeleton_cases(analysis)

    try:
        return _llm_generate_functional(adapter, analysis)
    except Exception as exc:
        logger.warning("LLM generation failed (%s), generating skeleton cases", exc)
        return _generate_skeleton_cases(analysis)


def _llm_generate_functional(adapter: Any, analysis: Any) -> list[dict[str, Any]]:
    """Use LLM to generate detailed functional test cases."""
    features_text = "\n".join(
        f"- {f.id}: {f.name} -- {f.description} (priority: {f.priority})"
        for f in analysis.features
    )

    rules_text = "\n".join(
        f"- {r.id}: {r.name} -- {r.condition} -> {r.expected_behavior}"
        for r in analysis.rules
    ) or "No specific business rules extracted."

    prompt = f"""You are a QA test engineer. Generate functional test cases for the following features.

FEATURES:
{features_text}

BUSINESS RULES:
{rules_text}

For each feature, generate 2-4 test cases. Each test case should have:
- "id": unique test case ID (e.g. "TC-F001-01")
- "title": descriptive test title
- "description": what this test validates
- "feature_id": the feature ID being tested
- "preconditions": array of required preconditions
- "steps": array of {{ "order": number, "action": string, "expected_result": string, "input_data": string }}
- "expected_result": overall expected outcome
- "priority": "high", "medium", or "low"
- "tags": array of tags (e.g. "smoke", "regression", "negative")

Include positive, negative, and edge case tests. Return a JSON array only."""

    response = adapter.complete(prompt, max_tokens=4096)
    cases_data = _parse_json_array(response.text)

    cases: list[dict[str, Any]] = []
    for i, tc in enumerate(cases_data):
        case = FunctionalTestCase(
            id=tc.get("id", f"TC-F{i+1:03d}"),
            title=tc.get("title", f"Functional Test {i+1}"),
            description=tc.get("description", ""),
            feature_id=tc.get("feature_id", ""),
            preconditions=tc.get("preconditions", []),
            steps=[
                TestStep(
                    order=s.get("order", j + 1),
                    action=s.get("action", ""),
                    expected_result=s.get("expected_result", ""),
                    input_data=s.get("input_data", ""),
                )
                for j, s in enumerate(tc.get("steps", []))
            ],
            expected_result=tc.get("expected_result", ""),
            priority=tc.get("priority", "medium"),
            tags=tc.get("tags", []),
        )
        cases.append(case.to_dict())

    return cases


def _generate_skeleton_cases(analysis: Any) -> list[dict[str, Any]]:
    """Generate minimal skeleton test cases without LLM."""
    cases: list[dict[str, Any]] = []
    for i, feature in enumerate(analysis.features):
        case = FunctionalTestCase(
            id=f"TC-F{i+1:03d}-01",
            title=f"Verify {feature.name}",
            description=f"Validate that {feature.name} works as described: {feature.description}",
            feature_id=feature.id,
            preconditions=["System is accessible", "User is authenticated"],
            steps=[
                TestStep(order=1, action=f"Navigate to {feature.name} feature", expected_result="Feature is displayed"),
                TestStep(order=2, action="Perform primary action", expected_result="Expected behavior observed"),
                TestStep(order=3, action="Verify result", expected_result="Result matches specification"),
            ],
            expected_result=f"{feature.name} functions correctly as specified",
            priority=feature.priority,
            tags=["functional", "skeleton"],
        )
        cases.append(case.to_dict())
    return cases


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
    except json.JSONDecodeError:
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except json.JSONDecodeError:
                pass

    return []
