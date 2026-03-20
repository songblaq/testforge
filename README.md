# TestForge

> LLM-powered QA automation platform -- from documents to test reports

```
 _____ _____ ____ _____ _____ ___  ____   ____ _____
|_   _| ____/ ___|_   _|  ___/ _ \|  _ \ / ___| ____|
  | | |  _| \___ \ | | | |_ | | | | |_) | |  _|  _|
  | | | |___ ___) || | |  _|| |_| |  _ <| |_| | |___
  |_| |_____|____/ |_| |_|   \___/|_| \_\\____|_____|
```

## What is TestForge?

TestForge transforms project documents (PDFs, specs, designs, URLs) into comprehensive
test suites using LLM-powered analysis. It automates the entire QA pipeline:

```
  Documents        Analysis         Test Cases       Scripts          Execution        Reports
 +---------+     +---------+     +-----------+     +---------+     +-----------+     +---------+
 | PDF     |     | Feature |     | Functional|     |Playwright|    | Browser   |     | Markdown|
 | PPT     | --> | Extract | --> | Use Case  | --> | HTTP    | --> | API       | --> | HTML    |
 | Word    |     | Persona |     | Checklist |     | Shell   |     | Shell     |     | JSON    |
 | URL     |     | Rules   |     |           |     |         |     | SSH       |     |         |
 | GitHub  |     |         |     |           |     |         |     |           |     |         |
 +---------+     +---------+     +-----------+     +---------+     +-----------+     +---------+
```

## Features

- **Multi-format Input** -- PDF, PowerPoint, Word, Excel, images, URLs, GitHub repos
- **LLM-powered Analysis** -- Automatic feature extraction, persona derivation, business rule identification
- **Smart Test Generation** -- Functional tests, use case scenarios, manual checklists
- **Script Generation** -- Playwright browser tests, HTTP API tests, shell scripts
- **Flexible Execution** -- Browser, HTTP, shell, and SSH connectors
- **Evidence Collection** -- Screenshots, logs, network traces
- **Rich Reports** -- Markdown and HTML reports with evidence attachments

## Quick Start

```bash
# Install
pip install testforge

# With LLM support
pip install "testforge[anthropic]"   # Anthropic Claude
pip install "testforge[openai]"      # OpenAI GPT
pip install "testforge[all]"         # All providers

# Create a new project
testforge init my-project

# Analyze input documents
testforge analyze my-project --input spec.pdf --input design.pptx

# Generate test cases
testforge generate my-project

# Generate automation scripts
testforge script my-project --framework playwright

# Run tests
testforge run my-project

# Generate report
testforge report my-project --format html
```

## Pipeline

| Stage | Command | Description |
|-------|---------|-------------|
| 1. Init | `testforge init` | Create a new test project |
| 2. Analyze | `testforge analyze` | Parse inputs and extract features |
| 3. Generate | `testforge generate` | Generate test cases from analysis |
| 4. Script | `testforge script` | Generate automation scripts |
| 5. Run | `testforge run` | Execute test scripts |
| 6. Report | `testforge report` | Generate test reports |

## Requirements

- Python 3.11+
- For browser testing: Playwright (`playwright install`)
- For LLM features: API key for Anthropic or OpenAI

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

## License

Apache License 2.0 -- see [LICENSE](LICENSE) for details.

---

Part of the **LucaBlaq Tech Forge Series**
