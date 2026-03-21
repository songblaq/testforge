#!/usr/bin/env python3
"""F-007: Test testforge manual start/check/progress/finish workflow."""
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

        # Write analysis so checklist can be generated
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

        # manual start
        result = subprocess.run(
            [testforge, "manual", "start", project],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"FAIL: manual start exited with code {result.returncode}")
            print(result.stderr)
            sys.exit(1)

        if "Session started" not in result.stdout:
            print(f"FAIL: unexpected output from manual start: {result.stdout}")
            sys.exit(1)

        # manual check
        result = subprocess.run(
            [testforge, "manual", "check", project, "CL-001", "--status", "pass", "--note", "looks good"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"FAIL: manual check exited with code {result.returncode}")
            print(result.stderr)
            sys.exit(1)

        if "Checked" not in result.stdout:
            print(f"FAIL: unexpected output from manual check: {result.stdout}")
            sys.exit(1)

        # manual progress
        result = subprocess.run(
            [testforge, "manual", "progress", project],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"FAIL: manual progress exited with code {result.returncode}")
            print(result.stderr)
            sys.exit(1)

        if "Progress" not in result.stdout:
            print(f"FAIL: unexpected output from manual progress: {result.stdout}")
            sys.exit(1)

        # manual finish
        result = subprocess.run(
            [testforge, "manual", "finish", project],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"FAIL: manual finish exited with code {result.returncode}")
            print(result.stderr)
            sys.exit(1)

        if "Session finished" not in result.stdout:
            print(f"FAIL: unexpected output from manual finish: {result.stdout}")
            sys.exit(1)

        print("PASS: F-007 Manual QA Workflow")


if __name__ == "__main__":
    main()
