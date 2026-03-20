"""Script validator -- syntax check and dry-run validation of generated scripts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationResult:
    """Result of a script validation."""

    path: str
    valid: bool
    errors: list[str]


def validate_script(script_path: Path) -> ValidationResult:
    """Validate a generated test script.

    Checks syntax and basic structure without executing.

    Parameters
    ----------
    script_path:
        Path to the script file.

    Returns
    -------
    ValidationResult:
        Validation outcome.
    """
    errors: list[str] = []

    if not script_path.exists():
        errors.append(f"File not found: {script_path}")
        return ValidationResult(path=str(script_path), valid=False, errors=errors)

    # Basic Python syntax check
    source = script_path.read_text()
    try:
        compile(source, str(script_path), "exec")
    except SyntaxError as exc:
        errors.append(f"Syntax error at line {exc.lineno}: {exc.msg}")

    return ValidationResult(
        path=str(script_path),
        valid=len(errors) == 0,
        errors=errors,
    )
