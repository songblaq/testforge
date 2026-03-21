"""Test case generator -- orchestrates creation of different case types."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from testforge.core.project import save_cases

logger = logging.getLogger(__name__)


def generate_cases(project_dir: Path, case_type: str = "all") -> list[dict[str, Any]]:
    """Generate test cases for a project.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.
    case_type:
        Type of cases to generate: ``functional``, ``usecase``, ``checklist``, or ``all``.

    Returns
    -------
    list[dict]:
        Generated test cases.
    """
    cases: list[dict[str, Any]] = []

    generators = {
        "functional": _generate_functional,
        "usecase": _generate_usecases,
        "checklist": _generate_checklist,
    }

    if case_type == "all":
        for gen_name, gen in generators.items():
            logger.info("Generating %s cases...", gen_name)
            cases.extend(gen(project_dir))
    elif case_type in generators:
        cases.extend(generators[case_type](project_dir))
    else:
        raise ValueError(f"Unknown case type: {case_type}")

    # Persist generated cases
    if cases:
        save_cases(project_dir, cases)
        logger.info("Saved %d test cases to project", len(cases))

    return cases


def _generate_functional(project_dir: Path) -> list[dict[str, Any]]:
    """Generate functional test cases."""
    from testforge.cases.functional import generate_functional_cases

    return generate_functional_cases(project_dir)


def _generate_usecases(project_dir: Path) -> list[dict[str, Any]]:
    """Generate use case test scenarios."""
    from testforge.cases.usecases import generate_usecase_tests

    return generate_usecase_tests(project_dir)


def _generate_checklist(project_dir: Path) -> list[dict[str, Any]]:
    """Generate manual test checklists."""
    from testforge.cases.checklist import generate_checklist

    return generate_checklist(project_dir)
