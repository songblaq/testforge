"""TestForge GUI dogfooding — full user journey via API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from testforge.web.app import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def gui_project(tmp_path):
    """Create a fully populated project for GUI testing."""
    from testforge.core.project import (
        AnalysisResult,
        BusinessRule,
        create_project,
        Feature,
        Persona,
        save_analysis,
        save_cases,
    )

    p = tmp_path / "gui-dogfood"
    create_project(p)

    inputs = p / "inputs"
    (inputs / "spec.md").write_text(
        "# Login\nUsers login with email.\n## Rules\nPassword >= 8 chars."
    )

    analysis = AnalysisResult(
        features=[
            Feature(
                id="F-001",
                name="Login",
                description="User authentication",
                category="auth",
                priority="high",
            ),
            Feature(
                id="F-002",
                name="Dashboard",
                description="Main view",
                category="ui",
                priority="medium",
            ),
        ],
        personas=[
            Persona(
                id="P-001",
                name="Admin",
                description="Full access user",
                tech_level="advanced",
            ),
        ],
        rules=[
            BusinessRule(
                id="R-001",
                name="Password policy",
                description="Min 8 chars",
                condition="password.length >= 8",
                expected_behavior="Accept login",
            ),
        ],
    )
    save_analysis(p, analysis)

    cases = [
        {
            "id": "TC-F001-01",
            "title": "Login success",
            "description": "Valid login",
            "feature_id": "F-001",
            "type": "functional",
            "priority": "high",
            "tags": ["positive"],
            "steps": [
                {
                    "order": 1,
                    "action": "Enter email",
                    "expected_result": "Field populated",
                }
            ],
            "preconditions": ["User exists"],
            "expected_result": "Login success",
            "rule_ids": ["R-001"],
        },
        {
            "id": "TC-F001-02",
            "title": "Login failure",
            "description": "Invalid password",
            "feature_id": "F-001",
            "type": "functional",
            "priority": "high",
            "tags": ["negative"],
            "steps": [
                {
                    "order": 1,
                    "action": "Enter wrong password",
                    "expected_result": "Error shown",
                }
            ],
            "preconditions": [],
            "expected_result": "Error message",
            "rule_ids": ["R-001"],
        },
        {
            "id": "TC-F002-01",
            "title": "Dashboard load",
            "description": "After login",
            "feature_id": "F-002",
            "type": "functional",
            "priority": "medium",
            "tags": ["positive"],
            "steps": [
                {
                    "order": 1,
                    "action": "Navigate to dashboard",
                    "expected_result": "Page loads",
                }
            ],
            "preconditions": ["Logged in"],
            "expected_result": "Dashboard visible",
            "rule_ids": [],
        },
    ]
    save_cases(p, cases)

    return p


def _base(p):
    return f"/api/projects/{p}"


class TestGUIUserJourney:
    def test_01_project_appears_in_list(self, client, gui_project):
        parent = str(gui_project.parent)
        resp = client.get("/api/projects", params={"directory": parent})
        assert resp.status_code == 200
        data = resp.json()
        names = {proj["name"] for proj in data["projects"]}
        assert "gui-dogfood" in names

    def test_02_project_overview(self, client, gui_project):
        resp = client.get(f"{_base(gui_project)}/overview")
        assert resp.status_code == 200
        body = resp.json()
        assert body["project_name"]
        assert body["project_path"] == str(gui_project.resolve())
        stages = {s["stage"] for s in body["pipeline"]}
        assert stages >= {"inputs", "analysis", "cases", "scripts", "execution", "report"}

    def test_03_inputs_listed(self, client, gui_project):
        resp = client.get(f"{_base(gui_project)}/inputs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        names = {f["name"] for f in data["files"]}
        assert "spec.md" in names

    def test_04_analysis_loaded(self, client, gui_project):
        resp = client.get(f"{_base(gui_project)}/analysis")
        assert resp.status_code == 200
        analysis = resp.json()["analysis"]
        assert len(analysis["features"]) == 2
        assert len(analysis["personas"]) == 1
        assert len(analysis["rules"]) == 1

    def test_05_add_feature_via_gui(self, client, gui_project):
        resp = client.post(
            f"{_base(gui_project)}/analysis/features",
            json={
                "id": "F-900",
                "name": "MFA",
                "description": "Second factor",
                "category": "auth",
                "priority": "high",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["feature"]["id"] == "F-900"
        assert resp.json()["feature"]["name"] == "MFA"

    def test_06_edit_feature(self, client, gui_project):
        resp = client.put(
            f"{_base(gui_project)}/analysis/features/F-001",
            json={"name": "Login (updated)", "description": "Auth flow"},
        )
        assert resp.status_code == 200
        feat = resp.json()["feature"]
        assert feat["id"] == "F-001"
        assert feat["name"] == "Login (updated)"

    def test_07_delete_feature_post_then_delete(self, client, gui_project):
        add = client.post(
            f"{_base(gui_project)}/analysis/features",
            json={"name": "Disposable", "description": "to remove"},
        )
        assert add.status_code == 200
        fid = add.json()["feature"]["id"]
        delete = client.delete(f"{_base(gui_project)}/analysis/features/{fid}")
        assert delete.status_code == 200
        assert delete.json()["deleted"] == fid
        listed = client.get(f"{_base(gui_project)}/analysis")
        ids = {f["id"] for f in listed.json()["analysis"]["features"]}
        assert fid not in ids

    def test_08_cases_loaded(self, client, gui_project):
        resp = client.get(f"{_base(gui_project)}/cases")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 3
        assert len(data["cases"]) == 3

    def test_09_add_case(self, client, gui_project):
        resp = client.post(
            f"{_base(gui_project)}/cases/item",
            json={
                "title": "New manual case",
                "description": "Added via API",
                "feature_id": "F-002",
                "priority": "low",
                "type": "functional",
                "tags": ["api"],
                "preconditions": [],
                "steps": [
                    {
                        "order": "1",
                        "action": "Do thing",
                        "expected_result": "Done",
                    }
                ],
                "expected_result": "OK",
                "rule_ids": [],
            },
        )
        assert resp.status_code == 200
        case = resp.json()["case"]
        assert case["title"] == "New manual case"
        assert case["id"].startswith("TC-")

    def test_10_edit_case(self, client, gui_project):
        resp = client.put(
            f"{_base(gui_project)}/cases/item/TC-F001-01",
            json={"title": "Login success (edited)", "priority": "medium"},
        )
        assert resp.status_code == 200
        assert resp.json()["case"]["title"] == "Login success (edited)"

    def test_11_delete_case(self, client, gui_project):
        resp = client.delete(f"{_base(gui_project)}/cases/item/TC-F001-02")
        assert resp.status_code == 200
        assert resp.json()["deleted"] == "TC-F001-02"
        count = client.get(f"{_base(gui_project)}/cases").json()["count"]
        assert count == 2

    def test_12_bulk_delete_cases(self, client, gui_project):
        resp = client.post(
            f"{_base(gui_project)}/cases/bulk-delete",
            json={"case_ids": ["TC-F001-01", "TC-F002-01"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["deleted_count"] == 2
        assert body["remaining"] == 1

    def test_13_generate_scripts(self, client, gui_project):
        resp = client.post(
            f"{_base(gui_project)}/scripts",
            json={"no_llm": True},
        )
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_14_scripts_listed_with_mappings(self, client, gui_project):
        client.post(f"{_base(gui_project)}/scripts", json={"no_llm": True})
        resp = client.get(f"{_base(gui_project)}/scripts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        for s in data["scripts"]:
            assert "name" in s
            assert "mapped_cases" in s

    def test_15_script_code_viewable(self, client, gui_project):
        client.post(f"{_base(gui_project)}/scripts", json={"no_llm": True})
        listed = client.get(f"{_base(gui_project)}/scripts").json()["scripts"]
        assert listed
        name = listed[0]["name"]
        resp = client.get(f"{_base(gui_project)}/scripts/{name}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == name
        assert "content" in body
        assert body["lines"] >= 0

    def test_16_script_editable(self, client, gui_project):
        client.post(f"{_base(gui_project)}/scripts", json={"no_llm": True})
        listed = client.get(f"{_base(gui_project)}/scripts").json()["scripts"]
        assert listed
        name = listed[0]["name"]
        new_src = "# dogfood edit\nprint('ok')\n"
        resp = client.put(
            f"{_base(gui_project)}/scripts/{name}",
            json={"content": new_src},
        )
        assert resp.status_code == 200
        assert resp.json()["lines"] == len(new_src.splitlines())

    def test_17_case_script_drilldown(self, client, gui_project):
        client.post(f"{_base(gui_project)}/scripts", json={"no_llm": True})
        resp = client.get(f"{_base(gui_project)}/cases/TC-F001-01/scripts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_id"] == "TC-F001-01"
        assert "scripts" in data
        assert "count" in data

    def test_18_run_tests(self, client, gui_project):
        client.post(f"{_base(gui_project)}/scripts", json={"no_llm": True})
        try:
            resp = client.post(
                f"{_base(gui_project)}/run",
                json={"tags": [], "parallel": 1},
            )
        except FileNotFoundError:
            pytest.skip("python binary not available in test environment")
        assert resp.status_code == 200
        run = resp.json()["run"]
        assert "run_id" in run
        assert "summary" in run
        assert "results" in run

    def test_19_run_history(self, client, gui_project):
        client.post(f"{_base(gui_project)}/scripts", json={"no_llm": True})
        try:
            client.post(
                f"{_base(gui_project)}/run",
                json={"tags": [], "parallel": 1},
            )
        except FileNotFoundError:
            pytest.skip("python binary not available in test environment")
        resp = client.get(f"{_base(gui_project)}/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        assert data["runs"][0].get("run_id")

    def test_20_run_detail_by_id(self, client, gui_project):
        client.post(f"{_base(gui_project)}/scripts", json={"no_llm": True})
        try:
            run_resp = client.post(
                f"{_base(gui_project)}/run",
                json={"tags": [], "parallel": 1},
            )
        except FileNotFoundError:
            pytest.skip("python binary not available in test environment")
        run_id = run_resp.json()["run"]["run_id"]
        resp = client.get(f"{_base(gui_project)}/runs/{run_id}")
        assert resp.status_code == 200
        assert resp.json()["run"]["run_id"] == run_id

    def test_21_generate_report(self, client, gui_project):
        resp = client.post(f"{_base(gui_project)}/report?fmt=markdown")
        assert resp.status_code == 200
        body = resp.json()
        assert body["format"] == "markdown"
        assert body["report"]
        assert "report_id" in body

    def test_22_report_history(self, client, gui_project):
        client.post(f"{_base(gui_project)}/report?fmt=markdown")
        resp = client.get(f"{_base(gui_project)}/reports")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        assert data["reports"][0].get("report_id")

    def test_23_coverage(self, client, gui_project):
        resp = client.get(f"{_base(gui_project)}/coverage")
        assert resp.status_code == 200
        cov = resp.json()["coverage"]
        assert cov["total_features"] == 2
        assert cov["total_rules"] == 1
        assert "feature_coverage_pct" in cov
        assert "rule_coverage_pct" in cov

    def test_24_manual_qa_full_cycle(self, client, gui_project):
        start = client.post(
            f"{_base(gui_project)}/manual/start",
            json={"no_llm": True},
        )
        assert start.status_code == 200
        items = start.json()["items"]
        assert items
        item_id = items[0]["id"]
        chk = client.put(
            f"{_base(gui_project)}/manual/check/{item_id}",
            json={"status": "pass", "note": "dogfood"},
        )
        assert chk.status_code == 200
        prog = client.get(f"{_base(gui_project)}/manual/progress")
        assert prog.status_code == 200
        assert prog.json()["progress"]["checked"] >= 1
        fin = client.post(f"{_base(gui_project)}/manual/finish")
        assert fin.status_code == 200
        assert "report_path" in fin.json()

    def test_25_manual_session_history(self, client, gui_project):
        items = client.post(
            f"{_base(gui_project)}/manual/start",
            json={"no_llm": True},
        ).json()["items"]
        item_id = items[0]["id"]
        client.put(
            f"{_base(gui_project)}/manual/check/{item_id}",
            json={"status": "pass", "note": ""},
        )
        client.post(f"{_base(gui_project)}/manual/finish")
        resp = client.get(f"{_base(gui_project)}/manual/sessions")
        assert resp.status_code == 200
        sessions = resp.json()["sessions"]
        assert len(sessions) >= 1

    def test_26_llm_config_roundtrip(self, client, gui_project):
        g = client.get(f"{_base(gui_project)}/config")
        assert g.status_code == 200
        orig = g.json()["config"]
        u = client.put(
            f"{_base(gui_project)}/config",
            json={"llm_provider": "openai", "llm_model": "gpt-4o-mini"},
        )
        assert u.status_code == 200
        assert u.json()["config"]["llm_provider"] == "openai"
        g2 = client.get(f"{_base(gui_project)}/config")
        assert g2.json()["config"]["llm_model"] == "gpt-4o-mini"
        client.put(
            f"{_base(gui_project)}/config",
            json={
                "llm_provider": orig.get("llm_provider", "anthropic"),
                "llm_model": orig.get("llm_model") or "",
            },
        )

    def test_27_translation_policy(self, client, gui_project):
        resp = client.get(f"{_base(gui_project)}/translate/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["translation_policy"] == "source_plus_translation_job"
        assert "supported_languages" in body
        assert "status" in body
        for lang in ("ko", "en", "vi"):
            assert lang in body["status"]
            assert "cases" in body["status"][lang]
            assert "analysis" in body["status"][lang]

    def test_28_export_cases_schema(self, client, gui_project):
        resp = client.get(f"{_base(gui_project)}/cases")
        assert resp.status_code == 200
        data = resp.json()
        assert "cases" in data
        assert "count" in data
        assert data["count"] == len(data["cases"])
        for c in data["cases"]:
            assert isinstance(c.get("id"), str) and c["id"]
            assert "title" in c
            assert "feature_id" in c
