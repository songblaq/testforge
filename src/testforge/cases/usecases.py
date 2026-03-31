"""Use case scenario test generation."""

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
from testforge.llm import create_adapter
from testforge.llm.utils import parse_llm_json


def _parse_json_array(text: str) -> list:
    """Backward-compatible shim; delegates to parse_llm_json."""
    return parse_llm_json(text)

logger = logging.getLogger(__name__)


@dataclass
class UseCaseScenario:
    """A use case test scenario based on a persona interacting with features."""

    id: str
    title: str
    description: str
    persona_id: str = ""
    persona_name: str = ""
    preconditions: list[str] = field(default_factory=list)
    scenario_steps: list[str] = field(default_factory=list)
    expected_outcome: str = ""
    features_covered: list[str] = field(default_factory=list)
    priority: str = "medium"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Normalized steps for script generator compatibility
        d["steps"] = [
            {"order": i + 1, "action": step, "expected_result": "", "input_data": ""}
            for i, step in enumerate(self.scenario_steps)
        ]
        return d


def generate_usecase_tests(project_dir: Path, no_llm: bool = False) -> list[dict[str, Any]]:
    """Generate use case test scenarios from personas and features.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.

    Returns
    -------
    list[dict]:
        Use case test scenario definitions.
    """
    config = load_config(project_dir)
    analysis = load_analysis(project_dir)

    if analysis is None or not analysis.features:
        logger.info("No analysis results; skipping use case generation")
        return []

    locale = effective_locale(config)

    if no_llm:
        results = _generate_skeleton_usecases(analysis, locale)
        results.extend(_generate_crud_usecases(analysis, locale))
        return results

    adapter_kwargs: dict[str, Any] = {}
    if config.llm_model:
        adapter_kwargs["model"] = config.llm_model

    try:
        adapter = create_adapter(config.llm_provider, **adapter_kwargs)
    except (ValueError, ImportError) as exc:
        logger.warning("LLM unavailable (%s), generating skeleton use cases", exc)
        results = _generate_skeleton_usecases(analysis, locale)
        results.extend(_generate_crud_usecases(analysis, locale))
        return results

    try:
        return _llm_generate_usecases(adapter, analysis, locale)
    except Exception as exc:
        logger.warning("LLM generation failed (%s), generating skeleton use cases", exc)
        results = _generate_skeleton_usecases(analysis, locale)
        results.extend(_generate_crud_usecases(analysis, locale))
        return results


def _llm_generate_usecases(
    adapter: Any, analysis: Any, locale: str = "ko"
) -> list[dict[str, Any]]:
    """Use LLM to generate use case scenarios from personas and features."""
    features_text = "\n".join(
        f"- {f.id}: {f.name} -- {f.description}" for f in analysis.features
    )

    personas_text = "\n".join(
        f"- {p.id}: {p.name} (tech: {p.tech_level}) -- {p.description}"
        for p in analysis.personas
    ) or "- Default User: a typical end user of the system"

    prompt = f"""You are a QA engineer creating use case test scenarios.

FEATURES:
{features_text}

PERSONAS:
{personas_text}

Generate realistic end-to-end use case scenarios. Each persona should have at least one scenario.
Each scenario should cover a realistic user journey through multiple features.

Also include CRUD flow scenarios for each feature:
- List view: Can the user see a list of items with sufficient detail?
- Detail view: Can the user click an item and see ALL its information?
- Edit flow: Can the user modify item data?
- Delete flow: Can the user delete an item with confirmation?
Tag these scenarios with "crud" and "design-phase".

Return a JSON array where each element has:
- "id": unique ID (e.g. "UC-001")
- "title": descriptive scenario title
- "description": what this scenario tests end-to-end
- "persona_id": the persona ID
- "persona_name": the persona name
- "preconditions": array of starting conditions
- "scenario_steps": array of step descriptions (user actions in narrative form)
- "expected_outcome": the desired end state
- "features_covered": array of feature IDs tested in this scenario
- "priority": "high", "medium", or "low"
- "tags": array of tags (e.g. "e2e", "happy-path", "critical-path")

Return a JSON array only."""
    prompt = append_locale_user_facing_instruction(prompt, locale)

    response = adapter.complete(prompt, max_tokens=4096)
    scenarios_data = parse_llm_json(response.text)

    scenarios: list[dict[str, Any]] = []
    for i, sc in enumerate(scenarios_data):
        uc = UseCaseScenario(
            id=sc.get("id", f"UC-{i+1:03d}"),
            title=sc.get("title", f"Use Case {i+1}"),
            description=sc.get("description", ""),
            persona_id=sc.get("persona_id", ""),
            persona_name=sc.get("persona_name", ""),
            preconditions=sc.get("preconditions", []),
            scenario_steps=sc.get("scenario_steps", []),
            expected_outcome=sc.get("expected_outcome", ""),
            features_covered=sc.get("features_covered", []),
            priority=sc.get("priority", "medium"),
            tags=sc.get("tags", []),
        )
        scenarios.append(uc.to_dict())

    return scenarios


def _generate_crud_usecases(analysis: Any, locale: str = "ko") -> list[dict[str, Any]]:
    """Generate CRUD flow use cases for each feature — design-phase validation."""
    crud_cases = []

    def _crud_patterns(feature_name: str) -> list[dict[str, Any]]:
        return [
            {
                "suffix": "list-view",
                "title": s("view_list", locale, feature=feature_name),
                "steps": [
                    s("navigate_section", locale, feature=feature_name),
                    s("list_displayed", locale),
                    s("item_shows_info", locale),
                ],
                "expected": s("list_displayed", locale),
                "tags": ["crud", "list", "design-phase"],
            },
            {
                "suffix": "detail-view",
                "title": s("view_detail", locale, feature=feature_name),
                "steps": [
                    s("navigate_section", locale, feature=feature_name),
                    s("select_item", locale),
                    s("detail_shows_all", locale),
                    s("back_navigation", locale),
                ],
                "expected": s("detail_shows_all", locale),
                "tags": ["crud", "detail", "design-phase"],
            },
            {
                "suffix": "edit-flow",
                "title": s("edit_item", locale, feature=feature_name),
                "steps": [
                    s("navigate_section", locale, feature=feature_name),
                    s("click_edit", locale),
                    s("modify_fields", locale),
                    s("save_changes", locale),
                    s("updated_reflected", locale),
                ],
                "expected": s("updated_reflected", locale),
                "tags": ["crud", "edit", "design-phase"],
            },
            {
                "suffix": "delete-flow",
                "title": s("delete_item", locale, feature=feature_name),
                "steps": [
                    s("navigate_section", locale, feature=feature_name),
                    s("click_delete", locale),
                    s("confirm_delete", locale),
                    s("item_removed", locale),
                ],
                "expected": s("item_removed", locale),
                "tags": ["crud", "delete", "design-phase"],
            },
        ]

    for i, feature in enumerate(analysis.features):
        for pattern in _crud_patterns(feature.name):
            case_id = f"UC-CRUD-{i+1:03d}-{pattern['suffix']}"
            steps_list = pattern["steps"]
            crud_cases.append({
                "id": case_id,
                "title": pattern["title"],
                "description": s("uc_crud_validation", locale, feature=feature.name),
                "persona_id": analysis.personas[0].id if analysis.personas else "",
                "persona_name": analysis.personas[0].name if analysis.personas else "Default User",
                "preconditions": [s("has_existing_data", locale, feature=feature.name)],
                "scenario_steps": steps_list,
                "steps": [
                    {
                        "order": j + 1,
                        "action": step,
                        "expected_result": "",
                        "input_data": "",
                    }
                    for j, step in enumerate(steps_list)
                ],
                "expected_outcome": pattern["expected"],
                "features_covered": [feature.id],
                "priority": "high",
                "tags": pattern["tags"],
            })

    return crud_cases


def _generate_skeleton_usecases(analysis: Any, locale: str = "ko") -> list[dict[str, Any]]:
    """Generate minimal skeleton use case scenarios without LLM."""
    scenarios: list[dict[str, Any]] = []

    # Use personas if available, otherwise create a default
    personas = analysis.personas
    if not personas:
        from testforge.core.project import Persona

        personas = [
            Persona(
                id="P-DEFAULT",
                name="Default User",
                description="A typical end user",
            )
        ]

    for i, persona in enumerate(personas):
        feature_names = [f.name for f in analysis.features[:3]]
        uc = UseCaseScenario(
            id=f"UC-{i+1:03d}",
            title=s("uc_primary_workflow", locale, persona=persona.name),
            description=s("uc_e2e_scenario", locale, persona=persona.name),
            persona_id=persona.id,
            persona_name=persona.name,
            preconditions=[s("user_authenticated", locale), s("default_state", locale)],
            scenario_steps=[
                s("uc_navigate_app", locale, persona=persona.name),
                *[s("uc_interact_feature", locale, feature=fn) for fn in feature_names],
                s("uc_verify_final", locale),
            ],
            expected_outcome=s("uc_all_success", locale),
            features_covered=[f.id for f in analysis.features[:3]],
            priority="medium",
            tags=["e2e", "skeleton"],
        )
        scenarios.append(uc.to_dict())

    return scenarios
