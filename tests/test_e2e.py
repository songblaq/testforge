"""End-to-end integration tests for the TestForge pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from testforge.core.project import (
    AnalysisResult,
    BusinessRule,
    Feature,
    Persona,
    Screen,
    create_project,
    load_analysis,
    load_cases,
    save_analysis,
)
from testforge.core.pipeline import run_pipeline
from testforge.input.parser import ParsedDocument, parse
from testforge.report.generator import TestRun, generate_report, load_test_run
from testforge.llm.adapter import LLMAdapter, LLMResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_SPEC = FIXTURES_DIR / "sample-spec.md"


def _make_mock_adapter(json_text: str) -> LLMAdapter:
    """Return a mock LLMAdapter that returns *json_text* for any complete() call."""
    adapter = MagicMock(spec=LLMAdapter)
    adapter.complete.return_value = LLMResponse(text=json_text, model="mock")
    return adapter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def e2e_project(tmp_path: Path) -> Path:
    """Create a fresh TestForge project in a temp directory."""
    project_dir = tmp_path / "e2e-project"
    create_project(project_dir)
    return project_dir


@pytest.fixture
def project_with_analysis(e2e_project: Path) -> Path:
    """Project pre-populated with a minimal AnalysisResult."""
    result = AnalysisResult(
        features=[
            Feature(
                id="F-001",
                name="로그인",
                description="이메일/비밀번호로 로그인",
                priority="high",
                tags=["auth"],
            ),
            Feature(
                id="F-002",
                name="회원가입",
                description="신규 사용자 계정 생성",
                priority="high",
                tags=["auth"],
            ),
            Feature(
                id="F-003",
                name="게시판",
                description="게시글 CRUD",
                priority="medium",
                tags=["board"],
            ),
        ],
        personas=[
            Persona(id="P-001", name="일반 사용자", description="기본 사용자"),
        ],
        rules=[
            BusinessRule(
                id="R-001",
                name="나이 제한",
                description="만 14세 미만 가입 불가",
                condition="age < 14",
                expected_behavior="가입 거부",
            ),
        ],
    )
    save_analysis(e2e_project, result)
    return e2e_project


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestProjectLifecycle:
    """test_project_lifecycle: init -> project structure verification."""

    def test_creates_directory(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "lifecycle-project"
        result = create_project(project_dir)
        assert result == project_dir
        assert project_dir.is_dir()

    def test_creates_subdirectories(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "lifecycle-project"
        create_project(project_dir)
        for subdir in ("inputs", "output", "evidence", "scripts", "cases", "analysis"):
            assert (project_dir / subdir).is_dir(), f"Missing subdir: {subdir}"

    def test_creates_config_file(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "lifecycle-project"
        create_project(project_dir)
        config_path = project_dir / ".testforge" / "config.yaml"
        assert config_path.exists()

    def test_config_contains_project_name(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "my-app"
        create_project(project_dir)
        import yaml
        with open(project_dir / ".testforge" / "config.yaml") as f:
            data = yaml.safe_load(f)
        assert data["project_name"] == "my-app"


class TestInputParsing:
    """test_input_parsing: markdown parser -> ParsedDocument."""

    def test_parse_returns_parsed_document(self) -> None:
        doc = parse(str(SAMPLE_SPEC))
        assert isinstance(doc, ParsedDocument)

    def test_source_type_is_markdown(self) -> None:
        doc = parse(str(SAMPLE_SPEC))
        assert doc.source_type == "markdown"

    def test_text_is_non_empty(self) -> None:
        doc = parse(str(SAMPLE_SPEC))
        assert len(doc.text) > 0

    def test_headings_extracted(self) -> None:
        doc = parse(str(SAMPLE_SPEC))
        # The spec has multiple headings
        assert len(doc.headings) >= 3

    def test_source_path_matches(self) -> None:
        doc = parse(str(SAMPLE_SPEC))
        assert doc.source_path == str(SAMPLE_SPEC)

    def test_raw_has_type_key(self) -> None:
        doc = parse(str(SAMPLE_SPEC))
        assert doc.raw.get("type") == "markdown"

    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "file.xyz"
        bad_file.write_text("content")
        with pytest.raises(ValueError, match="Unsupported file format"):
            parse(str(bad_file))


class TestAnalysisPipeline:
    """test_analysis_pipeline: analyzer with mocked LLM -> AnalysisResult structure."""

    def test_run_analysis_with_mock_llm(self, e2e_project: Path) -> None:
        mock_response = json.dumps({
            "features": [
                {"name": "로그인", "description": "이메일 로그인", "category": "auth",
                 "priority": "high", "screens": [], "tags": ["auth"], "source": ""},
                {"name": "회원가입", "description": "계정 생성", "category": "auth",
                 "priority": "high", "screens": [], "tags": [], "source": ""},
            ],
            "screens": [
                {"name": "로그인 화면", "description": "로그인 폼", "url_pattern": "/login",
                 "features": ["로그인"], "elements": []},
            ],
            "personas": [
                {"name": "일반 사용자", "description": "기본 사용자", "goals": [],
                 "pain_points": [], "tech_level": "intermediate"},
            ],
            "rules": [
                {"name": "나이 제한", "description": "14세 미만 불가",
                 "condition": "age < 14", "expected_behavior": "가입 거부"},
            ],
        })

        mock_adapter = _make_mock_adapter(mock_response)

        with patch("testforge.llm.create_adapter", return_value=mock_adapter):
            from testforge.analysis.analyzer import run_analysis
            features = run_analysis(e2e_project, [str(SAMPLE_SPEC)])

        # returns a flat list of dicts (one per parsed doc)
        assert isinstance(features, list)
        assert len(features) == 1
        assert "features" in features[0]

    def test_run_analysis_offline_fallback(self, e2e_project: Path) -> None:
        """When LLM adapter unavailable, persists heuristic offline analysis."""
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            from testforge.analysis.analyzer import run_analysis
            features = run_analysis(e2e_project, [str(SAMPLE_SPEC)])

        assert isinstance(features, list)
        assert features
        assert features[0]["features"]

        analysis = load_analysis(e2e_project)
        assert analysis is not None
        assert len(analysis.features) >= 1

    def test_run_analysis_no_inputs(self, e2e_project: Path) -> None:
        from testforge.analysis.analyzer import run_analysis
        features = run_analysis(e2e_project, [])
        assert features == []

    def test_analysis_saved_to_disk(self, e2e_project: Path) -> None:
        mock_response = json.dumps({
            "features": [{"name": "F1", "description": "d", "category": "",
                          "priority": "low", "screens": [], "tags": [], "source": ""}],
            "screens": [], "personas": [], "rules": [],
        })
        mock_adapter = _make_mock_adapter(mock_response)

        with patch("testforge.llm.create_adapter", return_value=mock_adapter):
            from testforge.analysis.analyzer import run_analysis
            run_analysis(e2e_project, [str(SAMPLE_SPEC)])

        analysis = load_analysis(e2e_project)
        assert analysis is not None
        assert len(analysis.features) >= 1


class TestCaseGenerationStructure:
    """test_case_generation_structure: generated cases have required keys."""

    REQUIRED_KEYS = {"id", "title", "description", "feature_id", "priority", "tags", "steps"}

    def test_skeleton_cases_have_required_keys(self, project_with_analysis: Path) -> None:
        """Without LLM, skeleton cases are generated; verify their structure."""
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            from testforge.cases.generator import generate_cases
            cases = generate_cases(project_with_analysis, "functional")

        assert len(cases) > 0
        for case in cases:
            missing = self.REQUIRED_KEYS - set(case.keys())
            assert not missing, f"Case missing keys: {missing}"

    def test_skeleton_cases_steps_are_list(self, project_with_analysis: Path) -> None:
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            from testforge.cases.generator import generate_cases
            cases = generate_cases(project_with_analysis, "functional")

        for case in cases:
            assert isinstance(case["steps"], list)

    def test_generate_cases_saved_to_disk(self, project_with_analysis: Path) -> None:
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            from testforge.cases.generator import generate_cases
            generate_cases(project_with_analysis, "functional")

        saved = load_cases(project_with_analysis)
        assert len(saved) > 0

    def test_unknown_case_type_raises(self, project_with_analysis: Path) -> None:
        from testforge.cases.generator import generate_cases
        with pytest.raises(ValueError, match="Unknown case type"):
            generate_cases(project_with_analysis, "nonexistent_type")

    def test_generate_cases_no_analysis_returns_empty(self, e2e_project: Path) -> None:
        """When no analysis exists, skeleton generator returns empty list."""
        from testforge.cases.generator import generate_cases
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            cases = generate_cases(e2e_project, "functional")
        assert cases == []


class TestReportGeneration:
    """test_report_generation: empty TestRun -> markdown file created."""

    def test_generates_markdown_file(self, e2e_project: Path) -> None:
        report_path = generate_report(e2e_project, fmt="markdown")
        assert report_path.exists()
        assert report_path.suffix == ".md"

    def test_report_contains_project_name(self, e2e_project: Path) -> None:
        report_path = generate_report(e2e_project, fmt="markdown")
        content = report_path.read_text(encoding="utf-8")
        assert "e2e-project" in content

    def test_report_contains_summary_section(self, e2e_project: Path) -> None:
        report_path = generate_report(e2e_project, fmt="markdown")
        content = report_path.read_text(encoding="utf-8")
        # Accept both English ("Summary") and Korean ("요약") locale labels
        assert "Summary" in content or "요약" in content

    def test_report_custom_output_path(self, e2e_project: Path, tmp_path: Path) -> None:
        custom_out = tmp_path / "custom-report.md"
        report_path = generate_report(e2e_project, fmt="markdown", output=str(custom_out))
        assert report_path == custom_out
        assert custom_out.exists()

    def test_load_test_run_empty_project(self, e2e_project: Path) -> None:
        """load_test_run on a project with no results returns empty TestRun."""
        test_run = load_test_run(e2e_project)
        assert isinstance(test_run, TestRun)
        assert test_run.total == 0

    def test_test_run_with_results(self, e2e_project: Path) -> None:
        """TestRun loaded from a results.json reflects correct counts."""
        from testforge.core.config import load_config
        config = load_config(e2e_project)
        output_dir = e2e_project / config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        results_data = {
            "started_at": "2026-03-21T10:00:00",
            "finished_at": "2026-03-21T10:05:00",
            "environment": {},
            "results": [
                {"id": "TC-001", "name": "Login test", "status": "passed"},
                {"id": "TC-002", "name": "Signup test", "status": "failed",
                 "error_message": "Element not found"},
                {"id": "TC-003", "name": "Board test", "status": "skipped"},
            ],
        }
        (output_dir / "results.json").write_text(
            json.dumps(results_data), encoding="utf-8"
        )

        test_run = load_test_run(e2e_project)
        assert test_run.total == 3
        assert test_run.passed == 1
        assert test_run.failed == 1
        assert test_run.skipped == 1


class TestFullPipelineDryrun:
    """test_full_pipeline_dryrun: all stages complete without error (mocked LLM)."""

    def test_analyze_stage_only(self, e2e_project: Path) -> None:
        mock_adapter = _make_mock_adapter(
            json.dumps({"features": [], "screens": [], "personas": [], "rules": []})
        )
        with patch("testforge.llm.create_adapter", return_value=mock_adapter):
            result = run_pipeline(e2e_project, stages=["analyze"],
                                  inputs=[str(SAMPLE_SPEC)])
        assert result.success
        assert "analyze" in result.stages_completed

    def test_report_stage_only(self, e2e_project: Path) -> None:
        result = run_pipeline(e2e_project, stages=["report"])
        assert result.success
        assert "report" in result.stages_completed

    def test_analyze_then_report(self, e2e_project: Path) -> None:
        mock_adapter = _make_mock_adapter(
            json.dumps({"features": [], "screens": [], "personas": [], "rules": []})
        )
        with patch("testforge.llm.create_adapter", return_value=mock_adapter):
            result = run_pipeline(
                e2e_project,
                stages=["analyze", "report"],
                inputs=[str(SAMPLE_SPEC)],
            )
        assert result.success
        assert result.stages_completed == ["analyze", "report"]

    def test_pipeline_unknown_stage_is_error(self, e2e_project: Path) -> None:
        result = run_pipeline(e2e_project, stages=["analyze", "ghost_stage"])
        assert not result.success
        assert any("ghost_stage" in e for e in result.errors)

    def test_generate_stage_with_analysis(self, project_with_analysis: Path) -> None:
        """generate stage on a project that already has analysis => skeleton cases."""
        with patch("testforge.llm.create_adapter", side_effect=ImportError("no llm")):
            result = run_pipeline(project_with_analysis, stages=["generate"])
        assert result.success
        assert "generate" in result.stages_completed
        assert result.summary["generate"]["cases_generated"] >= 0

    def test_pipeline_result_has_project_name(self, e2e_project: Path) -> None:
        result = run_pipeline(e2e_project, stages=["report"])
        assert result.project == "e2e-project"
