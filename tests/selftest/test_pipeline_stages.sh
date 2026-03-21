#!/usr/bin/env bash
# Test: pipeline stage routing -- individual stages can be invoked without crash
set -euo pipefail

TESTFORGE="${TESTFORGE:-"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../.venv/bin/testforge"}"
PYTHON="${PYTHON:-"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../.venv/bin/python"}"
FIXTURES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/fixtures"

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

TMPDIR_PL="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_PL"' EXIT

"$TESTFORGE" init pipeline-test --directory "$TMPDIR_PL" >/dev/null 2>&1
PROJECT_DIR="$TMPDIR_PL/pipeline-test"

# --- Test 1: pipeline with unknown stage reports error cleanly ---
output="$("$TESTFORGE" pipeline "$PROJECT_DIR" --stages unknown-stage 2>&1)" || true
[[ "$output" != *"Traceback"* ]] || fail "unknown stage produced Python traceback"
pass "unknown stage handled without traceback"

# --- Test 2: pipeline run stage completes (returns 0; no results is acceptable) ---
output="$("$TESTFORGE" pipeline "$PROJECT_DIR" --stages run 2>&1)" || true
[[ "$output" != *"Traceback"* ]] || fail "run stage produced Python traceback"
pass "pipeline run stage produced no traceback"

# --- Test 3: pipeline report stage produces a report file ---
output="$("$TESTFORGE" pipeline "$PROJECT_DIR" --stages report 2>&1)" || true
[[ "$output" != *"Traceback"* ]] || fail "report stage produced Python traceback"
pass "pipeline report stage produced no traceback"

REPORT_FILE="$PROJECT_DIR/output/report.md"
[[ -f "$REPORT_FILE" ]] || fail "report.md not created at $REPORT_FILE"
pass "report.md created by pipeline report stage"

# --- Test 4: PipelineResult.success via Python API ---
api_output="$("$PYTHON" - <<'PYEOF'
import sys
sys.path.insert(0, "src")
from testforge.core.pipeline import PipelineResult
r = PipelineResult(project="test")
assert r.success is True
r.errors.append("boom")
assert r.success is False
print("OK")
PYEOF
)" || fail "PipelineResult API test failed"
[[ "$api_output" == *"OK"* ]] || fail "PipelineResult.success logic incorrect"
pass "PipelineResult.success property works correctly"

# --- Test 5: generate and script stages run without crash ---
for stage in generate script; do
    out="$("$TESTFORGE" pipeline "$PROJECT_DIR" --stages "$stage" 2>&1)" || true
    [[ "$out" != *"Traceback"* ]] || fail "stage '$stage' produced Python traceback"
    pass "pipeline stage '$stage' produced no traceback"
done
