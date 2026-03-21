#!/usr/bin/env bash
# Test: testforge --version prints the version string
set -euo pipefail

TESTFORGE="${TESTFORGE:-"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../.venv/bin/testforge"}"

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

output="$("$TESTFORGE" --version 2>&1)"
[[ "$output" == *"0.1.0"* ]] || fail "--version output missing '0.1.0': got '$output'"
pass "--version contains '0.1.0'"
