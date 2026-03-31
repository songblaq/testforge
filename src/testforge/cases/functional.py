"""Functional test case generation."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from testforge.core.config import (
    append_locale_user_facing_instruction,
    effective_locale,
    load_config,
)
from testforge.core.locale_strings import s
from testforge.core.project import load_analysis
from testforge.llm.utils import parse_llm_json

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
    rule_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def generate_functional_cases(project_dir: Path, no_llm: bool = False) -> list[dict[str, Any]]:
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

    locale = effective_locale(config)

    if no_llm:
        return _generate_skeleton_cases(analysis, locale)

    # Try LLM-powered generation
    from testforge.llm import create_adapter

    adapter_kwargs: dict[str, Any] = {}
    if config.llm_model:
        adapter_kwargs["model"] = config.llm_model

    try:
        adapter = create_adapter(config.llm_provider, **adapter_kwargs)
    except (ValueError, ImportError) as exc:
        logger.warning("LLM unavailable (%s), generating skeleton cases", exc)
        return _generate_skeleton_cases(analysis, locale)

    try:
        return _llm_generate_functional(adapter, analysis, locale)
    except Exception as exc:
        logger.warning("LLM generation failed (%s), generating skeleton cases", exc)
        return _generate_skeleton_cases(analysis, locale)


def _llm_generate_functional(
    adapter: Any, analysis: Any, locale: str = "ko"
) -> list[dict[str, Any]]:
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
    prompt = append_locale_user_facing_instruction(prompt, locale)

    response = adapter.complete(prompt, max_tokens=4096)
    cases_data = parse_llm_json(response.text)

    cases: list[dict[str, Any]] = []
    for i, tc in enumerate(cases_data):
        feature_id = tc.get("feature_id", "")
        # Use LLM-provided rule_ids; fall back to auto-mapping when absent or empty
        rule_ids: list[str] = tc.get("rule_ids") or []
        if not rule_ids and analysis is not None:
            rule_ids = _map_rule_ids_for_feature(feature_id, analysis)

        case = FunctionalTestCase(
            id=tc.get("id", f"TC-F{i+1:03d}"),
            title=tc.get("title", f"Functional Test {i+1}"),
            description=tc.get("description", ""),
            feature_id=feature_id,
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
            rule_ids=rule_ids,
        )
        cases.append(case.to_dict())

    return cases


def _map_rule_ids_for_feature(feature_id: str, analysis: Any) -> list[str]:
    """Return rule IDs whose condition/description text references the feature_id or feature name.

    Falls back to returning all rule IDs when no targeted match is found so that
    skeleton cases always surface at least the full rule set for coverage tracking.
    """
    # Find the feature object
    feature_name = ""
    for f in analysis.features:
        if f.id == feature_id:
            feature_name = f.name.lower()
            break

    matched: list[str] = []
    for rule in analysis.rules:
        searchable = " ".join([
            rule.id.lower(),
            getattr(rule, "name", "").lower(),
            getattr(rule, "description", "").lower(),
            getattr(rule, "condition", "").lower(),
            getattr(rule, "expected_behavior", "").lower(),
        ])
        if feature_id.lower() in searchable or (feature_name and feature_name in searchable):
            matched.append(rule.id)

    # If no match found, return all rule IDs (better than zero coverage)
    return matched if matched else [r.id for r in analysis.rules]


def _generate_skeleton_cases(analysis: Any, locale: str = "ko") -> list[dict[str, Any]]:
    """Generate minimal skeleton test cases without LLM."""
    cases: list[dict[str, Any]] = []
    for i, feature in enumerate(analysis.features):
        rule_ids = _map_rule_ids_for_feature(feature.id, analysis)
        case = FunctionalTestCase(
            id=f"TC-F{i+1:03d}-01",
            title=s("verify_feature", locale, feature=feature.name),
            description=s("validate_feature", locale, feature=feature.name, description=feature.description),
            feature_id=feature.id,
            preconditions=[s("system_accessible", locale), s("user_authenticated", locale)],
            steps=[
                TestStep(order=1, action=s("navigate_to", locale, feature=feature.name), expected_result=s("feature_displayed", locale)),
                TestStep(order=2, action=s("perform_primary", locale), expected_result=s("expected_observed", locale)),
                TestStep(order=3, action=s("verify_result", locale), expected_result=s("result_matches", locale)),
            ],
            expected_result=s("functions_correctly", locale, feature=feature.name),
            priority=feature.priority,
            tags=["functional", "skeleton"],
            rule_ids=rule_ids,
        )
        cases.append(case.to_dict())
    return cases
