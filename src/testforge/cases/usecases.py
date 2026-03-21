"""Use case scenario test generation."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from testforge.core.config import load_config
from testforge.core.project import load_analysis
from testforge.llm import create_adapter

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
        return asdict(self)


def generate_usecase_tests(project_dir: Path) -> list[dict[str, Any]]:
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

    adapter_kwargs: dict[str, Any] = {}
    if config.llm_model:
        adapter_kwargs["model"] = config.llm_model

    try:
        adapter = create_adapter(config.llm_provider, **adapter_kwargs)
    except (ValueError, ImportError) as exc:
        logger.warning("LLM unavailable (%s), generating skeleton use cases", exc)
        return _generate_skeleton_usecases(analysis)

    try:
        return _llm_generate_usecases(adapter, analysis)
    except Exception as exc:
        logger.warning("LLM generation failed (%s), generating skeleton use cases", exc)
        return _generate_skeleton_usecases(analysis)


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
    scenarios_data = _parse_json_array(response.text)

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
