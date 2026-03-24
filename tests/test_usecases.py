"""Tests for use case scenario generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from testforge.cases.usecases import (
    UseCaseScenario,
    _generate_skeleton_usecases,
    _llm_generate_usecases,
    _parse_json_array,
    generate_usecase_tests,
)
from testforge.core.project import (
    AnalysisResult,
    Feature,
    Persona,
    save_analysis,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_analysis(
    features: list[Feature] | None = None,
    personas: list[Persona] | None = None,
) -> AnalysisResult:
    return AnalysisResult(
        features=features
        or [
            Feature(id="F-001", name="Login", description="User login flow"),
            Feature(id="F-002", name="Dashboard", description="Main dashboard"),
        ],
        personas=personas
        or [
            Persona(id="P-001", name="Admin", description="System administrator"),
        ],
    )


def _make_adapter(response_text: str) -> MagicMock:
    from testforge.llm.adapter import LLMResponse

    adapter = MagicMock()
    adapter.complete.return_value = LLMResponse(text=response_text)
    return adapter


# ---------------------------------------------------------------------------
# Unit tests: UseCaseScenario dataclass
# ---------------------------------------------------------------------------


def test_usecase_scenario_to_dict() -> None:
    uc = UseCaseScenario(
        id="UC-001",
        title="Admin login",
        description="Admin logs in",
        persona_id="P-001",
        persona_name="Admin",
        preconditions=["System running"],
        scenario_steps=["Open browser", "Enter credentials"],
        expected_outcome="Dashboard shown",
        features_covered=["F-001"],
        priority="high",
        tags=["e2e"],
    )
    d = uc.to_dict()
    assert d["id"] == "UC-001"
    assert d["persona_id"] == "P-001"
    assert d["tags"] == ["e2e"]
    assert d["features_covered"] == ["F-001"]


# ---------------------------------------------------------------------------
# Unit tests: _parse_json_array
# ---------------------------------------------------------------------------


def test_parse_json_array_plain() -> None:
    data = [{"id": "UC-001", "title": "test"}]
    result = _parse_json_array(json.dumps(data))
    assert result == data


def test_parse_json_array_with_backticks() -> None:
    raw = "```json\n[{\"id\": \"UC-001\"}]\n```"
    result = _parse_json_array(raw)
    assert result[0]["id"] == "UC-001"


def test_parse_json_array_embedded() -> None:
    raw = "Here is the result:\n[{\"id\": \"UC-002\"}]\nEnd."
    result = _parse_json_array(raw)
    assert result[0]["id"] == "UC-002"


def test_parse_json_array_invalid_returns_empty() -> None:
    result = _parse_json_array("this is not json")
    assert result == []


# ---------------------------------------------------------------------------
# Unit tests: _generate_skeleton_usecases
# ---------------------------------------------------------------------------


def test_skeleton_usecases_one_per_persona() -> None:
    analysis = _make_analysis(
        personas=[
            Persona(id="P-001", name="Admin", description="Admin user"),
            Persona(id="P-002", name="Guest", description="Guest user"),
        ]
    )
    results = _generate_skeleton_usecases(analysis)
    assert len(results) == 2
    persona_ids = [r["persona_id"] for r in results]
    assert "P-001" in persona_ids
    assert "P-002" in persona_ids


def test_skeleton_usecases_no_personas_uses_default() -> None:
    analysis = AnalysisResult(
        features=[Feature(id="F-001", name="Login", description="Login")],
        personas=[],
    )
    results = _generate_skeleton_usecases(analysis)
    assert len(results) == 1
    assert results[0]["persona_name"] == "Default User"


def test_skeleton_usecases_fields_present() -> None:
    analysis = _make_analysis()
    result = _generate_skeleton_usecases(analysis)[0]
    assert "id" in result
    assert "title" in result
    assert "scenario_steps" in result
    assert "features_covered" in result
    assert len(result["scenario_steps"]) > 0


# ---------------------------------------------------------------------------
# Unit tests: _llm_generate_usecases
# ---------------------------------------------------------------------------


def test_llm_generate_usecases_parses_response() -> None:
    scenarios = [
        {
            "id": "UC-001",
            "title": "Admin happy path",
            "description": "Admin completes main workflow",
            "persona_id": "P-001",
            "persona_name": "Admin",
            "preconditions": ["Logged out"],
            "scenario_steps": ["Login", "View dashboard"],
            "expected_outcome": "Dashboard visible",
            "features_covered": ["F-001", "F-002"],
            "priority": "high",
            "tags": ["e2e", "critical-path"],
        }
    ]
    adapter = _make_adapter(json.dumps(scenarios))
    analysis = _make_analysis()
    results = _llm_generate_usecases(adapter, analysis)
    assert len(results) == 1
    assert results[0]["id"] == "UC-001"
    assert results[0]["tags"] == ["e2e", "critical-path"]


def test_llm_generate_usecases_falls_back_on_empty_json() -> None:
    adapter = _make_adapter("[]")
    analysis = _make_analysis()
    results = _llm_generate_usecases(adapter, analysis)
    assert results == []


def test_llm_generate_usecases_handles_missing_fields() -> None:
    scenarios = [{"id": "UC-001", "title": "Minimal"}]
    adapter = _make_adapter(json.dumps(scenarios))
    results = _llm_generate_usecases(adapter, _make_analysis())
    assert results[0]["id"] == "UC-001"
    assert results[0]["priority"] == "medium"
    assert results[0]["tags"] == []


# ---------------------------------------------------------------------------
# Integration: generate_usecase_tests (with mocked LLM)
# ---------------------------------------------------------------------------


def test_generate_usecase_tests_no_analysis(tmp_project: Path) -> None:
    """Returns empty list when no analysis exists."""
    result = generate_usecase_tests(tmp_project)
    assert result == []


def test_generate_usecase_tests_with_analysis_skeleton(tmp_project: Path) -> None:
    """Falls back to skeleton when LLM is unavailable."""
    analysis = _make_analysis()
    save_analysis(tmp_project, analysis)

    with patch("testforge.cases.usecases.create_adapter", side_effect=ValueError("no llm")):
        results = generate_usecase_tests(tmp_project)

    assert len(results) >= 1
    assert all("id" in r for r in results)


def test_generate_usecase_tests_with_llm(tmp_project: Path) -> None:
    """Uses LLM adapter when available."""
    analysis = _make_analysis()
    save_analysis(tmp_project, analysis)

    llm_scenarios = [
        {
            "id": "UC-001",
            "title": "Admin workflow",
            "description": "Full admin journey",
            "persona_id": "P-001",
            "persona_name": "Admin",
            "preconditions": [],
            "scenario_steps": ["Step 1", "Step 2"],
            "expected_outcome": "Success",
            "features_covered": ["F-001"],
            "priority": "high",
            "tags": ["e2e"],
        }
    ]

    from testforge.llm.adapter import LLMResponse

    mock_adapter = MagicMock()
    mock_adapter.complete.return_value = LLMResponse(text=json.dumps(llm_scenarios))

    with patch("testforge.cases.usecases.create_adapter", return_value=mock_adapter):
        results = generate_usecase_tests(tmp_project)

    assert len(results) == 1
    assert results[0]["id"] == "UC-001"


def test_generate_usecase_tests_llm_failure_falls_back(tmp_project: Path) -> None:
    """Falls back to skeleton when LLM call raises."""
    analysis = _make_analysis()
    save_analysis(tmp_project, analysis)

    mock_adapter = MagicMock()
    mock_adapter.complete.side_effect = RuntimeError("connection error")

    with patch("testforge.cases.usecases.create_adapter", return_value=mock_adapter):
        results = generate_usecase_tests(tmp_project)

    assert len(results) >= 1
    assert all("tags" in r for r in results)
