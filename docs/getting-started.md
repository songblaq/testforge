# Getting Started with TestForge

This guide walks you through a complete TestForge workflow: from installation to a finished test
report. Each step shows the command, the expected output, and what happened under the hood.

## Prerequisites

- Python 3.11 or newer
- An API key for Anthropic or OpenAI (or a locally installed `claude`/`codex` CLI tool)
- Playwright browsers (for browser-based tests)

---

## Step 1: Install TestForge

```bash
# Minimal install (no LLM provider)
pip install testforge

# With Anthropic Claude (recommended)
pip install "testforge[anthropic]"

# With OpenAI GPT
pip install "testforge[openai]"

# With TUI interface
pip install "testforge[tui]"

# Everything
pip install "testforge[all]"
```

Install Playwright browsers after installation:

```bash
playwright install chromium
# For full cross-browser coverage:
playwright install
```

### Set your API key

```bash
# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI
export OPENAI_API_KEY="sk-..."
```

Add the export to your `~/.zshrc` or `~/.bashrc` to persist it.

### Verify installation

```bash
$ testforge --version
testforge, version 0.1.0
```

---

## Step 2: Create a Project

```bash
$ testforge init my-webapp --provider anthropic
Project created: my-webapp
  LLM provider: anthropic
  Config: my-webapp/.testforge/config.yaml
```

This creates the following directory structure:

```
my-webapp/
  .testforge/
    config.yaml      # Project configuration
  inputs/            # Drop your documents here
  analysis/          # Auto-populated by testforge analyze
  cases/             # Auto-populated by testforge generate
  scripts/           # Auto-populated by testforge script
  evidence/          # Auto-populated by testforge run
  output/            # Reports written here
```

### Options

```bash
# Specify parent directory
testforge init my-webapp --directory /path/to/projects

# Use OpenAI instead
testforge init my-webapp --provider openai --model gpt-4o

# Use a local CLI tool
testforge init my-webapp --provider cli
```

---

## Step 3: Add Input Documents

Place one or more of the following in `my-webapp/inputs/`:

| Format | Examples |
|--------|---------|
| PDF | Requirements doc, spec sheet, design brief |
| PowerPoint | Design slides, feature walkthrough |
| Word | Functional spec, user stories |
| Excel | Test matrix, data tables |
| Images | Screenshots, wireframes (PNG/JPG/WEBP) |
| URLs | Live staging URL, documentation page |
| GitHub repo | Repo URL for code-level analysis |

```bash
cp requirements.pdf my-webapp/inputs/
cp design.pptx my-webapp/inputs/
```

---

## Step 4: Analyze Documents

```bash
$ testforge analyze my-webapp
Auto-discovered 2 input file(s)
Analysis complete: 2 source(s), 18 features extracted
```

You can also pass files explicitly:

```bash
$ testforge analyze my-webapp \
    --input my-webapp/inputs/requirements.pdf \
    --input my-webapp/inputs/design.pptx
Analysis complete: 2 source(s), 18 features extracted
```

Or analyze a live URL:

```bash
$ testforge analyze my-webapp --input https://staging.example.com
Analysis complete: 1 source(s), 9 features extracted
```

The analysis output is saved to `my-webapp/analysis/analysis.json` and includes:
- **Features** — testable functionality items (e.g. "User login", "Password reset")
- **Personas** — user types derived from the documents (e.g. "Admin", "Guest")
- **Business rules** — constraints and expected behaviors
- **Screens** — UI pages or API endpoints identified

---

## Step 5: Generate Test Cases

```bash
# Generate all types (default)
$ testforge generate my-webapp
Generated: 36 test cases (all)

# Functional tests only
$ testforge generate my-webapp --type functional
Generated: 18 test cases (functional)

# Use-case scenarios only
$ testforge generate my-webapp --type usecase
Generated: 12 test cases (usecase)

# Manual QA checklist only
$ testforge generate my-webapp --type checklist
Generated: 6 test cases (checklist)

# Use flag aliases
$ testforge generate my-webapp --use-cases --checklists
Generated: 36 test cases (all)
```

Generated cases are saved to `my-webapp/cases/cases.json`.

Each test case contains:
- Unique ID (e.g. `TC-001`, `UC-001`, `CL-001`)
- Title and description
- Pre-conditions
- Steps
- Expected result
- Tags (for filtering during `testforge run`)

---

## Step 6: Generate Automation Scripts

```bash
$ testforge script my-webapp --framework playwright
Generated: 12 scripts (playwright)
```

Scripts are written to `my-webapp/scripts/`. Each script is a standalone Python file using the
Playwright API that can be run directly or via `testforge run`.

---

## Step 7: Run Tests

```bash
# Run all tests
$ testforge run my-webapp
Passed: 10  Failed: 2

# Run only smoke-tagged tests
$ testforge run my-webapp --tags smoke
Passed: 4  Failed: 0

# Run with parallel workers
$ testforge run my-webapp --parallel 4
Passed: 10  Failed: 2
```

Evidence (screenshots, logs) is collected under `my-webapp/evidence/` for each test run.

---

## Step 8: Generate a Report

```bash
# Markdown report (default)
$ testforge report my-webapp
Report generated: my-webapp/output/report.md

# HTML report
$ testforge report my-webapp --format html
Report generated: my-webapp/output/report.html

# Custom output path
$ testforge report my-webapp --format html --output /tmp/qa-report.html
Report generated: /tmp/qa-report.html
```

Open `report.html` in any browser to review results with embedded evidence links.

---

## Full Pipeline in One Command

Instead of running each stage manually, use `testforge pipeline`:

```bash
$ testforge pipeline my-webapp --input my-webapp/inputs/requirements.pdf
Pipeline complete: analyze, generate, script, run, report
```

Run only specific stages:

```bash
$ testforge pipeline my-webapp --stages analyze --stages generate
Pipeline complete: analyze, generate
```

---

## Manual QA Workflow

When tests require human judgment, use the manual checklist workflow:

```bash
# 1. Generate checklists (if not already done)
$ testforge generate my-webapp --type checklist

# 2. Start a session
$ testforge manual start my-webapp
Session started: session-20260322-143000
  Items: 8
  State saved to: my-webapp/.testforge/manual/active-session.json

# 3. Work through items
$ testforge manual check my-webapp CL-001 --note "Hero banner renders on mobile"
Checked: CL-001 -> pass  (1/8)

$ testforge manual check my-webapp CL-002 --status fail --note "Footer links broken in Safari"
Checked: CL-002 -> fail  (2/8)

# 4. Check progress at any time
$ testforge manual progress my-webapp
Progress: 2/8 (25%)
  Passed:  1
  Failed:  1
  Pending: 6

# 5. Finish and save the report
$ testforge manual finish my-webapp
Session finished: my-webapp/output/manual-report-20260322-143000.md
```

---

## Troubleshooting

### "No input files specified"

```
[yellow]No input files specified. Use -i or place files in inputs/ directory.[/yellow]
```

Either pass files with `--input` flags or copy documents into `my-webapp/inputs/`.

### "No cases generated. Run 'testforge analyze' first."

You must run `testforge analyze` before `testforge generate`. The generate step reads from
`analysis/analysis.json`.

### Playwright not found

```bash
pip install playwright
playwright install chromium
```

### Anthropic / OpenAI import errors

```bash
# For Anthropic
pip install "testforge[anthropic]"

# For OpenAI
pip install "testforge[openai]"
```

### TUI fails to launch

```bash
pip install "testforge[tui]"
```

### API key not found

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# or
export OPENAI_API_KEY="sk-..."
```

### Verify your installation with selftest

```bash
$ testforge selftest
$ testforge selftest --verbose   # show full output from each test script
```

---

## Next Steps

- [Configuration reference](configuration.md) — full config schema and LLM provider setup
- [CLI reference](cli-reference.md) — all commands with options and examples
- [Architecture](architecture.md) — internal module structure and data flow
