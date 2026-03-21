"""Coverage tracker -- compute feature and rule coverage from analysis + cases."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CoverageReport:
    """Coverage of features and rules by test cases."""

    total_features: int
    covered_features: int
    total_rules: int
    covered_rules: int
    feature_matrix: dict[str, list[str]] = field(default_factory=dict)  # feature_id -> [case_ids]
    rule_matrix: dict[str, list[str]] = field(default_factory=dict)     # rule_id -> [case_ids]
    uncovered_features: list[str] = field(default_factory=list)
    uncovered_rules: list[str] = field(default_factory=list)

    @property
    def feature_coverage_pct(self) -> float:
        return (self.covered_features / self.total_features * 100) if self.total_features else 0.0

    @property
    def rule_coverage_pct(self) -> float:
        return (self.covered_rules / self.total_rules * 100) if self.total_rules else 0.0


def compute_coverage(analysis_path: Path, cases_path: Path) -> CoverageReport:
    """Compute coverage by comparing analysis results against test cases.

    Parameters
    ----------
    analysis_path:
        Path to ``analysis.json`` produced by the analyze stage.
    cases_path:
        Path to ``cases.json`` produced by the generate stage.

    Returns
    -------
    CoverageReport:
        Coverage metrics and traceability matrices.
    """
    # Load analysis
    with open(analysis_path) as f:
        analysis_data = json.load(f)

    all_features: list[str] = [f["id"] for f in analysis_data.get("features", [])]
    all_rules: list[str] = [r["id"] for r in analysis_data.get("rules", [])]

    # Load cases
    with open(cases_path) as f:
        cases_data = json.load(f)

    # Build traceability matrices
    feature_matrix: dict[str, list[str]] = {fid: [] for fid in all_features}
    rule_matrix: dict[str, list[str]] = {rid: [] for rid in all_rules}

    for case in cases_data:
        case_id = case.get("id", "")

        # Feature coverage: cases reference a single feature_id
        fid = case.get("feature_id", "")
        if fid and fid in feature_matrix:
            feature_matrix[fid].append(case_id)

        # Rule coverage: cases may reference multiple rule_ids
        for rid in case.get("rule_ids", []):
            if rid in rule_matrix:
                rule_matrix[rid].append(case_id)

    covered_features = [fid for fid, cases in feature_matrix.items() if cases]
    covered_rules = [rid for rid, cases in rule_matrix.items() if cases]

    return CoverageReport(
        total_features=len(all_features),
        covered_features=len(covered_features),
        total_rules=len(all_rules),
        covered_rules=len(covered_rules),
        feature_matrix=feature_matrix,
        rule_matrix=rule_matrix,
        uncovered_features=[fid for fid in all_features if fid not in covered_features],
        uncovered_rules=[rid for rid in all_rules if rid not in covered_rules],
    )
