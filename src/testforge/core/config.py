"""Configuration management for TestForge projects."""

from __future__ import annotations

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
    input_dir: str = "inputs"
    output_dir: str = "output"
    evidence_dir: str = "evidence"
    cases_dir: str = "cases"
    analysis_dir: str = "analysis"
    extra: dict[str, Any] = field(default_factory=dict)


def load_config(project_dir: Path) -> TestForgeConfig:
    """Load configuration from a project directory."""
    config_path = project_dir / ".testforge" / "config.yaml"
    if not config_path.exists():
        return TestForgeConfig(project_name=project_dir.name)

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    return TestForgeConfig(
        project_name=data.get("project_name", project_dir.name),
        version=data.get("version", "0.1.0"),
        llm_provider=data.get("llm_provider", "anthropic"),
        llm_model=data.get("llm_model", ""),
        input_dir=data.get("input_dir", "inputs"),
        output_dir=data.get("output_dir", "output"),
        evidence_dir=data.get("evidence_dir", "evidence"),
        cases_dir=data.get("cases_dir", "cases"),
        analysis_dir=data.get("analysis_dir", "analysis"),
        extra=data.get("extra", {}),
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
        "input_dir": config.input_dir,
        "output_dir": config.output_dir,
        "evidence_dir": config.evidence_dir,
        "cases_dir": config.cases_dir,
        "analysis_dir": config.analysis_dir,
        "extra": config.extra,
    }

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)

    return config_path
