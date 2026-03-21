#!/usr/bin/env python3
"""F-003: Test testforge generate creates test cases from analysis."""
import json
import os
import subprocess
import sys
import tempfile


def main():
    testforge = os.path.join(os.path.dirname(sys.executable), "testforge")
    with tempfile.TemporaryDirectory() as tmpdir:
        project = os.path.join(tmpdir, "test-proj")
        subprocess.run(
            [testforge, "init", "test-proj", "--directory", tmpdir],
            capture_output=True, text=True, check=True,
        )

        # Write pre-built analysis
        analysis_dir = os.path.join(project, "analysis")
        os.makedirs(analysis_dir, exist_ok=True)
        analysis = {
            "features": [
                {"id": "F-001", "name": "Login", "description": "User login", "category": "auth",
                 "priority": "high", "screens": [], "tags": [], "source": ""},
                {"id": "F-002", "name": "Dashboard", "description": "Main dashboard", "category": "ui",
                 "priority": "medium", "screens": [], "tags": [], "source": ""},
            ],
            "screens": [],
            "personas": [
                {"id": "P-001", "name": "User", "description": "End user",
                 "goals": [], "pain_points": [], "tech_level": "intermediate"},
            ],
            "rules": [],
            "raw_sources": [],
        }
        with open(os.path.join(analysis_dir, "analysis.json"), "w") as f:
            json.dump(analysis, f)

        result = subprocess.run(
            [testforge, "generate", project],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"FAIL: generate exited with code {result.returncode}")
            print(result.stderr)
            sys.exit(1)

        cases_path = os.path.join(project, "cases", "cases.json")
        if not os.path.isfile(cases_path):
            print("FAIL: cases/cases.json not created")
            sys.exit(1)

        with open(cases_path) as f:
            cases = json.load(f)

        if not isinstance(cases, list) or len(cases) == 0:
            print("FAIL: no test cases generated")
            sys.exit(1)

        # Check we have functional, usecase, and checklist cases
        ids = [c.get("id", "") for c in cases]
        has_tc = any(i.startswith("TC-") for i in ids)
        has_uc = any(i.startswith("UC-") for i in ids)
        has_cl = any(i.startswith("CL-") for i in ids)

        if not has_tc:
            print("FAIL: no functional test cases (TC-*)")
            sys.exit(1)
        if not has_uc:
            print("FAIL: no use-case scenarios (UC-*)")
            sys.exit(1)
        if not has_cl:
            print("FAIL: no checklist items (CL-*)")
            sys.exit(1)

        print(f"PASS: F-003 Test Case Generation ({len(cases)} cases)")


if __name__ == "__main__":
    main()
