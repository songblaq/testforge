#!/usr/bin/env bash
# Test: testforge analyze runs with sample fixture input
# Note: The analyze command invokes the LLM analyzer pipeline which may fail
# without an API key or due to upstream bugs. This test only validates that
# the CLI plumbing (import, argument parsing, project loading) works correctly.
set -euo pipefail

TESTFORGE="${TESTFORGE:-"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../.venv/bin/testforge"}"
FIXTURES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/fixtures"

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

TMPDIR_ANALYZE="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_ANALYZE"' EXIT

"$TESTFORGE" init analyze-test --directory "$TMPDIR_ANALYZE" >/dev/null 2>&1
PROJECT_DIR="$TMPDIR_ANALYZE/analyze-test"

[[ -d "$PROJECT_DIR" ]] || fail "init failed: project dir not created"
pass "project directory created for analyze test"

# Copy sample fixture into project inputs
cp "$FIXTURES_DIR/sample-readme.md" "$PROJECT_DIR/inputs/"

# Run analyze -- capture output; we don't fail on non-zero exit since the
# analyzer requires an LLM API key or may hit upstream bugs unrelated to CLI.
output="$("$TESTFORGE" analyze "$PROJECT_DIR" --input "$PROJECT_DIR/inputs/sample-readme.md" 2>&1)" || true
pass "analyze command invoked without import/startup crash (output: ${output:0:80})"

# Must not crash at import time (ModuleNotFoundError, SyntaxError, etc.)
[[ "$output" != *"ModuleNotFoundError"* ]] || fail "analyze: ModuleNotFoundError -- missing dependency"
pass "analyze: no ModuleNotFoundError"

[[ "$output" != *"SyntaxError"* ]] || fail "analyze: SyntaxError in source"
pass "analyze: no SyntaxError"

# Verify the project structure is intact after the analyze attempt
[[ -f "$PROJECT_DIR/.testforge/config.yaml" ]] || fail "config.yaml missing after analyze"
pass "project config.yaml intact after analyze"
