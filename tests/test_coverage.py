"""Tests for the coverage tracker."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from testforge.coverage.tracker import CoverageReport, compute_coverage


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def analysis_file(tmp_path: Path) -> Path:
    data = {
        "features": [
            {"id": "F-001", "name": "Feature One"},
            {"id": "F-002", "name": "Feature Two"},
            {"id": "F-003", "name": "Feature Three"},
        ],
        "rules": [
            {"id": "R-001", "name": "Rule One"},
            {"id": "R-002", "name": "Rule Two"},
        ],
        "screens": [],
        "personas": [],
        "raw_sources": [],
    }
    path = tmp_path / "analysis.json"
    path.write_text(json.dumps(data))
    return path


@pytest.fixture
def cases_file(tmp_path: Path) -> Path:
    data = [
        {"id": "TC-001", "feature_id": "F-001", "rule_ids": ["R-001"]},
        {"id": "TC-002", "feature_id": "F-002", "rule_ids": []},
        {"id": "TC-003", "feature_id": "F-001", "rule_ids": ["R-001", "R-002"]},
    ]
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(data))
    return path


@pytest.fixture
def empty_cases_file(tmp_path: Path) -> Path:
    path = tmp_path / "cases_empty.json"
    path.write_text("[]")
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_compute_coverage_basic(analysis_file: Path, cases_file: Path) -> None:
    """Coverage counts features and rules correctly."""
    report = compute_coverage(analysis_file, cases_file)

    assert report.total_features == 3
    assert report.covered_features == 2  # F-001 and F-002 covered; F-003 not
    assert report.total_rules == 2
    assert report.covered_rules == 2  # R-001 and R-002 both covered


def test_feature_coverage_pct(analysis_file: Path, cases_file: Path) -> None:
    report = compute_coverage(analysis_file, cases_file)
    assert abs(report.feature_coverage_pct - 66.67) < 0.1


def test_rule_coverage_pct(analysis_file: Path, cases_file: Path) -> None:
    report = compute_coverage(analysis_file, cases_file)
    assert report.rule_coverage_pct == 100.0


def test_uncovered_features(analysis_file: Path, cases_file: Path) -> None:
    report = compute_coverage(analysis_file, cases_file)
    assert "F-003" in report.uncovered_features
    assert "F-001" not in report.uncovered_features


def test_uncovered_rules_empty_when_all_covered(analysis_file: Path, cases_file: Path) -> None:
    report = compute_coverage(analysis_file, cases_file)
    assert report.uncovered_rules == []


def test_feature_matrix(analysis_file: Path, cases_file: Path) -> None:
    """feature_matrix maps each feature id to its covering case ids."""
    report = compute_coverage(analysis_file, cases_file)
    assert "TC-001" in report.feature_matrix["F-001"]
    assert "TC-003" in report.feature_matrix["F-001"]
    assert report.feature_matrix["F-002"] == ["TC-002"]
    assert report.feature_matrix["F-003"] == []


def test_rule_matrix(analysis_file: Path, cases_file: Path) -> None:
    """rule_matrix maps each rule id to its covering case ids."""
    report = compute_coverage(analysis_file, cases_file)
    assert "TC-001" in report.rule_matrix["R-001"]
    assert "TC-003" in report.rule_matrix["R-001"]
    assert report.rule_matrix["R-002"] == ["TC-003"]


def test_zero_coverage_when_no_cases(analysis_file: Path, empty_cases_file: Path) -> None:
    """No cases means zero coverage."""
    report = compute_coverage(analysis_file, empty_cases_file)
    assert report.covered_features == 0
    assert report.covered_rules == 0
    assert report.feature_coverage_pct == 0.0
    assert report.rule_coverage_pct == 0.0
    assert set(report.uncovered_features) == {"F-001", "F-002", "F-003"}
    assert set(report.uncovered_rules) == {"R-001", "R-002"}


def test_coverage_report_pct_zero_totals() -> None:
    """Properties return 0.0 when totals are zero (no division by zero)."""
    report = CoverageReport(
        total_features=0,
        covered_features=0,
        total_rules=0,
        covered_rules=0,
    )
    assert report.feature_coverage_pct == 0.0
    assert report.rule_coverage_pct == 0.0


def test_cases_with_unknown_feature_id(analysis_file: Path, tmp_path: Path) -> None:
    """Cases referencing unknown feature/rule IDs are ignored gracefully."""
    cases = [
        {"id": "TC-001", "feature_id": "F-999", "rule_ids": ["R-999"]},
    ]
    cases_path = tmp_path / "cases_unknown.json"
    cases_path.write_text(json.dumps(cases))

    report = compute_coverage(analysis_file, cases_path)
    assert report.covered_features == 0
    assert report.covered_rules == 0
