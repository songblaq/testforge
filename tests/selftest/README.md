# TestForge Stage 0 Self-Tests

External bash test corpus that validates the TestForge CLI from the outside,
without relying on pytest. These scripts test the installed binary end-to-end.

## Structure

```
tests/selftest/
  run_all.sh                  # Master runner: executes all test_*.sh scripts
  test_cli_version.sh         # testforge --version
  test_cli_help.sh            # testforge --help
  test_cli_init.sh            # testforge init
  test_cli_projects.sh        # testforge projects
  test_cli_analyze.sh         # testforge analyze (with sample fixture)
  test_config_loading.sh      # config load/save round-trip
  test_pipeline_stages.sh     # pipeline stage execution
  fixtures/
    sample-readme.md          # Sample input document
    sample-config.yaml        # Valid testforge.yaml
    invalid-config.yaml       # Intentionally broken config
```

## Usage

```bash
# Run all selftests
bash tests/selftest/run_all.sh

# Run a single test
bash tests/selftest/test_cli_version.sh

# With a custom testforge binary path
TESTFORGE=path/to/testforge bash tests/selftest/run_all.sh
```

## Exit codes

- `0`: all tests passed
- `1`: one or more tests failed

Each script is independently executable and prints `PASS` or `FAIL` per assertion.
The master `run_all.sh` aggregates results and prints a final summary.
