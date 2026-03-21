#!/usr/bin/env python3
"""F-010: Test testforge projects lists managed projects."""
import os
import subprocess
import sys
import tempfile


def main():
    testforge = os.path.join(os.path.dirname(sys.executable), "testforge")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create two projects
        subprocess.run(
            [testforge, "init", "proj-a", "--directory", tmpdir],
            capture_output=True, text=True, check=True,
        )
        subprocess.run(
            [testforge, "init", "proj-b", "--directory", tmpdir],
            capture_output=True, text=True, check=True,
        )

        result = subprocess.run(
            [testforge, "projects"],
            capture_output=True, text=True,
            cwd=tmpdir,
        )
        if result.returncode != 0:
            print(f"FAIL: projects exited with code {result.returncode}")
            print(result.stderr)
            sys.exit(1)

        if "proj-a" not in result.stdout or "proj-b" not in result.stdout:
            print(f"FAIL: projects output missing expected names: {result.stdout}")
            sys.exit(1)

        print("PASS: F-010 Multi-Project Management")


if __name__ == "__main__":
    main()
