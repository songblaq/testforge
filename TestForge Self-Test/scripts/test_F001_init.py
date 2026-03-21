#!/usr/bin/env python3
"""F-001: Test testforge init creates project structure."""
import subprocess
import sys
import tempfile
import os

def main():
    testforge = os.path.join(os.path.dirname(sys.executable), "testforge")
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [testforge, "init", "test-project", "--directory", tmpdir],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"FAIL: init exited with code {result.returncode}")
            print(result.stderr)
            sys.exit(1)

        project_dir = os.path.join(tmpdir, "test-project")

        # Check testforge.yaml equivalent (.testforge/config.yaml)
        config_path = os.path.join(project_dir, ".testforge", "config.yaml")
        if not os.path.isfile(config_path):
            print("FAIL: .testforge/config.yaml not created")
            sys.exit(1)

        # Check expected subdirectories
        for subdir in ["inputs", "output", "evidence", "scripts", "cases", "analysis"]:
            path = os.path.join(project_dir, subdir)
            if not os.path.isdir(path):
                print(f"FAIL: {subdir}/ not created")
                sys.exit(1)

        print("PASS: F-001 Project Init")

if __name__ == "__main__":
    main()
