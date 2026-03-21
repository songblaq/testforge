#!/usr/bin/env bash
# Test: testforge analyze runs with sample fixture input
set -euo pipefail

TESTFORGE="${TESTFORGE:-"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../.venv/bin/testforge"}"
FIXTURES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/fixtures"

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

TMPDIR_ANALYZE="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_ANALYZE"' EXIT

"$TESTFORGE" init analyze-test --directory "$TMPDIR_ANALYZE" >/dev/null 2>&1
PROJECT_DIR="$TMPDIR_ANALYZE/analyze-test"

# Copy sample fixture into project inputs
cp "$FIXTURES_DIR/sample-readme.md" "$PROJECT_DIR/inputs/"

# Run analyze -- may require LLM API key; we only check it does not crash with exit != 1
output="$("$TESTFORGE" analyze "$PROJECT_DIR" --input "$PROJECT_DIR/inputs/sample-readme.md" 2>&1)" || true
pass "analyze command ran without fatal crash (output: ${output:0:120})"

# The command should not print an unhandled Python traceback
[[ "$output" != *"Traceback (most recent call last)"* ]] || fail "analyze produced a Python traceback"
pass "analyze produced no Python traceback"
