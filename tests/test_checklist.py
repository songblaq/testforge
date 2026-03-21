"""Tests for manual test checklist generation and session workflow."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from testforge.cases.checklist import (
    ChecklistItem,
    ChecklistSession,
    _generate_skeleton_checklist,
    _llm_generate_checklist,
    _parse_json_array,
    check_item,
    finish_session,
    generate_checklist,
    session_progress,
    start_session,
)
from testforge.core.project import (
    AnalysisResult,
    BusinessRule,
    Feature,
    save_analysis,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_analysis(n_features: int = 2) -> AnalysisResult:
    features = [
        Feature(id=f"F-{i:03d}", name=f"Feature {i}", description=f"Desc {i}", priority="medium")
        for i in range(1, n_features + 1)
    ]
    rules = [BusinessRule(id="R-001", name="Rule 1", description="A business rule")]
    return AnalysisResult(features=features, rules=rules)


def _make_adapter(response_text: str) -> MagicMock:
    from testforge.llm.adapter import LLMResponse

    adapter = MagicMock()
    adapter.complete.return_value = LLMResponse(text=response_text)
    return adapter


def _seed_analysis(project_dir: Path, n_features: int = 2) -> AnalysisResult:
    analysis = _make_analysis(n_features)
    save_analysis(project_dir, analysis)
    return analysis


# ---------------------------------------------------------------------------
# Unit: ChecklistItem
# ---------------------------------------------------------------------------


def test_checklist_item_to_dict() -> None:
    item = ChecklistItem(
        id="CL-001",
        title="Check login UI",
        description="Verify login form",
        category="UI",
        feature_id="F-001",
        check_steps=["Open page", "Check button"],
        pass_criteria="Button visible",
        priority="high",
    )
    d = item.to_dict()
    assert d["id"] == "CL-001"
    assert d["category"] == "UI"
    assert d["check_steps"] == ["Open page", "Check button"]


# ---------------------------------------------------------------------------
# Unit: _parse_json_array
# ---------------------------------------------------------------------------


def test_parse_json_array_valid() -> None:
    data = [{"id": "CL-001"}]
    assert _parse_json_array(json.dumps(data)) == data


def test_parse_json_array_backtick_fenced() -> None:
    raw = "```json\n[{\"id\": \"CL-002\"}]\n```"
    result = _parse_json_array(raw)
    assert result[0]["id"] == "CL-002"


def test_parse_json_array_invalid() -> None:
    assert _parse_json_array("not json at all") == []


# ---------------------------------------------------------------------------
# Unit: _generate_skeleton_checklist
# ---------------------------------------------------------------------------


def test_skeleton_checklist_one_per_feature() -> None:
    analysis = _make_analysis(n_features=3)
    items = _generate_skeleton_checklist(analysis)
    assert len(items) == 3


def test_skeleton_checklist_fields() -> None:
    analysis = _make_analysis(n_features=1)
    item = _generate_skeleton_checklist(analysis)[0]
    assert item["id"] == "CL-001"
    assert item["feature_id"] == "F-001"
    assert len(item["check_steps"]) > 0
    assert item["pass_criteria"]


# ---------------------------------------------------------------------------
# Unit: _llm_generate_checklist
# ---------------------------------------------------------------------------


def test_llm_generate_checklist_parses_response() -> None:
    cl_items = [
        {
            "id": "CL-001",
            "title": "Login button visible",
            "description": "Check that login button is rendered",
            "category": "UI",
            "feature_id": "F-001",
            "check_steps": ["Open URL", "Locate button"],
            "pass_criteria": "Button has text Login",
            "priority": "high",
        }
    ]
    adapter = _make_adapter(json.dumps(cl_items))
    analysis = _make_analysis()
    results = _llm_generate_checklist(adapter, analysis)
    assert len(results) == 1
    assert results[0]["id"] == "CL-001"
    assert results[0]["category"] == "UI"


def test_llm_generate_checklist_handles_missing_fields() -> None:
    items = [{"id": "CL-001", "title": "Minimal"}]
    adapter = _make_adapter(json.dumps(items))
    result = _llm_generate_checklist(adapter, _make_analysis())[0]
    assert result["priority"] == "medium"
    assert result["check_steps"] == []


# ---------------------------------------------------------------------------
# Integration: generate_checklist
# ---------------------------------------------------------------------------


def test_generate_checklist_no_analysis(tmp_project: Path) -> None:
    result = generate_checklist(tmp_project)
    assert result == []


def test_generate_checklist_skeleton_fallback(tmp_project: Path) -> None:
    _seed_analysis(tmp_project, n_features=2)
    with patch("testforge.cases.checklist.create_adapter", side_effect=ValueError("no llm")):
        items = generate_checklist(tmp_project)
    assert len(items) == 2


def test_generate_checklist_with_llm(tmp_project: Path) -> None:
    _seed_analysis(tmp_project)
    cl_items = [
        {
            "id": "CL-001",
            "title": "T",
            "description": "D",
            "category": "UI",
            "feature_id": "F-001",
            "check_steps": [],
            "pass_criteria": "P",
            "priority": "medium",
        }
    ]
    from testforge.llm.adapter import LLMResponse

    mock_adapter = MagicMock()
    mock_adapter.complete.return_value = LLMResponse(text=json.dumps(cl_items))

    with patch("testforge.cases.checklist.create_adapter", return_value=mock_adapter):
        items = generate_checklist(tmp_project)

    assert items[0]["id"] == "CL-001"


def test_generate_checklist_llm_error_falls_back(tmp_project: Path) -> None:
    _seed_analysis(tmp_project, n_features=1)
    mock_adapter = MagicMock()
    mock_adapter.complete.side_effect = RuntimeError("timeout")

    with patch("testforge.cases.checklist.create_adapter", return_value=mock_adapter):
        items = generate_checklist(tmp_project)

    assert len(items) == 1


# ---------------------------------------------------------------------------
# Session workflow: start_session
# ---------------------------------------------------------------------------


def test_start_session_creates_active_file(tmp_project: Path) -> None:
    _seed_analysis(tmp_project)
    with patch("testforge.cases.checklist.create_adapter", side_effect=ValueError("no llm")):
        session = start_session(tmp_project)

    active = tmp_project / ".testforge" / "manual" / "active-session.json"
    assert active.exists()
    assert session.session_id
    assert len(session.items) > 0


def test_start_session_has_no_results_yet(tmp_project: Path) -> None:
    _seed_analysis(tmp_project)
    with patch("testforge.cases.checklist.create_adapter", side_effect=ValueError("no llm")):
        session = start_session(tmp_project)
    assert session.results == {}


# ---------------------------------------------------------------------------
# Session workflow: check_item
# ---------------------------------------------------------------------------


def test_check_item_records_pass(tmp_project: Path) -> None:
    _seed_analysis(tmp_project)
    with patch("testforge.cases.checklist.create_adapter", side_effect=ValueError("no llm")):
        session = start_session(tmp_project)

    item_id = session.items[0]["id"]
    updated = check_item(tmp_project, item_id, "pass", note="Looks good")
    assert updated.results[item_id]["status"] == "pass"
    assert updated.results[item_id]["note"] == "Looks good"


def test_check_item_records_fail(tmp_project: Path) -> None:
    _seed_analysis(tmp_project)
    with patch("testforge.cases.checklist.create_adapter", side_effect=ValueError("no llm")):
        session = start_session(tmp_project)

    item_id = session.items[0]["id"]
    updated = check_item(tmp_project, item_id, "fail", note="Broken")
    assert updated.results[item_id]["status"] == "fail"


def test_check_item_no_session_raises(tmp_project: Path) -> None:
    with pytest.raises(FileNotFoundError):
        check_item(tmp_project, "CL-001", "pass")


def test_check_item_persists_to_disk(tmp_project: Path) -> None:
    _seed_analysis(tmp_project)
    with patch("testforge.cases.checklist.create_adapter", side_effect=ValueError("no llm")):
        session = start_session(tmp_project)

    item_id = session.items[0]["id"]
    check_item(tmp_project, item_id, "pass")

    active = tmp_project / ".testforge" / "manual" / "active-session.json"
    data = json.loads(active.read_text())
    assert item_id in data["results"]


# ---------------------------------------------------------------------------
# Session workflow: session_progress
# ---------------------------------------------------------------------------


def test_session_progress_initial(tmp_project: Path) -> None:
    _seed_analysis(tmp_project, n_features=2)
    with patch("testforge.cases.checklist.create_adapter", side_effect=ValueError("no llm")):
        session = start_session(tmp_project)

    prog = session_progress(tmp_project)
    assert prog["total"] == len(session.items)
    assert prog["checked"] == 0
    assert prog["pending"] == prog["total"]
    assert prog["percent"] == 0


def test_session_progress_after_checks(tmp_project: Path) -> None:
    _seed_analysis(tmp_project, n_features=2)
    with patch("testforge.cases.checklist.create_adapter", side_effect=ValueError("no llm")):
        session = start_session(tmp_project)

    ids = [item["id"] for item in session.items]
    check_item(tmp_project, ids[0], "pass")
    if len(ids) > 1:
        check_item(tmp_project, ids[1], "fail")

    prog = session_progress(tmp_project)
    assert prog["checked"] == min(2, len(ids))
    assert prog["passed"] >= 1


def test_session_progress_no_session_raises(tmp_project: Path) -> None:
    with pytest.raises(FileNotFoundError):
        session_progress(tmp_project)


# ---------------------------------------------------------------------------
# Session workflow: finish_session
# ---------------------------------------------------------------------------


def test_finish_session_writes_report(tmp_project: Path) -> None:
    _seed_analysis(tmp_project)
    with patch("testforge.cases.checklist.create_adapter", side_effect=ValueError("no llm")):
        session = start_session(tmp_project)

    item_id = session.items[0]["id"]
    check_item(tmp_project, item_id, "pass")

    report_path = finish_session(tmp_project)
    assert report_path.exists()
    data = json.loads(report_path.read_text())
    assert data["session_id"] == session.session_id
    assert data["finished_at"]


def test_finish_session_removes_active(tmp_project: Path) -> None:
    _seed_analysis(tmp_project)
    with patch("testforge.cases.checklist.create_adapter", side_effect=ValueError("no llm")):
        start_session(tmp_project)

    finish_session(tmp_project)
    active = tmp_project / ".testforge" / "manual" / "active-session.json"
    assert not active.exists()


def test_finish_session_no_session_raises(tmp_project: Path) -> None:
    with pytest.raises(FileNotFoundError):
        finish_session(tmp_project)


def test_finish_session_report_contains_results(tmp_project: Path) -> None:
    _seed_analysis(tmp_project, n_features=1)
    with patch("testforge.cases.checklist.create_adapter", side_effect=ValueError("no llm")):
        session = start_session(tmp_project)

    item_id = session.items[0]["id"]
    check_item(tmp_project, item_id, "fail", note="Bug found")

    report_path = finish_session(tmp_project)
    data = json.loads(report_path.read_text())
    assert data["results"][item_id]["status"] == "fail"
    assert data["results"][item_id]["note"] == "Bug found"
