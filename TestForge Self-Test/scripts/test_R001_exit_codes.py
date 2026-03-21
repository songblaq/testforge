#!/usr/bin/env python3
"""R-001: CLI must exit 0 on success, non-zero on failure."""
import os
import subprocess
import sys


def main():
    testforge = os.path.join(os.path.dirname(sys.executable), "testforge")

    # Success case: --help should exit 0
    result = subprocess.run(
        [testforge, "--help"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"FAIL: --help exited with code {result.returncode}")
        sys.exit(1)

    # Success case: --version should exit 0
    result = subprocess.run(
        [testforge, "--version"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"FAIL: --version exited with code {result.returncode}")
        sys.exit(1)

    # Failure case: analyze on non-existent project should exit non-zero
    result = subprocess.run(
        [testforge, "analyze", "/tmp/nonexistent-project-xyz-12345"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("FAIL: analyze on nonexistent path exited 0 (expected non-zero)")
        sys.exit(1)

    print("PASS: R-001 CLI Exit Codes")


if __name__ == "__main__":
    main()
