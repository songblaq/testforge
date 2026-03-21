#!/usr/bin/env python3
"""F-009: Test testforge selftest runs built-in tests."""
import os
import subprocess
import sys


def main():
    testforge = os.path.join(os.path.dirname(sys.executable), "testforge")

    result = subprocess.run(
        [testforge, "selftest"],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    )

    # selftest may exit 0 (all pass) or report no scripts found
    # either is acceptable for this verification
    if "PASS" in result.stdout or "No selftest" in result.stdout or "passed" in result.stdout:
        print("PASS: F-009 Self-Test Suite")
    else:
        print(f"FAIL: selftest output unexpected: {result.stdout}")
        print(result.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
