# TestForge

> LLM-powered QA automation platform — from documents to test reports

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![GitHub](https://img.shields.io/badge/GitHub-songblaq%2Ftestforge-black.svg)](https://github.com/songblaq/testforge)

```
 _____ _____ ____ _____ _____ ___  ____   ____ _____
|_   _| ____/ ___|_   _|  ___/ _ \|  _ \ / ___| ____|
  | | |  _| \___ \ | | | |_ | | | | |_) | |  _|  _|
  | | | |___ ___) || | |  _|| |_| |  _ <| |_| | |___
  |_| |_____|____/ |_| |_|   \___/|_| \_\\____|_____|
```

## What is TestForge?

TestForge transforms project documents — PDFs, specs, design slides, screenshots, and URLs — into
comprehensive test suites, ready to run. Feed it a requirements document and it extracts features,
derives user personas, identifies business rules, then produces functional test cases, use-case
scenarios, and manual QA checklists automatically.

Where LLM inference is the right tool (analysis, generation, judgment), TestForge uses it. Where
deterministic code is the right tool (script execution, evidence collection, report rendering),
TestForge uses that instead. The result is a platform that is both intelligent and reliable:
LLMs handle the hard parts, programmatic code handles the rest.

The full pipeline takes you from raw documents to a shareable HTML or Markdown test report in a
single session. Generated automation is **Playwright-based Python tests** run via pytest; HTTP API,
shell-command, and SSH-style execution paths are **planned** as connectors. A manual QA checklist
workflow covers scenarios that require a human eye.

## Key Features

- **Multi-format input** — PDF, PowerPoint, Word, Excel, images, URLs, GitHub repositories
- **LLM-powered analysis** — automatic feature extraction, persona derivation, business-rule identification
- **Smart test generation** — functional tests, use-case scenarios, manual checklists
- **Script generation**: Playwright browser tests (LLM-powered with skeleton fallback). More frameworks planned.
- **Dual-track QA** — automated execution track + structured manual-checklist track
- **Flexible execution** — Browser-based testing via Playwright (HTTP, Shell, SSH connectors planned)
- **Evidence collection** — screenshots and logs per test run (HAR traces planned)
- **Rich reports** — Markdown and HTML reports with evidence attachments
- **TUI interface** — full interactive terminal UI built with Textual
- **Multi-project management** — `testforge projects` lists all local projects
- **Self-test / dogfooding** — `testforge selftest` runs TestForge against itself
- **Multiple LLM providers** — Anthropic Claude, OpenAI GPT, CLI tools (claude, codex), and **Ollama** (`llm_provider: ollama`)

## Pipeline

```
  Documents        Analysis         Test Cases        Scripts              Execution           Reports
 +---------+     +-----------+     +-----------+     +----------------+     +---------------+     +---------+
 | PDF     |     | Features  |     | Functional|     | Playwright     |     | pytest +      |     |Markdown |
 | PPT     | --> | Personas  | --> | Use Cases | --> | (Python tests) | --> | Playwright    | --> | HTML    |
 | Word    |     | Rules     |     | Checklist |     |                |     | (browser)     |     | JSON    |
 | Excel   |     | Screens   |     |           |     |                |     |               |     |         |
 | Images  |     |           |     |           |     |                |     |               |     |         |
 | URLs    |     |           |     |           |     |                |     |               |     |         |
 | GitHub  |     |           |     |           |     |                |     |               |     |         |
 +---------+     +-----------+     +-----------+     +----------------+     +---------------+     +---------+
```

_Default `testforge run` executes generated Playwright-based Python tests via pytest. HTTP, shell,
SSH, and API-style connectors are planned or extension points—not the default generated script path._

Each stage persists its output to disk. You can run stages individually or chain the full pipeline
with a single `testforge pipeline` command.

## Quick Start

### Installation

```bash
# Core installation
pip install testforge

# With specific LLM provider
pip install "testforge[anthropic]"   # Anthropic Claude
pip install "testforge[openai]"      # OpenAI GPT
pip install "testforge[browser]"     # Browser testing (Playwright)
pip install "testforge[tui]"         # TUI interface (Textual)
pip install "testforge[web]"         # Web GUI (FastAPI)
pip install "testforge[all]"         # Everything

# Install Playwright browsers (required for browser testing)
playwright install chromium
```

### Your First Project

```bash
# 1. Create a project
$ testforge init my-webapp --provider anthropic
# Project created: my-webapp
#   LLM provider: anthropic
#   Config: my-webapp/.testforge/config.yaml

# 2. Place your documents in my-webapp/inputs/, then analyze
$ testforge analyze my-webapp --input my-webapp/inputs/requirements.pdf
# Auto-discovered 1 input file(s)
# Analysis complete: 1 source(s), 12 features extracted

# 3. Generate test cases
$ testforge generate my-webapp
# Generated: 24 test cases (all)

# 4. Generate automation scripts
$ testforge script my-webapp --framework playwright
# Generated: 8 scripts (playwright)

# 5. Run tests
$ testforge run my-webapp
# Passed: 7  Failed: 1

# 6. Generate report
$ testforge report my-webapp --format html
# Report generated: my-webapp/output/report.html
```

Alternatively, run the entire pipeline in one command:

```bash
$ testforge pipeline my-webapp --input my-webapp/inputs/requirements.pdf
# Pipeline complete: analyze, generate, script, run, report
```

For deterministic local dogfooding or environments without API keys, use the global offline flag:

```bash
$ testforge --no-llm pipeline my-webapp --input my-webapp/inputs/requirements.pdf
# Pipeline complete: analyze, generate, script, run, report
```

`--no-llm` skips external model calls and uses offline heuristics/skeleton generation for
`analyze`, `generate`, `script`, `pipeline`, and `research`.

## CLI Reference

See [docs/cli-reference.md](docs/cli-reference.md) for the full command reference.

| Command | Description |
|---------|-------------|
| `testforge init NAME` | Create a new project |
| `testforge analyze PROJECT` | Parse inputs and extract features |
| `testforge generate PROJECT` | Generate test cases |
| `testforge script PROJECT` | Generate automation scripts |
| `testforge run PROJECT` | Execute tests and collect evidence |
| `testforge report PROJECT` | Generate test report |
| `testforge pipeline PROJECT` | Run the full pipeline end-to-end |
| `testforge manual start PROJECT` | Start a manual QA checklist session |
| `testforge manual check PROJECT ITEM_ID` | Record pass/fail for a checklist item |
| `testforge manual progress PROJECT` | Show checklist session progress |
| `testforge manual finish PROJECT` | Finish session and save report |
| `testforge tui [PROJECT]` | Launch TUI interface |
| `testforge web` | Launch Web GUI (requires `testforge[web]`) |
| `testforge research PROJECT` | Run AutoResearch loop (iterations, threshold, strategy; supports `--no-llm`) |
| `testforge coverage PROJECT` | Print feature/rule coverage from `analysis.json` vs `cases.json` |
| `testforge projects` | List all local TestForge projects |
| `testforge selftest` | Run built-in self-test suite |

## Manual QA Workflow

For test scenarios that require human judgment, TestForge generates a structured checklist and
tracks your progress through it:

```bash
# Generate checklists first
$ testforge generate my-webapp --type checklist

# Start a manual session
$ testforge manual start my-webapp
# Session started: session-20260322-143000
#   Items: 15
#   State saved to: my-webapp/.testforge/manual/active-session.json

# Record results item by item
$ testforge manual check my-webapp CL-001 --note "Login form renders correctly"
# Checked: CL-001 -> pass  (1/15)

$ testforge manual check my-webapp CL-002 --status fail --note "Submit button misaligned on mobile"
# Checked: CL-002 -> fail  (2/15)

# Check progress at any time
$ testforge manual progress my-webapp
# Progress: 2/15 (13%)
#   Passed:  1
#   Failed:  1
#   Pending: 13

# Finish and save the report
$ testforge manual finish my-webapp
# Session finished: my-webapp/output/manual-report-20260322-143000.md
```

## TUI Mode

Launch the interactive terminal interface for a visual project dashboard:

```bash
$ testforge tui
# or open a specific project directly
$ testforge tui my-webapp
```

Requires the `tui` extra: `pip install "testforge[tui]"`.

The TUI provides:
- **Dashboard** — project overview, pipeline status, recent runs
- **Cases** — browsable test case table with filtering
- **Runner** — live execution view with pass/fail indicators
- **Manual** — guided checklist walkthrough

Key bindings: `Tab` to switch screens, `q` to quit, `r` to run, `Enter` to inspect.

### Web GUI

Install with web dependencies and launch:

```bash
pip install "testforge[web]"
testforge web
```

Opens at `http://127.0.0.1:8000`. Use `--host` and `--port` to customize.

The web interface provides:

- Project management with guided pipeline stepper
- Visual test case editor with CRUD operations
- One-click analysis, generation, and execution
- Real-time execution results and report viewing
- Multi-language support (English, Korean, Vietnamese)

## Configuration

Each project has a `.testforge/config.yaml` file:

```yaml
project_name: my-webapp
version: "0.1.0"

# LLM settings
llm_provider: anthropic   # anthropic | openai | cli | ollama
llm_model: ""             # leave empty to use provider default

# Directory layout (relative to project root)
input_dir: inputs
output_dir: output
evidence_dir: evidence
cases_dir: cases
analysis_dir: analysis
```

See [docs/configuration.md](docs/configuration.md) for the full schema and global config.

## LLM Providers

| Provider | Install extra | Environment variable |
|----------|--------------|----------------------|
| Anthropic Claude | `testforge[anthropic]` | `ANTHROPIC_API_KEY` |
| OpenAI GPT | `testforge[openai]` | `OPENAI_API_KEY` |
| CLI tools (claude, codex) | _(none)_ | _(CLI must be in PATH)_ |
| Ollama (local) | _(none)_ | Set `llm_provider: ollama` and `llm_model` in config (local Ollama server) |

## Connectors

TestForge uses connectors for test execution. Default `testforge run` uses the **browser (Playwright)**
path on generated `.py` tests. HTTP and shell connectors exist in the architecture but are not the
default generated-script or `run` path today. Each connector maps to a test type:

| Connector | Use case |
|-----------|----------|
| **Browser** (Playwright) | UI/UX tests, end-to-end flows |
| **HTTP** (httpx) | REST API tests, webhook verification |
| **Shell** (subprocess) | CLI tool tests, build script verification |
| **SSH** | Remote server tests (placeholder — extensible, not yet implemented) |

## Project Structure

```
my-webapp/
  .testforge/
    config.yaml          # Project configuration
    manual/
      active-session.json  # Active manual QA session state
  inputs/                # Source documents (PDFs, specs, images, etc.)
  analysis/
    analysis.json        # Extracted features, personas, rules
  cases/
    cases.json           # Generated test cases
  scripts/               # Generated automation scripts (.py, Playwright/pytest)
  evidence/              # Screenshots and logs from test runs (HAR capture planned)
  output/                # Generated reports
```

## Self-Test

TestForge can test itself using the `selftest` command. This is useful to verify your installation
is working correctly:

```bash
$ testforge selftest
  running smoke.sh ... PASS
  running pipeline.sh ... PASS

Results: 2/2 passed  All tests passed.

# Verbose mode shows stdout/stderr from each script
$ testforge selftest --verbose
```

## Development

```bash
# Clone
git clone https://github.com/songblaq/testforge.git
cd testforge

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/
```

## Part of the Forge Series

TestForge is the first product of the **LucaBlaq Tech Forge Series** — a collection of
developer-focused tools that apply LLM intelligence to common engineering workflows.

## Contributing

Contributions are welcome. Please open an issue first to discuss the change you have in mind,
then submit a pull request against `main`.

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
