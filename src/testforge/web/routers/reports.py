"""Report generation and retrieval endpoints with immutable history."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from testforge.web.deps import resolve_project

router = APIRouter(prefix="/api/projects", tags=["reports"])


@router.post("/{project_path:path}/report")
async def create_report(project_path: str, fmt: str = Query("markdown", description="markdown or html")):
    """Generate and return a test report, saving immutable copy."""
    from testforge.core.config import load_config
    from testforge.report.generator import generate_report

    p = resolve_project(project_path)

    if fmt not in ("markdown", "html"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    try:
        report_path = generate_report(p, fmt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    content = report_path.read_text(encoding="utf-8")

    config = load_config(p)
    output_dir = p / config.output_dir
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    ext = ".html" if fmt == "html" else ".md"
    immutable_path = reports_dir / f"report_{report_id}{ext}"
    immutable_path.write_text(content, encoding="utf-8")

    meta = {
        "report_id": report_id,
        "format": fmt,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file": immutable_path.name,
    }
    meta_path = reports_dir / f"report_{report_id}.meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return {"report": content, "format": fmt, "path": str(report_path), "report_id": report_id}


@router.get("/{project_path:path}/reports")
async def list_reports(project_path: str):
    """List all immutable report history."""
    from testforge.core.config import load_config

    p = resolve_project(project_path)
    config = load_config(p)
    reports_dir = p / config.output_dir / "reports"

    reports = []
    if reports_dir.exists():
        for f in sorted(reports_dir.glob("report_*.meta.json"), reverse=True):
            try:
                meta = json.loads(f.read_text())
                reports.append(meta)
            except Exception:
                pass

    return {"reports": reports, "count": len(reports)}


@router.get("/{project_path:path}/reports/{report_id}")
async def get_report_by_id(project_path: str, report_id: str):
    """Get a specific report by ID."""
    from testforge.core.config import load_config

    p = resolve_project(project_path)
    config = load_config(p)
    reports_dir = p / config.output_dir / "reports"

    if ".." in report_id or "/" in report_id:
        raise HTTPException(status_code=400, detail="Invalid report_id")

    meta_path = reports_dir / f"report_{report_id}.meta.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    meta = json.loads(meta_path.read_text())
    report_filename = Path(meta["file"]).name
    report_file = reports_dir / report_filename
    if not report_file.resolve().is_relative_to(reports_dir.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="Report file missing")

    content = report_file.read_text(encoding="utf-8")
    return {"report": content, "meta": meta}


@router.get("/{project_path:path}/coverage")
async def get_coverage(project_path: str):
    """Get feature and rule coverage for a project."""
    from testforge.core.config import load_config
    from testforge.coverage.tracker import compute_coverage

    p = resolve_project(project_path)

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
