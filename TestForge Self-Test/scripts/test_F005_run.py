#!/usr/bin/env python3
"""F-005: Test testforge run executes test scripts."""
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

        # Create a simple test script that passes
        scripts_dir = os.path.join(project, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        with open(os.path.join(scripts_dir, "test_smoke.py"), "w") as f:
            f.write('print("smoke test passed")\n')

        result = subprocess.run(
            [testforge, "run", project],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"FAIL: run exited with code {result.returncode}")
            print(result.stderr)
            sys.exit(1)

        # Check output mentions passed
        if "Passed" not in result.stdout:
            print(f"FAIL: run output does not mention 'Passed': {result.stdout}")
            sys.exit(1)

        print("PASS: F-005 Test Execution")


if __name__ == "__main__":
    main()
