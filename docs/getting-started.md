# Getting Started with TestForge

## Installation

```bash
pip install testforge
```

For LLM-powered features, install with provider extras:

```bash
pip install "testforge[anthropic]"   # Anthropic Claude
pip install "testforge[openai]"      # OpenAI GPT
pip install "testforge[all]"         # All providers
```

For browser testing, install Playwright browsers:

```bash
playwright install chromium
```

## Create a Project

```bash
testforge init my-app
cd my-app
```

This creates a project directory with:
```
my-app/
  .testforge/config.yaml
  inputs/
  output/
  evidence/
  scripts/
  cases/
```

## Analyze Documents

Place your input documents (specs, designs, screenshots) in the `inputs/` directory,
then run analysis:

```bash
testforge analyze my-app --input inputs/spec.pdf --input inputs/design.pptx
```

## Generate Test Cases

```bash
testforge generate my-app                  # All types
testforge generate my-app -t functional    # Functional only
testforge generate my-app -t checklist     # Manual checklist
```

## Generate Scripts

```bash
testforge script my-app --framework playwright
```

## Run Tests

```bash
testforge run my-app
testforge run my-app -t smoke           # Filter by tag
testforge run my-app -p 4               # 4 parallel workers
```

## Generate Reports

```bash
testforge report my-app                  # Markdown (default)
testforge report my-app -f html          # HTML report
testforge report my-app -o report.html   # Custom output path
```

## Configuration

Edit `.testforge/config.yaml` in your project directory:

```yaml
project_name: my-app
version: "0.1.0"
llm_provider: anthropic
llm_model: ""
input_dir: inputs
output_dir: output
evidence_dir: evidence
```

## Environment Variables

- `ANTHROPIC_API_KEY` -- API key for Anthropic Claude
- `OPENAI_API_KEY` -- API key for OpenAI
