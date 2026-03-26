# TestForge v0.4 — 도그푸딩 + 품질 경화 Cursor 배치 프롬프트

> **지시**: 서브에이전트를 병렬로 호출해서 작업하라. 각 Phase 내 독립 작업은 반드시 병렬. Phase 간은 순차.
> **Runtime**: Cursor (1 request = 1 consume)
> **목표**: TestForge로 TestForge 자체를 CLI/GUI 양쪽에서 도그푸딩. 발견 이슈 즉시 수정. 비개발자가 실제 사용 가능한 상태로.

---

## 이미 완료된 작업 — 절대 건드리지 말 것

### 절대 수정 금지 파일/기능
- `src/testforge/web/routers/*.py` — 8개 라우터 전부 (40개 엔드포인트 정상 작동)
- `src/testforge/web/deps.py` — load_mappings/save_mappings
- `src/testforge/web/app.py` — 라우터 등록 구조
- `src/testforge/core/project.py` — 데이터 모델 (Feature, Persona, BusinessRule, AnalysisResult)
- `src/testforge/core/config.py` — TestForgeConfig 데이터클래스
- `src/testforge/llm/agent.py` — detect_agent_runtime
- `src/testforge/input/code.py` — AST 기반 파서
- `app.js`의 CRUD 모달 시스템, 드릴다운, LLM 설정 패널, 실행 이력, 보고서 이력
- `tests/test_web.py` — 65개 테스트 (전부 통과 상태 유지 필수)

### 테스트 검증 명령
```bash
.venv/bin/python -m pytest tests/test_web.py -q --tb=line
# 반드시 65+ passed 유지
```

---

## Phase 0: 인프라 수정 (순차, Phase 1 선행 조건)

### Task 0A: conftest.py 자동 생성 보장

**문제**: `scripts/` 디렉토리에 conftest.py가 없어서 생성된 Playwright 스크립트가 실행 시 `ModuleNotFoundError` 발생.
`src/testforge/scripts/generator.py` L55-58에 자동 생성 코드가 있으나, `--no-llm` 모드에서 일부 경로를 건너뜀.

**파일**: `src/testforge/scripts/generator.py`
**수정**:
1. `generate_scripts()` 함수의 최상단 (스크립트 생성 로직 시작 전)에서 conftest.py를 무조건 확인·생성:
```python
# 함수 시작 직후, 다른 로직 전에:
scripts_dir = project_dir / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)
conftest_path = scripts_dir / "conftest.py"
if not conftest_path.exists():
    from testforge.scripts.playwright import PLAYWRIGHT_CONFTEST_PY
    conftest_path.write_text(PLAYWRIGHT_CONFTEST_PY, encoding="utf-8")
```
2. `PLAYWRIGHT_CONFTEST_PY` 상수가 `src/testforge/scripts/playwright.py`에 정의되어 있는지 확인. 없으면 생성:
```python
PLAYWRIGHT_CONFTEST_PY = '''"""Playwright fixtures for TestForge generated scripts."""
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser():
    """Launch browser once per test session."""
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            yield browser
            browser.close()
    except Exception:
        pytest.skip("Playwright not installed or browser not available")

@pytest.fixture
def page(browser):
    """Create a new page for each test."""
    page = browser.new_page()
    yield page
    page.close()
'''
```
3. **중요**: `pytest.skip` 사용으로 Playwright 미설치 시 graceful skip 처리

### Task 0B: 실행 전 Playwright 사전 체크

**파일**: `src/testforge/execution/runner.py`
**수정**: `run_tests()` 함수 시작부에 사전 체크 추가:
```python
# scripts 디스커버리 후, 실행 전에:
conftest = scripts_dir / "conftest.py"
if not conftest.exists():
    # Auto-create from generator if available
    try:
        from testforge.scripts.playwright import PLAYWRIGHT_CONFTEST_PY
        conftest.write_text(PLAYWRIGHT_CONFTEST_PY, encoding="utf-8")
    except ImportError:
        pass
```

### Task 0C: 도그푸딩 프로젝트 구조 정비

**문제**: `TestForge Self-Test/`와 `AgentHive QA/`에 `.testforge/config.yaml`이 없음. 정식 프로젝트가 아님.

**파일**: 새 파일 생성 (3개)

1. `TestForge Self-Test/.testforge/config.yaml`:
```yaml
project_name: "TestForge Self-Test"
version: "0.3.0"
llm_provider: anthropic
llm_model: ""
input_dir: inputs
output_dir: output
evidence_dir: evidence
cases_dir: cases
analysis_dir: analysis
extra: {}
```

2. `AgentHive QA/.testforge/config.yaml`:
```yaml
project_name: "AgentHive QA"
version: "0.3.0"
llm_provider: anthropic
llm_model: ""
input_dir: inputs
output_dir: output
evidence_dir: evidence
cases_dir: cases
analysis_dir: analysis
extra: {}
```

3. `Health Device QA/.testforge/config.yaml`:
```yaml
project_name: "Health Device QA"
version: "0.3.0"
llm_provider: anthropic
llm_model: ""
input_dir: inputs
output_dir: output
evidence_dir: evidence
cases_dir: cases
analysis_dir: analysis
extra: {}
```

또한 각 프로젝트의 `scripts/` 디렉토리에 conftest.py가 없으면 생성 (Task 0A의 상수 사용).

---

## Phase 1: CLI 도그푸딩 (병렬 3개)

### Task 1A: CLI 파이프라인 전체 실행 + 검증 스크립트

**파일**: `tests/selftest/test_cli_dogfood.py` (신규)

이 파일은 `.venv/bin/python -m pytest tests/selftest/test_cli_dogfood.py -v`로 실행되는 실제 pytest 테스트 파일.
`tmp_path` fixture로 격리된 임시 프로젝트에서 전체 CLI 파이프라인을 실행.

```python
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
        [*TESTFORGE, "init", name, "-d", str(tmp_path), "--no-llm"],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, f"init failed: {result.stderr}"
    project_dir = tmp_path / name

    # Create a sample input document
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
        [*TESTFORGE, "analyze", str(dog_project), "--no-llm"],
        capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, f"analyze failed: {result.stderr}"
    analysis_path = dog_project / "analysis" / "analysis.json"
    assert analysis_path.exists()
    data = json.loads(analysis_path.read_text())
    assert len(data.get("features", [])) > 0

def test_cli_generate(dog_project):
    """testforge generate creates test cases."""
    # Ensure analysis exists first
    subprocess.run([*TESTFORGE, "analyze", str(dog_project), "--no-llm"],
                   capture_output=True, text=True, timeout=60)
    result = subprocess.run(
        [*TESTFORGE, "generate", str(dog_project), "--no-llm"],
        capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, f"generate failed: {result.stderr}"
    cases_path = dog_project / "cases" / "cases.json"
    assert cases_path.exists()
    cases = json.loads(cases_path.read_text())
    assert len(cases) > 0
    # Verify schema
    for c in cases:
        assert "id" in c
        assert "title" in c
        assert "steps" in c
        assert isinstance(c["steps"], list)

def test_cli_script(dog_project):
    """testforge script generates Playwright scripts + conftest.py."""
    subprocess.run([*TESTFORGE, "analyze", str(dog_project), "--no-llm"],
                   capture_output=True, text=True, timeout=60)
    subprocess.run([*TESTFORGE, "generate", str(dog_project), "--no-llm"],
                   capture_output=True, text=True, timeout=60)
    result = subprocess.run(
        [*TESTFORGE, "script", str(dog_project), "--no-llm"],
        capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, f"script failed: {result.stderr}"
    scripts_dir = dog_project / "scripts"
    assert scripts_dir.exists()
    scripts = list(scripts_dir.glob("test_*.py"))
    assert len(scripts) > 0
    # conftest.py must be auto-created
    assert (scripts_dir / "conftest.py").exists(), "conftest.py not auto-created!"

def test_cli_run_no_playwright(dog_project):
    """testforge run handles missing Playwright gracefully."""
    subprocess.run([*TESTFORGE, "analyze", str(dog_project), "--no-llm"],
                   capture_output=True, text=True, timeout=60)
    subprocess.run([*TESTFORGE, "generate", str(dog_project), "--no-llm"],
                   capture_output=True, text=True, timeout=60)
    subprocess.run([*TESTFORGE, "script", str(dog_project), "--no-llm"],
                   capture_output=True, text=True, timeout=60)
    result = subprocess.run(
        [*TESTFORGE, "run", str(dog_project)],
        capture_output=True, text=True, timeout=120
    )
    # Should not crash — either passes (if Playwright installed) or fails gracefully
    # returncode 0 means passed, non-zero means some failed but no crash
    assert result.returncode in (0, 1), f"run crashed: {result.stderr}"

def test_cli_report(dog_project):
    """testforge report generates markdown report."""
    # Run minimal pipeline
    subprocess.run([*TESTFORGE, "analyze", str(dog_project), "--no-llm"],
                   capture_output=True, text=True, timeout=60)
    subprocess.run([*TESTFORGE, "generate", str(dog_project), "--no-llm"],
                   capture_output=True, text=True, timeout=60)
    result = subprocess.run(
        [*TESTFORGE, "report", str(dog_project)],
        capture_output=True, text=True, timeout=60
    )
    # report may fail if no run results, that's OK — just shouldn't crash
    assert result.returncode in (0, 1), f"report crashed: {result.stderr}"

def test_cli_coverage(dog_project):
    """testforge coverage shows feature coverage."""
    subprocess.run([*TESTFORGE, "analyze", str(dog_project), "--no-llm"],
                   capture_output=True, text=True, timeout=60)
    subprocess.run([*TESTFORGE, "generate", str(dog_project), "--no-llm"],
                   capture_output=True, text=True, timeout=60)
    result = subprocess.run(
        [*TESTFORGE, "coverage", str(dog_project)],
        capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, f"coverage failed: {result.stderr}"

def test_cli_manual_workflow(dog_project):
    """testforge manual start/check/progress/finish works end-to-end."""
    subprocess.run([*TESTFORGE, "analyze", str(dog_project), "--no-llm"],
                   capture_output=True, text=True, timeout=60)
    subprocess.run([*TESTFORGE, "generate", str(dog_project), "--no-llm"],
                   capture_output=True, text=True, timeout=60)
    # Start
    r = subprocess.run([*TESTFORGE, "manual", "start", str(dog_project), "-y"],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"manual start failed: {r.stderr}"
    # Progress
    r = subprocess.run([*TESTFORGE, "manual", "progress", str(dog_project)],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0
    # Finish
    r = subprocess.run([*TESTFORGE, "manual", "finish", str(dog_project), "-y"],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0

def test_cli_pipeline_full(dog_project):
    """testforge pipeline runs all stages end-to-end."""
    result = subprocess.run(
        [*TESTFORGE, "--no-llm", "pipeline", str(dog_project)],
        capture_output=True, text=True, timeout=180
    )
    # Pipeline may have partial failures (e.g., Playwright not installed)
    # but should not crash with unhandled exception
    assert "Traceback" not in result.stderr or result.returncode in (0, 1)

def test_cli_projects_list(dog_project):
    """testforge projects lists the dogfood project."""
    result = subprocess.run(
        [*TESTFORGE, "projects"],
        capture_output=True, text=True, timeout=30,
        cwd=str(dog_project.parent)
    )
    assert result.returncode == 0
```

**검증**: `.venv/bin/python -m pytest tests/selftest/test_cli_dogfood.py -v --tb=short`

### Task 1B: GUI API 통합 도그푸딩 테스트

**파일**: `tests/selftest/test_gui_dogfood.py` (신규)

GUI를 통한 전체 사용자 여정을 API 레벨에서 테스트 (실제 브라우저 불필요).

```python
"""TestForge GUI dogfooding — full user journey via API."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from testforge.core.project import create_project, save_analysis, save_cases, AnalysisResult, Feature, Persona, BusinessRule
from testforge.web.app import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def gui_project(tmp_path):
    """Create a fully populated project for GUI testing."""
    p = tmp_path / "gui-dogfood"
    create_project(p)

    # Stage 1: Add input files
    inputs = p / "inputs"
    (inputs / "spec.md").write_text("# Login\nUsers login with email.\n## Rules\nPassword >= 8 chars.")

    # Stage 2: Populate analysis
    analysis = AnalysisResult(
        features=[
            Feature(id="F-001", name="Login", description="User authentication", category="auth", priority="high"),
            Feature(id="F-002", name="Dashboard", description="Main view", category="ui", priority="medium"),
        ],
        personas=[
            Persona(id="P-001", name="Admin", description="Full access user", tech_level="advanced"),
        ],
        rules=[
            BusinessRule(id="R-001", name="Password policy", description="Min 8 chars", condition="password.length >= 8", expected_behavior="Accept login"),
        ],
    )
    save_analysis(p, analysis)

    # Stage 3: Populate cases
    cases = [
        {"id": "TC-F001-01", "title": "Login success", "description": "Valid login", "feature_id": "F-001",
         "type": "functional", "priority": "high", "tags": ["positive"],
         "steps": [{"order": 1, "action": "Enter email", "expected_result": "Field populated"}],
         "preconditions": ["User exists"], "expected_result": "Login success", "rule_ids": ["R-001"]},
        {"id": "TC-F001-02", "title": "Login failure", "description": "Invalid password", "feature_id": "F-001",
         "type": "functional", "priority": "high", "tags": ["negative"],
         "steps": [{"order": 1, "action": "Enter wrong password", "expected_result": "Error shown"}],
         "preconditions": [], "expected_result": "Error message", "rule_ids": ["R-001"]},
        {"id": "TC-F002-01", "title": "Dashboard load", "description": "After login", "feature_id": "F-002",
         "type": "functional", "priority": "medium", "tags": ["positive"],
         "steps": [{"order": 1, "action": "Navigate to dashboard", "expected_result": "Page loads"}],
         "preconditions": ["Logged in"], "expected_result": "Dashboard visible", "rule_ids": []},
    ]
    save_cases(p, cases)

    return p


class TestGUIUserJourney:
    """Tests simulating a QA engineer's complete workflow through the GUI."""

    def test_01_project_appears_in_list(self, client, gui_project):
        r = client.get(f"/api/projects?directory={gui_project.parent}")
        assert r.status_code == 200
        projects = r.json()["projects"]
        assert any(p["name"] == "gui-dogfood" for p in projects)

    def test_02_project_overview(self, client, gui_project):
        r = client.get(f"/api/projects/{gui_project}/overview")
        assert r.status_code == 200
        pipeline = r.json()["pipeline"]
        assert pipeline[0]["stage"] == "inputs"
        assert pipeline[1]["status"] == "done"  # analysis exists

    def test_03_inputs_listed(self, client, gui_project):
        r = client.get(f"/api/projects/{gui_project}/inputs")
        assert r.status_code == 200
        assert len(r.json()["inputs"]) == 1

    def test_04_analysis_loaded(self, client, gui_project):
        r = client.get(f"/api/projects/{gui_project}/analysis")
        assert r.status_code == 200
        data = r.json()["analysis"]
        assert len(data["features"]) == 2
        assert len(data["personas"]) == 1
        assert len(data["rules"]) == 1

    def test_05_add_feature_via_gui(self, client, gui_project):
        r = client.post(f"/api/projects/{gui_project}/analysis/features",
                        json={"name": "Registration", "description": "New user signup", "category": "auth", "priority": "medium"})
        assert r.status_code == 200
        assert r.json()["feature"]["name"] == "Registration"
        # Verify it's in the list
        r2 = client.get(f"/api/projects/{gui_project}/analysis")
        assert len(r2.json()["analysis"]["features"]) == 3

    def test_06_edit_feature_via_gui(self, client, gui_project):
        r = client.put(f"/api/projects/{gui_project}/analysis/features/F-001",
                       json={"name": "Login (Updated)", "priority": "critical"})
        assert r.status_code == 200
        assert r.json()["feature"]["name"] == "Login (Updated)"

    def test_07_delete_feature_via_gui(self, client, gui_project):
        # Add then delete
        client.post(f"/api/projects/{gui_project}/analysis/features",
                    json={"name": "Temp", "description": "To be deleted"})
        r = client.get(f"/api/projects/{gui_project}/analysis")
        temp_id = [f for f in r.json()["analysis"]["features"] if f["name"] == "Temp"][0]["id"]
        r = client.delete(f"/api/projects/{gui_project}/analysis/features/{temp_id}")
        assert r.status_code == 200

    def test_08_cases_loaded(self, client, gui_project):
        r = client.get(f"/api/projects/{gui_project}/cases")
        assert r.status_code == 200
        assert r.json()["count"] == 3

    def test_09_add_case_via_gui(self, client, gui_project):
        r = client.post(f"/api/projects/{gui_project}/cases/item", json={
            "title": "Logout flow", "description": "User clicks logout",
            "type": "functional", "priority": "low", "feature_id": "F-001",
            "tags": ["positive"], "steps": [{"order": 1, "action": "Click logout", "expected_result": "Redirected to login"}],
            "expected_result": "Session ended"
        })
        assert r.status_code == 200
        assert "TC-" in r.json()["case"]["id"]

    def test_10_edit_case_via_gui(self, client, gui_project):
        r = client.put(f"/api/projects/{gui_project}/cases/item/TC-F001-01",
                       json={"title": "Login success (updated)", "priority": "critical"})
        assert r.status_code == 200

    def test_11_delete_case_via_gui(self, client, gui_project):
        r = client.delete(f"/api/projects/{gui_project}/cases/item/TC-F001-02")
        assert r.status_code == 200

    def test_12_bulk_delete_cases(self, client, gui_project):
        r = client.post(f"/api/projects/{gui_project}/cases/bulk-delete",
                        json={"case_ids": ["TC-F002-01"]})
        assert r.status_code == 200

    def test_13_generate_scripts(self, client, gui_project):
        r = client.post(f"/api/projects/{gui_project}/scripts",
                        json={"no_llm": True})
        assert r.status_code == 200

    def test_14_scripts_listed_with_mappings(self, client, gui_project):
        # Generate first
        client.post(f"/api/projects/{gui_project}/scripts", json={"no_llm": True})
        r = client.get(f"/api/projects/{gui_project}/scripts")
        assert r.status_code == 200
        scripts = r.json()["scripts"]
        assert len(scripts) > 0
        # Check mapping info present
        for s in scripts:
            assert "mapped_cases" in s

    def test_15_script_code_viewable(self, client, gui_project):
        client.post(f"/api/projects/{gui_project}/scripts", json={"no_llm": True})
        r = client.get(f"/api/projects/{gui_project}/scripts")
        name = r.json()["scripts"][0]["name"]
        r2 = client.get(f"/api/projects/{gui_project}/scripts/{name}")
        assert r2.status_code == 200
        assert "def test_" in r2.json()["content"]

    def test_16_script_editable(self, client, gui_project):
        client.post(f"/api/projects/{gui_project}/scripts", json={"no_llm": True})
        r = client.get(f"/api/projects/{gui_project}/scripts")
        name = r.json()["scripts"][0]["name"]
        r2 = client.put(f"/api/projects/{gui_project}/scripts/{name}",
                        json={"content": "# edited\ndef test_edited(): pass\n"})
        assert r2.status_code == 200

    def test_17_case_script_drilldown(self, client, gui_project):
        client.post(f"/api/projects/{gui_project}/scripts", json={"no_llm": True})
        r = client.get(f"/api/projects/{gui_project}/cases/TC-F001-01/scripts")
        assert r.status_code == 200
        # May be empty if mapping didn't match, but endpoint works

    def test_18_run_tests(self, client, gui_project):
        client.post(f"/api/projects/{gui_project}/scripts", json={"no_llm": True})
        r = client.post(f"/api/projects/{gui_project}/run", json={"parallel": 1})
        assert r.status_code == 200
        run = r.json()["run"]
        assert "run_id" in run
        assert "results" in run

    def test_19_run_history(self, client, gui_project):
        client.post(f"/api/projects/{gui_project}/scripts", json={"no_llm": True})
        client.post(f"/api/projects/{gui_project}/run", json={"parallel": 1})
        r = client.get(f"/api/projects/{gui_project}/runs")
        assert r.status_code == 200
        assert len(r.json()["runs"]) > 0

    def test_20_run_detail_by_id(self, client, gui_project):
        client.post(f"/api/projects/{gui_project}/scripts", json={"no_llm": True})
        run_resp = client.post(f"/api/projects/{gui_project}/run", json={"parallel": 1})
        run_id = run_resp.json()["run"]["run_id"]
        r = client.get(f"/api/projects/{gui_project}/runs/{run_id}")
        assert r.status_code == 200
        data = r.json()["run"]
        # Verify full failure data is present
        for result in data["results"]:
            assert "script_name" in result
            assert "stderr" in result
            assert "returncode" in result

    def test_21_generate_report(self, client, gui_project):
        client.post(f"/api/projects/{gui_project}/scripts", json={"no_llm": True})
        client.post(f"/api/projects/{gui_project}/run", json={"parallel": 1})
        r = client.post(f"/api/projects/{gui_project}/report?fmt=markdown")
        assert r.status_code == 200
        assert "report_id" in r.json()

    def test_22_report_history(self, client, gui_project):
        client.post(f"/api/projects/{gui_project}/scripts", json={"no_llm": True})
        client.post(f"/api/projects/{gui_project}/run", json={"parallel": 1})
        client.post(f"/api/projects/{gui_project}/report?fmt=markdown")
        r = client.get(f"/api/projects/{gui_project}/reports")
        assert r.status_code == 200
        assert len(r.json()["reports"]) > 0

    def test_23_coverage(self, client, gui_project):
        r = client.get(f"/api/projects/{gui_project}/coverage")
        assert r.status_code == 200
        cov = r.json()["coverage"]
        assert "feature_coverage_pct" in cov

    def test_24_manual_qa_full_cycle(self, client, gui_project):
        # Start session
        r = client.post(f"/api/projects/{gui_project}/manual/start")
        assert r.status_code == 200
        items = r.json().get("items", r.json().get("checklist", []))
        if items:
            item_id = items[0].get("id", items[0].get("item_id", "CL-001"))
            # Check item
            client.put(f"/api/projects/{gui_project}/manual/check/{item_id}",
                       json={"status": "pass", "note": "Dogfood test"})
        # Progress
        r = client.get(f"/api/projects/{gui_project}/manual/progress")
        assert r.status_code == 200
        # Finish
        r = client.post(f"/api/projects/{gui_project}/manual/finish")
        assert r.status_code == 200

    def test_25_manual_session_history(self, client, gui_project):
        # Run a session first
        client.post(f"/api/projects/{gui_project}/manual/start")
        client.post(f"/api/projects/{gui_project}/manual/finish")
        r = client.get(f"/api/projects/{gui_project}/manual/sessions")
        assert r.status_code == 200

    def test_26_llm_config_roundtrip(self, client, gui_project):
        # Get
        r = client.get(f"/api/projects/{gui_project}/config")
        assert r.status_code == 200
        # Update
        r = client.put(f"/api/projects/{gui_project}/config",
                       json={"llm_provider": "ollama", "llm_model": "llama3"})
        assert r.status_code == 200
        # Verify
        r = client.get(f"/api/projects/{gui_project}/config")
        assert r.json()["config"]["llm_provider"] == "ollama"
        assert r.json()["config"]["llm_model"] == "llama3"

    def test_27_translation_policy(self, client, gui_project):
        r = client.get(f"/api/projects/{gui_project}/translate/status")
        assert r.status_code == 200
        assert r.json()["translation_policy"] == "source_plus_translation_job"

    def test_28_export_cases_data(self, client, gui_project):
        """Verify cases endpoint returns exportable data."""
        r = client.get(f"/api/projects/{gui_project}/cases")
        assert r.status_code == 200
        cases = r.json()["cases"]
        # Every case must have the required schema
        for c in cases:
            assert "id" in c
            assert "title" in c
            assert "steps" in c
```

**검증**: `.venv/bin/python -m pytest tests/selftest/test_gui_dogfood.py -v --tb=short`

### Task 1C: README 정확도 수정

**파일**: `README.md`

현재 거짓 주장:
1. L237 "Ollama — Coming in v0.2" → Ollama는 이미 구현됨. "Ollama (Local)" 으로 변경.
2. L40 "Flexible execution: Browser, HTTP, Shell, SSH" → 현재 Playwright만 구현. 정확히:
   "Flexible execution: Browser-based testing via Playwright (HTTP, Shell, SSH connectors planned)"
3. L38 "Script generation: Playwright, HTTP, Shell" → 현재 Playwright만 구현:
   "Script generation: Playwright (more frameworks planned)"
4. L41 "HAR traces" → HAR 수집 미구현. 삭제하거나 "planned" 표기.

기존 README 전체 구조는 유지. 위 4곳만 정확하게 수정.

---

## Phase 2: 발견 이슈 수정 + 에지 케이스 강화 (병렬 3개)

### Task 2A: Persona/Rule UPDATE/DELETE 테스트 추가

**파일**: `tests/test_web.py`

현재 persona/rule에 대해 create만 테스트됨. update/delete 추가:

```python
def test_update_persona(web_client, sample_project):
    r = web_client.put(f"/api/projects/{sample_project}/analysis/personas/P-001",
                       json={"name": "Updated Admin", "tech_level": "beginner"})
    assert r.status_code == 200
    assert r.json()["persona"]["name"] == "Updated Admin"

def test_delete_persona(web_client, sample_project):
    r = web_client.delete(f"/api/projects/{sample_project}/analysis/personas/P-001")
    assert r.status_code == 200

def test_update_rule(web_client, sample_project):
    r = web_client.put(f"/api/projects/{sample_project}/analysis/rules/R-001",
                       json={"name": "Updated Rule", "condition": "x > 10"})
    assert r.status_code == 200

def test_delete_rule(web_client, sample_project):
    r = web_client.delete(f"/api/projects/{sample_project}/analysis/rules/R-001")
    assert r.status_code == 200

def test_delete_persona_not_found(web_client, sample_project):
    r = web_client.delete(f"/api/projects/{sample_project}/analysis/personas/NOPE")
    assert r.status_code == 404

def test_delete_rule_not_found(web_client, sample_project):
    r = web_client.delete(f"/api/projects/{sample_project}/analysis/rules/NOPE")
    assert r.status_code == 404
```

### Task 2B: 파일 업로드 테스트 추가

**파일**: `tests/test_web.py`

```python
def test_file_upload(web_client, sample_project):
    """Test multipart file upload via GUI."""
    r = web_client.post(
        f"/api/projects/{sample_project}/inputs",
        files={"file": ("test-doc.md", b"# Test Document\nSome content.", "text/markdown")},
    )
    assert r.status_code == 200
    # Verify file appears in list
    r2 = web_client.get(f"/api/projects/{sample_project}/inputs")
    names = [i["name"] for i in r2.json()["inputs"]]
    assert "test-doc.md" in names

def test_file_upload_duplicate(web_client, sample_project):
    """Upload same filename twice should overwrite or error gracefully."""
    web_client.post(f"/api/projects/{sample_project}/inputs",
                    files={"file": ("dup.md", b"# First", "text/markdown")})
    r = web_client.post(f"/api/projects/{sample_project}/inputs",
                        files={"file": ("dup.md", b"# Second", "text/markdown")})
    # Should succeed (overwrite) or return meaningful error
    assert r.status_code in (200, 409)
```

### Task 2C: tag 필터링 + 병렬 실행 테스트

**파일**: `tests/test_web.py`

```python
def test_run_with_tags(web_client, sample_project):
    """Run only scripts matching tag filter."""
    # Create scripts first
    web_client.post(f"/api/projects/{sample_project}/scripts", json={"no_llm": True})
    r = web_client.post(f"/api/projects/{sample_project}/run",
                        json={"tags": ["nonexistent_tag"], "parallel": 1})
    assert r.status_code == 200
    # No scripts should match
    assert r.json()["run"]["summary"]["total"] == 0

def test_run_parallel(web_client, sample_project):
    """Run with parallel > 1 doesn't crash."""
    web_client.post(f"/api/projects/{sample_project}/scripts", json={"no_llm": True})
    r = web_client.post(f"/api/projects/{sample_project}/run",
                        json={"parallel": 2})
    assert r.status_code == 200
```

---

## Phase 3: Hive 동기화 + 검증 + 커밋 (순차)

### Task 3A: Hive BACKLOG.md 업데이트

**파일**: `~/.agenthive/projects/Users--user--_--workspace--nts-ai/testforge/tasks/BACKLOG.md`

```markdown
# Task Index — TestForge

## Done (v0.3 + v0.4 도그푸딩)
- TASK-001~021 | v0.3 전체 완료 | ✅
- TASK-022 | conftest.py 자동 생성 보장 | ✅ v0.4
- TASK-023 | CLI 도그푸딩 테스트 12개 | ✅ v0.4
- TASK-024 | GUI 도그푸딩 테스트 28개 | ✅ v0.4
- TASK-025 | README 정확도 수정 | ✅ v0.4
- TASK-026 | Persona/Rule CRUD 테스트 | ✅ v0.4
- TASK-027 | 파일 업로드 테스트 | ✅ v0.4
- TASK-028 | Tag 필터링/병렬 실행 테스트 | ✅ v0.4
```

### Task 3B: 전체 테스트 실행 검증

**명령** (순차 실행):
```bash
# 1. 기존 API 테스트
.venv/bin/python -m pytest tests/test_web.py -v --tb=short
# 2. CLI 도그푸딩
.venv/bin/python -m pytest tests/selftest/test_cli_dogfood.py -v --tb=short
# 3. GUI 도그푸딩
.venv/bin/python -m pytest tests/selftest/test_gui_dogfood.py -v --tb=short
# 4. 전체
.venv/bin/python -m pytest tests/ -v --tb=short -q
```

**실패 시**: 해당 테스트가 실패하는 원인을 분석하고 코드를 수정. 테스트 자체를 삭제하지 말 것.

### Task 3C: 커밋 + Khala 공지

```bash
git add -A
git commit -m "feat: v0.4 dogfooding — CLI/GUI test suites, conftest fix, README accuracy

- Phase 0: conftest.py auto-creation guaranteed, Playwright pre-check in runner
- Phase 1: 12 CLI dogfooding tests, 28 GUI user journey tests, README fixes
- Phase 2: Persona/Rule CRUD tests, file upload tests, tag/parallel tests
- All tests passing: 65 (API) + 12 (CLI) + 28 (GUI) + 10 (edge cases)

Co-Authored-By: Cursor Agent <noreply@cursor.com>"

# Khala 공지
~/.aria/bin/aria khala publish "plaza/announcements" \
  "[TestForge v0.4 도그푸딩 완료] 전체 테스트: 115+개 통과. CLI 12개 + GUI 28개 + API 75개. conftest 자동생성, README 정확도 수정. commit: $(git rev-parse --short HEAD)"
```

---

## 최종 산출물 체크리스트

- [ ] `.venv/bin/python -m pytest tests/test_web.py -q` → 75+ passed
- [ ] `.venv/bin/python -m pytest tests/selftest/test_cli_dogfood.py -q` → 12 passed
- [ ] `.venv/bin/python -m pytest tests/selftest/test_gui_dogfood.py -q` → 28 passed
- [ ] conftest.py: 스크립트 생성 시 자동 생성됨 (tests/selftest/test_cli_dogfood.py::test_cli_script에서 검증)
- [ ] Playwright 미설치 시 graceful skip (crash 아님)
- [ ] README.md: Ollama "Coming" 제거, HTTP/Shell/SSH "planned" 명시
- [ ] 도그푸딩 프로젝트 3개 모두 .testforge/config.yaml 존재
- [ ] Hive BACKLOG.md 업데이트됨
- [ ] Khala 공지 완료
- [ ] git commit 완료

---

## 참조 파일 경로

| 파일 | 역할 | 작업 |
|------|------|------|
| `src/testforge/scripts/generator.py` | 스크립트 생성기 | conftest 자동 생성 보장 |
| `src/testforge/scripts/playwright.py` | Playwright 템플릿 | CONFTEST 상수 확인 |
| `src/testforge/execution/runner.py` | 테스트 러너 | conftest 사전 체크 추가 |
| `tests/test_web.py` | API 테스트 | persona/rule/upload/tag 테스트 추가 |
| `tests/selftest/test_cli_dogfood.py` | CLI 도그푸딩 | 신규 (12개 테스트) |
| `tests/selftest/test_gui_dogfood.py` | GUI 도그푸딩 | 신규 (28개 테스트) |
| `README.md` | 프로젝트 문서 | 정확도 4곳 수정 |
| `TestForge Self-Test/.testforge/config.yaml` | 프로젝트 설정 | 신규 |
| `AgentHive QA/.testforge/config.yaml` | 프로젝트 설정 | 신규 |
| `Health Device QA/.testforge/config.yaml` | 프로젝트 설정 | 신규 |
