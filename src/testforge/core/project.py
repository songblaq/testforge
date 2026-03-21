"""Project management -- create, list, and manage TestForge projects."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from testforge.core.config import TestForgeConfig, load_config, save_config


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Feature:
    """A testable feature extracted from input documents."""

    id: str
    name: str
    description: str
    category: str = ""
    priority: str = "medium"
    screens: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    source: str = ""


@dataclass
class Screen:
    """A UI screen or page identified in the project."""

    id: str
    name: str
    description: str
    url_pattern: str = ""
    features: list[str] = field(default_factory=list)
    elements: list[dict[str, str]] = field(default_factory=list)


@dataclass
class Persona:
    """A user persona derived from project analysis."""

    id: str
    name: str
    description: str
    goals: list[str] = field(default_factory=list)
    pain_points: list[str] = field(default_factory=list)
    tech_level: str = "intermediate"


@dataclass
class BusinessRule:
    """A business rule extracted from project documents."""

    id: str
    name: str
    description: str
    condition: str = ""
    expected_behavior: str = ""
    source: str = ""


@dataclass
class AnalysisResult:
    """Aggregated result of the analysis stage."""

    features: list[Feature] = field(default_factory=list)
    screens: list[Screen] = field(default_factory=list)
    personas: list[Persona] = field(default_factory=list)
    rules: list[BusinessRule] = field(default_factory=list)
    raw_sources: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "features": [asdict(f) for f in self.features],
            "screens": [asdict(s) for s in self.screens],
            "personas": [asdict(p) for p in self.personas],
            "rules": [asdict(r) for r in self.rules],
            "raw_sources": self.raw_sources,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalysisResult":
        return cls(
            features=[Feature(**f) for f in data.get("features", [])],
            screens=[Screen(**s) for s in data.get("screens", [])],
            personas=[Persona(**p) for p in data.get("personas", [])],
            rules=[BusinessRule(**r) for r in data.get("rules", [])],
            raw_sources=data.get("raw_sources", []),
        )


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------


def create_project(project_dir: Path) -> Path:
    """Create a new TestForge project with default structure."""
    project_dir.mkdir(parents=True, exist_ok=True)

    subdirs = ["inputs", "output", "evidence", "scripts", "cases", "analysis"]
    for subdir in subdirs:
        (project_dir / subdir).mkdir(exist_ok=True)

    config = TestForgeConfig(project_name=project_dir.name)
    save_config(project_dir, config)

    return project_dir


def list_projects(base_dir: Path | None = None) -> list[str]:
    """List TestForge projects found under *base_dir* (default: cwd)."""
    base = base_dir or Path.cwd()
    projects: list[str] = []

    for candidate in base.iterdir():
        if candidate.is_dir() and (candidate / ".testforge" / "config.yaml").exists():
            projects.append(candidate.name)

    return sorted(projects)


def save_analysis(project_dir: Path, result: AnalysisResult) -> Path:
    """Persist analysis results to the project's analysis directory."""
    config = load_config(project_dir)
    analysis_dir = project_dir / config.analysis_dir
    analysis_dir.mkdir(parents=True, exist_ok=True)
    out_path = analysis_dir / "analysis.json"

    with open(out_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    return out_path


def load_analysis(project_dir: Path) -> AnalysisResult | None:
    """Load previously saved analysis results, or None if not found."""
    config = load_config(project_dir)
    analysis_path = project_dir / config.analysis_dir / "analysis.json"

    if not analysis_path.exists():
        return None

    with open(analysis_path) as f:
        data = json.load(f)

    return AnalysisResult.from_dict(data)


def save_cases(project_dir: Path, cases: list[dict[str, Any]]) -> Path:
    """Persist generated test cases to the project's cases directory."""
    config = load_config(project_dir)
    cases_dir = project_dir / config.cases_dir
    cases_dir.mkdir(parents=True, exist_ok=True)
    out_path = cases_dir / "cases.json"

    with open(out_path, "w") as f:
        json.dump(cases, f, indent=2, ensure_ascii=False)

    return out_path


def load_cases(project_dir: Path) -> list[dict[str, Any]]:
    """Load previously saved test cases."""
    config = load_config(project_dir)
    cases_path = project_dir / config.cases_dir / "cases.json"

    if not cases_path.exists():
        return []

    with open(cases_path) as f:
        return json.load(f)
