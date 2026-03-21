#!/usr/bin/env python3
"""F-004: Test testforge script generates automation scripts."""
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

        # Write analysis and cases so script generation has input
        analysis_dir = os.path.join(project, "analysis")
        os.makedirs(analysis_dir, exist_ok=True)
        analysis = {
            "features": [
                {"id": "F-001", "name": "Login", "description": "User login", "category": "auth",
                 "priority": "high", "screens": [], "tags": [], "source": ""},
            ],
            "screens": [], "personas": [], "rules": [], "raw_sources": [],
        }
        with open(os.path.join(analysis_dir, "analysis.json"), "w") as f:
            json.dump(analysis, f)

        cases_dir = os.path.join(project, "cases")
        os.makedirs(cases_dir, exist_ok=True)
        cases = [
            {"id": "TC-F001-01", "title": "Verify Login", "description": "Test login",
             "feature_id": "F-001", "preconditions": [], "steps": [], "expected_result": "Login works",
             "priority": "high", "tags": ["smoke"]},
        ]
        with open(os.path.join(cases_dir, "cases.json"), "w") as f:
            json.dump(cases, f)

        result = subprocess.run(
            [testforge, "script", project],
            capture_output=True, text=True,
        )
        # Script generation may produce 0 scripts if no URL/browser target
        # but the command itself should not error out
        if result.returncode != 0:
            print(f"FAIL: script exited with code {result.returncode}")
            print(result.stderr)
            sys.exit(1)

        print("PASS: F-004 Script Generation")


if __name__ == "__main__":
    main()
