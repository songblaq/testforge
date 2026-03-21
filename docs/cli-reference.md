# TestForge CLI Reference

Complete reference for all `testforge` commands.

## Global Options

These options apply to every command:

```
testforge [OPTIONS] COMMAND [ARGS]...

Options:
  -y, --non-interactive   Skip confirmation prompts and auto-approve.
  --version               Show version and exit.
  --help                  Show help and exit.
```

---

## `testforge init`

Create a new TestForge project.

```
testforge init NAME [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `NAME` | Project name. A directory with this name is created. |

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-d, --directory PATH` | `.` (current dir) | Parent directory where the project folder is created. |
| `-p, --provider TEXT` | `anthropic` | LLM provider: `anthropic`, `openai`, `cli`. |
| `-m, --model TEXT` | `""` | LLM model name. Empty uses the provider default. |

**Examples:**

```bash
# Create a project in the current directory
testforge init my-webapp

# Create under a specific parent, using OpenAI
testforge init my-webapp --directory ~/projects --provider openai --model gpt-4o

# Create with Anthropic Haiku for cheaper runs
testforge init my-webapp --provider anthropic --model claude-3-haiku-20240307
```

**Output:**
```
Project created: my-webapp
  LLM provider: anthropic
  Config: my-webapp/.testforge/config.yaml
```

**Creates:**
```
my-webapp/
  .testforge/config.yaml
  inputs/
  output/
  evidence/
  scripts/
  cases/
  analysis/
```

---

## `testforge analyze`

Parse input documents and extract features, personas, and business rules using LLM analysis.

```
testforge analyze PROJECT [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PROJECT` | Path to an existing TestForge project directory. |

**Options:**

| Option | Description |
|--------|-------------|
| `-i, --input PATH_OR_URL` | File path or URL to analyze. Repeatable. If omitted, all files in `inputs/` are auto-discovered. |

**Examples:**

```bash
# Auto-discover files from inputs/
testforge analyze my-webapp

# Explicit file list
testforge analyze my-webapp -i inputs/spec.pdf -i inputs/design.pptx

# Analyze a live URL
testforge analyze my-webapp -i https://staging.example.com

# Mix files and URLs
testforge analyze my-webapp -i inputs/spec.pdf -i https://staging.example.com
```

**Output:**
```
Auto-discovered 2 input file(s)
Analysis complete: 2 source(s), 18 features extracted
```

**Persists to:** `{project}/analysis/analysis.json`

**Supported input types:**
- `.pdf` — PDF documents (text + embedded images)
- `.pptx` — PowerPoint presentations
- `.docx` — Word documents
- `.xlsx` — Excel spreadsheets
- `.png`, `.jpg`, `.jpeg`, `.webp` — Images (LLM vision)
- `http://...`, `https://...` — URLs (crawled and extracted)
- GitHub repository URLs

---

## `testforge generate`

Generate test cases from analysis results.

```
testforge generate PROJECT [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PROJECT` | Path to an existing TestForge project directory. |

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-t, --type TYPE` | `all` | Test case type: `functional`, `usecase`, `checklist`, `all`. |
| `--use-cases` | off | Generate use-case scenarios (same as `-t usecase`). |
| `--checklists` | off | Generate manual checklists (same as `-t checklist`). |

Note: `--use-cases` and `--checklists` together are equivalent to `-t all`.

**Examples:**

```bash
# Generate all types
testforge generate my-webapp

# Functional tests only
testforge generate my-webapp --type functional

# Use-case scenarios only
testforge generate my-webapp --type usecase

# Manual checklists only
testforge generate my-webapp --type checklist

# Use flag shortcuts
testforge generate my-webapp --use-cases
testforge generate my-webapp --checklists
testforge generate my-webapp --use-cases --checklists
```

**Output:**
```
Generated: 36 test cases (all)
```

**Persists to:** `{project}/cases/cases.json`

**Test case ID prefixes:**
- `TC-NNN` — Functional test cases
- `UC-NNN` — Use-case scenarios
- `CL-NNN` — Manual checklist items

---

## `testforge script`

Generate automation scripts from test cases.

```
testforge script PROJECT [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PROJECT` | Path to an existing TestForge project directory. |

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-f, --framework FRAMEWORK` | `playwright` | Script framework: `playwright`. |

**Examples:**

```bash
testforge script my-webapp
testforge script my-webapp --framework playwright
```

**Output:**
```
Generated: 12 scripts (playwright)
```

**Persists to:** `{project}/scripts/`

---

## `testforge run`

Execute generated test scripts and collect evidence.

```
testforge run PROJECT [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PROJECT` | Path to an existing TestForge project directory. |

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-t, --tags TAG` | _(all)_ | Filter tests by tag. Repeatable. |
| `-p, --parallel N` | `1` | Number of parallel workers. |

**Examples:**

```bash
# Run all tests
testforge run my-webapp

# Smoke tests only
testforge run my-webapp --tags smoke

# Multiple tag filters
testforge run my-webapp --tags smoke --tags login

# Parallel execution
testforge run my-webapp --parallel 4

# Combined
testforge run my-webapp --tags regression --parallel 2
```

**Output:**
```
Passed: 10  Failed: 2
```

**Collects evidence to:** `{project}/evidence/`

---

## `testforge report`

Generate a test report from execution results.

```
testforge report PROJECT [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PROJECT` | Path to an existing TestForge project directory. |

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-f, --format FORMAT` | `markdown` | Report format: `markdown`, `html`. |
| `-o, --output PATH` | _(auto)_ | Output path. Defaults to `{project}/output/report.{ext}`. |

**Examples:**

```bash
# Markdown report
testforge report my-webapp

# HTML report
testforge report my-webapp --format html

# Custom output path
testforge report my-webapp --format html --output /tmp/qa-report.html
```

**Output:**
```
Report generated: my-webapp/output/report.html
```

---

## `testforge pipeline`

Run the full TestForge pipeline end to end in a single command.

```
testforge pipeline PROJECT [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PROJECT` | Path to an existing TestForge project directory. |

**Options:**

| Option | Description |
|--------|-------------|
| `-s, --stages STAGE` | Limit to specific stages. Repeatable. Stages: `analyze`, `generate`, `script`, `run`, `report`. |
| `-i, --input PATH_OR_URL` | Input files for the analysis stage. Repeatable. |

**Examples:**

```bash
# Full pipeline
testforge pipeline my-webapp

# With explicit inputs
testforge pipeline my-webapp --input inputs/spec.pdf --input inputs/design.pptx

# Only analysis + generation
testforge pipeline my-webapp --stages analyze --stages generate

# Skip execution (analysis → generate → script)
testforge pipeline my-webapp --stages analyze --stages generate --stages script
```

**Output (success):**
```
Pipeline complete: analyze, generate, script, run, report
```

**Output (failure):**
```
Pipeline failed: run stage: 3 scripts failed to execute
  Completed stages: analyze, generate, script
```

---

## `testforge manual`

Commands for the manual QA checklist workflow.

### `testforge manual start`

Start a manual test checklist session.

```
testforge manual start PROJECT
```

**Output:**
```
Session started: session-20260322-143000
  Items: 15
  State saved to: my-webapp/.testforge/manual/active-session.json
```

---

### `testforge manual check`

Record pass or fail for a checklist item.

```
testforge manual check PROJECT ITEM_ID [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PROJECT` | Path to an existing TestForge project directory. |
| `ITEM_ID` | Checklist item ID, e.g. `CL-001`. |

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-s, --status STATUS` | `pass` | Result: `pass` or `fail`. |
| `-n, --note TEXT` | `""` | Optional tester note. |

**Examples:**

```bash
# Mark as passed
testforge manual check my-webapp CL-001

# Mark as failed with a note
testforge manual check my-webapp CL-002 --status fail --note "Button misaligned on mobile"

# Pass with a note
testforge manual check my-webapp CL-003 --note "Looks good on Chrome and Firefox"
```

**Output:**
```
Checked: CL-001 -> pass  (1/15)
```

---

### `testforge manual progress`

Show progress of the active manual test session.

```
testforge manual progress PROJECT
```

**Output:**
```
Progress: 7/15 (46%)
  Passed:  5
  Failed:  2
  Pending: 8
```

---

### `testforge manual finish`

Finish the active session and save the final report.

```
testforge manual finish PROJECT
```

**Output:**
```
Session finished: my-webapp/output/manual-report-20260322-143000.md
```

---

## `testforge tui`

Launch the interactive TUI interface.

```
testforge tui [PROJECT]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PROJECT` | (optional) Path to a project to open on launch. |

**Requires:** `pip install "testforge[tui]"`

**Examples:**

```bash
# Open TUI with project selector
testforge tui

# Open directly to a project
testforge tui my-webapp
```

**Screens:**
- **Dashboard** — project overview, pipeline status
- **Cases** — browsable/filterable test case table
- **Runner** — live execution view
- **Manual** — guided checklist walkthrough

**Key bindings:**

| Key | Action |
|-----|--------|
| `Tab` | Cycle between screens |
| `q` | Quit |
| `r` | Run tests |
| `Enter` | Inspect selected item |
| `?` | Show help overlay |

---

## `testforge projects`

List all TestForge projects found in the current directory.

```
testforge projects
```

**Output:**
```
  my-webapp
  checkout-flow
  admin-portal
```

---

## `testforge selftest`

Run the built-in self-test suite to verify your TestForge installation.

```
testforge selftest [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Show stdout/stderr from each test script. |

**Examples:**

```bash
testforge selftest
testforge selftest --verbose
```

**Output:**
```
  running smoke.sh ... PASS
  running pipeline.sh ... PASS

Results: 2/2 passed  All tests passed.
```

**Exit codes:**
- `0` — all tests passed
- `1` — one or more tests failed
