"""Failure analyzer -- uses LLM to diagnose test failures."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from testforge.report.generator import TestCaseResult

logger = logging.getLogger(__name__)


def analyze_failures(
    project_dir: Path, failed_cases: list[TestCaseResult]
) -> list[dict[str, Any]]:
    """Analyze failed test cases and suggest improvements.

    Parameters
    ----------
    project_dir:
        TestForge project root.
    failed_cases:
        List of failed TestCaseResult objects.

    Returns
    -------
    list[dict]:
        Analysis results with suggested improvements.
    """
    from testforge.core.config import load_config
    from testforge.llm import create_adapter

    config = load_config(project_dir)
    results: list[dict[str, Any]] = []

    try:
        adapter = create_adapter(config.llm_provider, model=config.llm_model)
    except Exception as exc:
        logger.warning("LLM unavailable for failure analysis: %s", exc)
        return _deterministic_analysis(failed_cases)

    for case in failed_cases:
        prompt = _build_analysis_prompt(case)
        try:
            response = adapter.complete(prompt)
            analysis = {
                "case_id": case.id,
                "case_name": case.name,
                "error_message": case.error_message,
                "llm_analysis": response.text,
                "improvement_suggested": True,
            }
        except Exception as exc:
            logger.warning("LLM analysis failed for %s: %s", case.id, exc)
            analysis = {
                "case_id": case.id,
                "case_name": case.name,
                "error_message": case.error_message,
                "llm_analysis": f"Analysis failed: {exc}",
                "improvement_suggested": False,
            }
        results.append(analysis)

    return results


def _build_analysis_prompt(case: TestCaseResult) -> str:
    """Build the LLM prompt for failure analysis."""
    steps_text = ""
    if case.steps:
        steps_text = "\nSteps:\n" + "\n".join(
            f"  - {s.get('description', s.get('name', str(s)))}: {s.get('status', 'unknown')}"
            for s in case.steps
        )

    return f"""Analyze this failed test case and suggest improvements.

Test: {case.name} ({case.id})
Status: {case.status}
Error: {case.error_message}
{steps_text}

Provide:
1. Root cause analysis
2. Suggested fix for the test case
3. Whether the test expectation or the implementation is likely wrong
"""


def _deterministic_analysis(failed_cases: list[TestCaseResult]) -> list[dict[str, Any]]:
    """Fallback analysis without LLM."""
    results = []
    for case in failed_cases:
        analysis = {
            "case_id": case.id,
            "case_name": case.name,
            "error_message": case.error_message,
            "llm_analysis": "LLM unavailable. Manual review recommended.",
            "improvement_suggested": bool(case.error_message),
        }
        results.append(analysis)
    return results
