"""Report generation and retrieval endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/projects", tags=["reports"])


@router.get("/{project_path:path}/report")
async def get_report(project_path: str, fmt: str = Query("markdown", description="markdown or html")):
    """Generate and return a test report."""
    from testforge.report.generator import generate_report

    p = Path(project_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")

    if fmt not in ("markdown", "html"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    try:
        report_path = generate_report(p, fmt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    content = report_path.read_text(encoding="utf-8")
    return {"report": content, "format": fmt, "path": str(report_path)}


@router.get("/{project_path:path}/coverage")
async def get_coverage(project_path: str):
    """Get feature and rule coverage for a project."""
    from testforge.core.config import load_config
    from testforge.coverage.tracker import compute_coverage

    p = Path(project_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")

    config = load_config(p)
    analysis_path = p / config.analysis_dir / "analysis.json"
    cases_path = p / config.cases_dir / "cases.json"

    if not analysis_path.exists():
        raise HTTPException(status_code=404, detail="No analysis results found")
    if not cases_path.exists():
        raise HTTPException(status_code=404, detail="No test cases found")

    report = compute_coverage(analysis_path, cases_path)
    return {
        "coverage": {
            "total_features": report.total_features,
            "covered_features": report.covered_features,
            "feature_coverage_pct": report.feature_coverage_pct,
            "total_rules": report.total_rules,
            "covered_rules": report.covered_rules,
            "rule_coverage_pct": report.rule_coverage_pct,
            "uncovered_features": report.uncovered_features,
            "uncovered_rules": report.uncovered_rules,
            "feature_matrix": report.feature_matrix,
            "rule_matrix": report.rule_matrix,
        }
    }
