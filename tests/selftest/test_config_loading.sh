#!/usr/bin/env bash
# Test: config loading -- valid config round-trip, invalid config error handling
set -euo pipefail

TESTFORGE="${TESTFORGE:-"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../.venv/bin/testforge"}"
FIXTURES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/fixtures"
PYTHON="${PYTHON:-"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../.venv/bin/python"}"

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

TMPDIR_CFG="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_CFG"' EXIT

# --- Test 1: valid config is loadable via CLI (init + check file) ---
"$TESTFORGE" init cfg-test --directory "$TMPDIR_CFG" >/dev/null 2>&1
PROJECT_DIR="$TMPDIR_CFG/cfg-test"
[[ -f "$PROJECT_DIR/.testforge/config.yaml" ]] || fail "config.yaml not created by init"
pass "valid config file created"

# --- Test 2: config values round-trip through Python API ---
config_output="$("$PYTHON" - <<'PYEOF'
import sys
sys.path.insert(0, "src")
import os, tempfile
from pathlib import Path
from testforge.core.config import TestForgeConfig, save_config, load_config

with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "proj"
    p.mkdir()
    cfg = TestForgeConfig(
        project_name="roundtrip-test",
        llm_provider="openai",
        llm_model="gpt-4o",
    )
    save_config(p, cfg)
    loaded = load_config(p)
    assert loaded.project_name == "roundtrip-test", f"name mismatch: {loaded.project_name}"
    assert loaded.llm_provider == "openai", f"provider mismatch: {loaded.llm_provider}"
    assert loaded.llm_model == "gpt-4o", f"model mismatch: {loaded.llm_model}"
    print("OK")
PYEOF
)" || fail "config round-trip Python script failed"

[[ "$config_output" == *"OK"* ]] || fail "config round-trip did not return OK: $config_output"
pass "config round-trip OK (save + load matches)"

# --- Test 3: missing config file falls back to defaults gracefully ---
no_config_output="$("$PYTHON" - <<'PYEOF'
import sys
sys.path.insert(0, "src")
import tempfile
from pathlib import Path
from testforge.core.config import load_config

with tempfile.TemporaryDirectory() as tmp:
    cfg = load_config(Path(tmp))
    assert cfg.llm_provider == "anthropic"
    assert cfg.input_dir == "inputs"
    print("OK")
PYEOF
)" || fail "missing config fallback Python script failed"

[[ "$no_config_output" == *"OK"* ]] || fail "missing config fallback did not return OK"
pass "missing config falls back to defaults"
