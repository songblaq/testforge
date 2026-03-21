#!/usr/bin/env python3
"""F-006: Test testforge report generates markdown reports."""
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

        # Generate a report (even without results, it should produce an empty report)
        result = subprocess.run(
            [testforge, "report", project],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"FAIL: report exited with code {result.returncode}")
            print(result.stderr)
            sys.exit(1)

        report_path = os.path.join(project, "output", "report.md")
        if not os.path.isfile(report_path):
            print("FAIL: output/report.md not created")
            sys.exit(1)

        with open(report_path) as f:
            content = f.read()

        if len(content) < 10:
            print("FAIL: report is too short")
            sys.exit(1)

        print("PASS: F-006 Report Generation")


if __name__ == "__main__":
    main()
