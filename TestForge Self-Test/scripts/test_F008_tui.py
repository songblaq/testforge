#!/usr/bin/env python3
"""F-008: Test testforge tui import availability."""
import os
import subprocess
import sys


def main():
    testforge = os.path.join(os.path.dirname(sys.executable), "testforge")

    # TUI requires textual, which may or may not be installed.
    # We just verify the command exists and shows an appropriate message.
    result = subprocess.run(
        [testforge, "tui", "--help"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"FAIL: tui --help exited with code {result.returncode}")
        print(result.stderr)
        sys.exit(1)

    if "Launch the interactive TUI" not in result.stdout:
        print(f"FAIL: tui --help missing expected text: {result.stdout}")
        sys.exit(1)

    print("PASS: F-008 TUI Interface (help available)")


if __name__ == "__main__":
    main()
