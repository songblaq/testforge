"""Use case scenario test generation."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from testforge.core.config import load_config
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

    if no_llm:
        results = _generate_skeleton_usecases(analysis)
        results.extend(_generate_crud_usecases(analysis))
        return results

    adapter_kwargs: dict[str, Any] = {}
    if config.llm_model:
        adapter_kwargs["model"] = config.llm_model

    try:
        adapter = create_adapter(config.llm_provider, **adapter_kwargs)
    except (ValueError, ImportError) as exc:
        logger.warning("LLM unavailable (%s), generating skeleton use cases", exc)
        results = _generate_skeleton_usecases(analysis)
        results.extend(_generate_crud_usecases(analysis))
        return results

    try:
        return _llm_generate_usecases(adapter, analysis)
    except Exception as exc:
        logger.warning("LLM generation failed (%s), generating skeleton use cases", exc)
        results = _generate_skeleton_usecases(analysis)
        results.extend(_generate_crud_usecases(analysis))
        return results


def _llm_generate_usecases(adapter: Any, analysis: Any) -> list[dict[str, Any]]:
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


def _generate_crud_usecases(analysis: Any) -> list[dict[str, Any]]:
    """Generate CRUD flow use cases for each feature — design-phase validation."""
    crud_cases = []
    crud_patterns = [
        {
            "suffix": "list-view",
            "title_template": "View {feature} list",
            "steps": [
                "Navigate to {feature} section",
                "Verify list/table is displayed with items",
                "Verify each item shows key information (ID, name, status)",
                "Verify empty state message when no items exist",
            ],
            "expected": "List displays all items with sufficient information to identify each one",
            "tags": ["crud", "list", "design-phase"],
        },
        {
            "suffix": "detail-view",
            "title_template": "View {feature} detail",
            "steps": [
                "Navigate to {feature} list",
                "Click on a specific item",
                "Verify detail view shows ALL fields (not just summary)",
                "Verify user can see full description, attributes, metadata",
                "Verify back/close navigation to return to list",
            ],
            "expected": "Detail view shows complete information about the selected item",
            "tags": ["crud", "detail", "design-phase"],
        },
        {
            "suffix": "edit-flow",
            "title_template": "Edit {feature} item",
            "steps": [
                "Navigate to {feature} detail view",
                "Click edit button or inline edit field",
                "Modify one or more fields",
                "Save changes",
                "Verify updated data is reflected in list and detail views",
            ],
            "expected": "User can modify item data and changes persist",
            "tags": ["crud", "edit", "design-phase"],
        },
        {
            "suffix": "delete-flow",
            "title_template": "Delete {feature} item",
            "steps": [
                "Navigate to {feature} list or detail view",
                "Click delete button",
                "Confirm deletion in dialog",
                "Verify item is removed from list",
                "Verify proper feedback (toast or message)",
            ],
            "expected": "Item is deleted with confirmation step and user feedback",
            "tags": ["crud", "delete", "design-phase"],
        },
    ]

    for i, feature in enumerate(analysis.features):
        for pattern in crud_patterns:
            case_id = f"UC-CRUD-{i+1:03d}-{pattern['suffix']}"
            crud_cases.append({
                "id": case_id,
                "title": pattern["title_template"].format(feature=feature.name),
                "description": f"CRUD flow validation for {feature.name}",
                "persona_id": analysis.personas[0].id if analysis.personas else "",
                "persona_name": analysis.personas[0].name if analysis.personas else "Default User",
                "preconditions": [f"{feature.name} has existing data"],
                "scenario_steps": [s.format(feature=feature.name) for s in pattern["steps"]],
                "steps": [
                    {
                        "order": i + 1,
                        "action": s.format(feature=feature.name),
                        "expected_result": "",
                        "input_data": "",
                    }
                    for i, s in enumerate(pattern["steps"])
                ],
                "expected_outcome": pattern["expected"],
                "features_covered": [feature.id],
                "priority": "high",
                "tags": pattern["tags"],
            })

    return crud_cases


def _generate_skeleton_usecases(analysis: Any) -> list[dict[str, Any]]:
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
            title=f"{persona.name} -- primary workflow",
            description=f"End-to-end scenario for {persona.name}",
            persona_id=persona.id,
            persona_name=persona.name,
            preconditions=["User is authenticated", "System is in default state"],
            scenario_steps=[
                f"As {persona.name}, navigate to the application",
                *[f"Interact with {fn}" for fn in feature_names],
                "Verify final state matches expectations",
            ],
            expected_outcome="All interactions complete successfully",
            features_covered=[f.id for f in analysis.features[:3]],
            priority="medium",
            tags=["e2e", "skeleton"],
        )
        scenarios.append(uc.to_dict())

    return scenarios
