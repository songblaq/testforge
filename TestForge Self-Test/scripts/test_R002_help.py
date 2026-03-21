#!/usr/bin/env python3
"""R-002: All commands must show --help."""
import os
import subprocess
import sys


def main():
    testforge = os.path.join(os.path.dirname(sys.executable), "testforge")

    commands = [
        [],  # root --help
        ["init"],
        ["analyze"],
        ["generate"],
        ["script"],
        ["run"],
        ["report"],
        ["pipeline"],
        ["manual"],
        ["manual", "start"],
        ["manual", "check"],
        ["manual", "progress"],
        ["manual", "finish"],
        ["tui"],
        ["projects"],
        ["selftest"],
    ]

    failed = []
    for cmd in commands:
        full_cmd = [testforge] + cmd + ["--help"]
        result = subprocess.run(full_cmd, capture_output=True, text=True)
        label = " ".join(cmd) if cmd else "(root)"
        if result.returncode != 0:
            failed.append(label)

    if failed:
        print(f"FAIL: --help failed for: {', '.join(failed)}")
        sys.exit(1)

    print(f"PASS: R-002 Help Available ({len(commands)} commands verified)")


if __name__ == "__main__":
    main()
