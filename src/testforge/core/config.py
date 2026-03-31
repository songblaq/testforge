"""Configuration management for TestForge projects."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class TestForgeConfig:
    """Project-level configuration."""

    project_name: str = ""
    version: str = "0.1.0"
    llm_provider: str = "anthropic"
    llm_model: str = ""
    locale: str = "ko"
    input_dir: str = "inputs"
    output_dir: str = "output"
    evidence_dir: str = "evidence"
    cases_dir: str = "cases"
    analysis_dir: str = "analysis"
    extra: dict[str, Any] = field(default_factory=dict)
    execution_engines: list[str] = field(default_factory=lambda: ["playwright"])
    engine_configs: dict[str, dict[str, Any]] = field(default_factory=dict)
    cross_validation: bool = False


def effective_locale(config: TestForgeConfig) -> str:
    """Resolve locale: ``TESTFORGE_LOCALE`` overrides ``config.locale``."""
    override = os.environ.get("TESTFORGE_LOCALE", "").strip()
    if override:
        return override
    loc = (config.locale or "ko").strip()
    return loc or "ko"


_LOCALE_KO_USER_FACING_LINE = (
    "All user-facing text (names, descriptions, steps, expected results) "
    "MUST be written in Korean."
)


def append_locale_user_facing_instruction(prompt: str, locale: str) -> str:
    """Append Korean user-facing output instruction when primary language tag is ``ko``."""
    primary = (locale or "").strip().split("-", 1)[0].lower()
    if primary == "ko":
        return prompt.rstrip() + "\n\n" + _LOCALE_KO_USER_FACING_LINE
    return prompt


def load_config(project_dir: Path) -> TestForgeConfig:
    """Load configuration from a project directory.

    Resolution order (later values override earlier):
    1. Defaults
    2. ``{project_dir}/testforge.yaml`` (project-root config)
    3. ``{project_dir}/.testforge/config.yaml`` (local override)
    """
    data: dict[str, Any] = {}

    root_config = project_dir / "testforge.yaml"
    if root_config.exists():
        with open(root_config) as f:
            data.update(yaml.safe_load(f) or {})

    local_config = project_dir / ".testforge" / "config.yaml"
    if local_config.exists():
        with open(local_config) as f:
            data.update(yaml.safe_load(f) or {})

    return TestForgeConfig(
        project_name=data.get("project_name", project_dir.name),
        version=data.get("version", "0.1.0"),
        llm_provider=data.get("llm_provider", "anthropic"),
        llm_model=data.get("llm_model", ""),
        locale=data.get("locale", "ko"),
        input_dir=data.get("input_dir", "inputs"),
        output_dir=data.get("output_dir", "output"),
        evidence_dir=data.get("evidence_dir", "evidence"),
        cases_dir=data.get("cases_dir", "cases"),
        analysis_dir=data.get("analysis_dir", "analysis"),
        extra=data.get("extra", {}),
        execution_engines=data.get("execution_engines", ["playwright"]),
        engine_configs=data.get("engine_configs", {}),
        cross_validation=data.get("cross_validation", False),
    )


def save_config(project_dir: Path, config: TestForgeConfig) -> Path:
    """Save configuration to a project directory."""
    config_dir = project_dir / ".testforge"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"

    data = {
        "project_name": config.project_name,
        "version": config.version,
        "llm_provider": config.llm_provider,
        "llm_model": config.llm_model,
        "locale": config.locale,
        "input_dir": config.input_dir,
        "output_dir": config.output_dir,
        "evidence_dir": config.evidence_dir,
        "cases_dir": config.cases_dir,
        "analysis_dir": config.analysis_dir,
        "extra": config.extra,
        "execution_engines": config.execution_engines,
        "engine_configs": config.engine_configs,
        "cross_validation": config.cross_validation,
    }

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)

    return config_path
