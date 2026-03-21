#!/usr/bin/env bash
# Test: testforge projects command runs without error
set -euo pipefail

TESTFORGE="${TESTFORGE:-"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../.venv/bin/testforge"}"

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

# Run without crashing (empty dir or finds projects)
"$TESTFORGE" projects 2>&1
exit_code=$?
[[ $exit_code -eq 0 ]] || fail "'testforge projects' exited with code $exit_code"
pass "'testforge projects' exits 0"

# Run in a temp dir with one project and verify it's listed
TMPDIR_PROJ="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_PROJ"' EXIT

"$TESTFORGE" init myapp --directory "$TMPDIR_PROJ" >/dev/null 2>&1

# Change into temp dir and list -- projects lists from cwd
output="$(cd "$TMPDIR_PROJ" && "$TESTFORGE" projects 2>&1)"
[[ "$output" == *"myapp"* ]] || fail "'testforge projects' did not list 'myapp': got '$output'"
pass "'testforge projects' lists created project"
