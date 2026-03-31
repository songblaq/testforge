"""Cross-validation — compare results across execution engines."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from testforge.execution.engines.base import EngineResult


@dataclass
class CrossValidationResult:
    """Result of comparing a single test case across engines."""

    case_id: str
    engine_results: dict[str, EngineResult]
    consensus: str  # "agree" or "disagree"
    consensus_status: str  # majority-voted status
    discrepancies: list[str] = field(default_factory=list)

    @property
    def all_agree(self) -> bool:
        return self.consensus == "agree"


def cross_validate(
    results_by_engine: dict[str, list[EngineResult]],
) -> list[CrossValidationResult]:
    """Compare results across engines for each case_id.

    Groups EngineResults by case_id, compares statuses, returns
    a CrossValidationResult per case_id.
    """
    by_case: dict[str, dict[str, EngineResult]] = {}
    for engine_name, results in results_by_engine.items():
        for r in results:
            by_case.setdefault(r.case_id, {})[engine_name] = r

    validations: list[CrossValidationResult] = []
    for case_id, engine_results in sorted(by_case.items()):
        statuses = [r.status for r in engine_results.values()]
        unique = set(statuses)

        if len(unique) == 1:
            consensus = "agree"
            consensus_status = statuses[0]
            discrepancies: list[str] = []
        else:
            consensus = "disagree"
            counts = Counter(statuses)
            top_two = counts.most_common(2)
            if len(top_two) > 1 and top_two[0][1] == top_two[1][1]:
                priority = ["failed", "error", "passed", "skipped"]
                consensus_status = min(
                    (s for s, _ in top_two),
                    key=lambda x: priority.index(x) if x in priority else len(priority),
                )
            else:
                consensus_status = top_two[0][0]
            discrepancies = [
                f"{name}: {r.status} (expected {consensus_status})"
                for name, r in engine_results.items()
                if r.status != consensus_status
            ]

        validations.append(CrossValidationResult(
            case_id=case_id,
            engine_results=engine_results,
            consensus=consensus,
            consensus_status=consensus_status,
            discrepancies=discrepancies,
        ))

    return validations


def format_cross_validation_report(results: list[CrossValidationResult]) -> str:
    """Format cross-validation results as a human-readable report."""
    lines: list[str] = ["# Cross-Validation Report", ""]
    agree = sum(1 for r in results if r.all_agree)
    disagree = len(results) - agree
    lines.append(f"Total: {len(results)} | Agree: {agree} | Disagree: {disagree}")
    lines.append("")

    if disagree > 0:
        lines.append("## Discrepancies")
        lines.append("")
        for r in results:
            if not r.all_agree:
                lines.append(f"### {r.case_id}")
                lines.append(f"Consensus: {r.consensus_status}")
                for d in r.discrepancies:
                    lines.append(f"  - {d}")
                lines.append("")

    return "\n".join(lines)
