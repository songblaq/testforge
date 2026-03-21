#!/usr/bin/env bash
# Test: testforge --help shows all major commands
set -euo pipefail

TESTFORGE="${TESTFORGE:-"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../.venv/bin/testforge"}"

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

output="$("$TESTFORGE" --help 2>&1)"

for cmd in init analyze generate script run report pipeline projects; do
    [[ "$output" == *"$cmd"* ]] || fail "--help missing command '$cmd'"
    pass "--help contains '$cmd'"
done
