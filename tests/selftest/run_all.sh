#!/usr/bin/env bash
# Stage 0: External bash test corpus for TestForge
# Usage: bash tests/selftest/run_all.sh [--verbose]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTFORGE="${TESTFORGE:-"$SCRIPT_DIR/../../.venv/bin/testforge"}"
export TESTFORGE

PASS=0
FAIL=0
TOTAL=0
VERBOSE="${VERBOSE:-0}"
[[ "${1:-}" == "--verbose" ]] && VERBOSE=1

# Color codes (disabled if not a terminal)
if [[ -t 1 ]]; then
    GREEN="\033[0;32m"
    RED="\033[0;31m"
    YELLOW="\033[0;33m"
    RESET="\033[0m"
else
    GREEN="" RED="" YELLOW="" RESET=""
fi

run_test() {
    local script="$1"
    local name
    name="$(basename "$script" .sh)"
    TOTAL=$((TOTAL + 1))

    if [[ "$VERBOSE" == "1" ]]; then
        echo "--- $name ---"
        if bash "$script"; then
            echo -e "${GREEN}PASS${RESET} $name"
            PASS=$((PASS + 1))
        else
            echo -e "${RED}FAIL${RESET} $name"
            FAIL=$((FAIL + 1))
        fi
        echo ""
    else
        local output
        local exit_code=0
        output=$(bash "$script" 2>&1) || exit_code=$?
        if [[ $exit_code -eq 0 ]]; then
            echo -e "${GREEN}PASS${RESET} $name"
            PASS=$((PASS + 1))
        else
            echo -e "${RED}FAIL${RESET} $name"
            echo "$output" | sed 's/^/       /'
            FAIL=$((FAIL + 1))
        fi
    fi
}

echo "TestForge Stage 0 Self-Tests"
echo "TESTFORGE: $TESTFORGE"
echo "-----------------------------------"

# Verify binary is available
if ! command -v "$TESTFORGE" &>/dev/null && [[ ! -x "$TESTFORGE" ]]; then
    echo -e "${RED}ERROR${RESET}: testforge binary not found at: $TESTFORGE"
    echo "Install with: pip install -e . (in the project root)"
    exit 1
fi

for script in "$SCRIPT_DIR"/test_*.sh; do
    run_test "$script"
done

echo ""
echo "==================================="
echo -e "Results: ${GREEN}${PASS} passed${RESET}, ${RED}${FAIL} failed${RESET}, ${TOTAL} total"
echo "==================================="

[[ $FAIL -eq 0 ]]
