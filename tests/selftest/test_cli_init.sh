#!/usr/bin/env bash
# Test: testforge init creates project structure
set -euo pipefail

TESTFORGE="${TESTFORGE:-"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../.venv/bin/testforge"}"
FIXTURES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/fixtures"

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

TMPDIR_INIT="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_INIT"' EXIT

output="$("$TESTFORGE" init selftest-project --directory "$TMPDIR_INIT" 2>&1)"
[[ "$output" == *"Project created"* ]] || fail "init output missing 'Project created': got '$output'"
pass "init prints 'Project created'"

PROJECT_DIR="$TMPDIR_INIT/selftest-project"

[[ -d "$PROJECT_DIR" ]] || fail "project directory not created: $PROJECT_DIR"
pass "project directory exists"

[[ -f "$PROJECT_DIR/.testforge/config.yaml" ]] || fail ".testforge/config.yaml not created"
pass ".testforge/config.yaml exists"

for subdir in inputs output evidence scripts cases analysis; do
    [[ -d "$PROJECT_DIR/$subdir" ]] || fail "subdirectory '$subdir' not created"
    pass "subdirectory '$subdir' exists"
done
