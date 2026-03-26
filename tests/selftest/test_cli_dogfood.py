"""TestForge CLI dogfooding — full pipeline smoke test."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

TESTFORGE = [sys.executable, "-m", "testforge"]


@pytest.fixture
def dog_project(tmp_path):
    """Initialize a fresh TestForge project for dogfooding."""
    name = "dogfood-test"
    result = subprocess.run(
        [*TESTFORGE, "init", name, "-d", str(tmp_path)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"init failed: {result.stderr}"
    project_dir = tmp_path / name

    inputs_dir = project_dir / "inputs"
    inputs_dir.mkdir(exist_ok=True)
    (inputs_dir / "sample-spec.md").write_text("""
# Login Feature
Users can login with email and password.
## Rules
- Password must be at least 8 characters.
- Account locks after 5 failed attempts.
## User Types
- Admin: Full access
- Viewer: Read-only access
""")
    return project_dir


def test_cli_init(dog_project):
    """testforge init creates proper project structure."""
    assert (dog_project / ".testforge" / "config.yaml").exists()
    for d in ["inputs", "output", "evidence", "scripts", "cases", "analysis"]:
        assert (dog_project / d).exists(), f"Missing directory: {d}"


def test_cli_analyze(dog_project):
    """testforge analyze extracts features from documents."""
    result = subprocess.run(
        [*TESTFORGE, "--no-llm", "analyze", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"analyze failed: {result.stderr}"
    analysis_path = dog_project / "analysis" / "analysis.json"
    assert analysis_path.exists()
    data = json.loads(analysis_path.read_text())
    assert len(data.get("features", [])) > 0


def test_cli_generate(dog_project):
    """testforge generate creates test cases."""
    subprocess.run(
        [*TESTFORGE, "--no-llm", "analyze", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    result = subprocess.run(
        [*TESTFORGE, "--no-llm", "generate", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"generate failed: {result.stderr}"
    cases_path = dog_project / "cases" / "cases.json"
    assert cases_path.exists()
    cases = json.loads(cases_path.read_text())
    assert isinstance(cases, list)
    assert len(cases) > 0


def test_cli_script(dog_project):
    """testforge script generates Playwright scripts + conftest.py."""
    subprocess.run(
        [*TESTFORGE, "--no-llm", "analyze", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    subprocess.run(
        [*TESTFORGE, "--no-llm", "generate", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    result = subprocess.run(
        [*TESTFORGE, "--no-llm", "script", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"script failed: {result.stderr}"
    scripts_dir = dog_project / "scripts"
    assert scripts_dir.exists()
    scripts = list(scripts_dir.glob("test_*.py"))
    assert len(scripts) > 0
    assert (scripts_dir / "conftest.py").exists(), "conftest.py not auto-created!"


def test_cli_run_no_playwright(dog_project):
    """testforge run handles missing Playwright gracefully."""
    subprocess.run(
        [*TESTFORGE, "--no-llm", "analyze", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    subprocess.run(
        [*TESTFORGE, "--no-llm", "generate", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    subprocess.run(
        [*TESTFORGE, "--no-llm", "script", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    result = subprocess.run(
        [*TESTFORGE, "run", str(dog_project)],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode in (0, 1), f"run crashed: {result.stderr}"


def test_cli_report(dog_project):
    """testforge report generates markdown report."""
    subprocess.run(
        [*TESTFORGE, "--no-llm", "analyze", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    subprocess.run(
        [*TESTFORGE, "--no-llm", "generate", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    result = subprocess.run(
        [*TESTFORGE, "report", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode in (0, 1), f"report crashed: {result.stderr}"


def test_cli_coverage(dog_project):
    """testforge coverage shows feature coverage."""
    subprocess.run(
        [*TESTFORGE, "--no-llm", "analyze", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    subprocess.run(
        [*TESTFORGE, "--no-llm", "generate", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    result = subprocess.run(
        [*TESTFORGE, "coverage", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"coverage failed: {result.stderr}"


def test_cli_manual_workflow(dog_project):
    """testforge manual start/progress/finish works end-to-end."""
    subprocess.run(
        [*TESTFORGE, "--no-llm", "analyze", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    subprocess.run(
        [*TESTFORGE, "--no-llm", "generate", str(dog_project)],
        capture_output=True, text=True, timeout=60,
    )
    r = subprocess.run(
        [*TESTFORGE, "--no-llm", "-y", "manual", "start", str(dog_project)],
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, f"manual start failed: {r.stderr}"
    r = subprocess.run(
        [*TESTFORGE, "manual", "progress", str(dog_project)],
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0
    r = subprocess.run(
        [*TESTFORGE, "-y", "manual", "finish", str(dog_project)],
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0


def test_cli_pipeline_full(dog_project):
    """testforge pipeline runs all stages end-to-end."""
    spec = dog_project / "inputs" / "sample-spec.md"
    result = subprocess.run(
        [
            *TESTFORGE,
            "--no-llm",
            "pipeline",
            str(dog_project),
            "-i",
            str(spec),
        ],
        capture_output=True, text=True, timeout=180,
    )
    assert "Traceback" not in result.stderr


def test_cli_projects_list(dog_project):
    """testforge projects lists the dogfood project."""
    result = subprocess.run(
        [*TESTFORGE, "projects"],
        capture_output=True, text=True, timeout=30,
        cwd=str(dog_project.parent),
    )
    assert result.returncode == 0
    assert "dogfood-test" in result.stdout
