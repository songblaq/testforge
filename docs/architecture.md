# TestForge Architecture

## Overview

TestForge follows a pipeline architecture where each stage transforms data
and passes it to the next stage.

```
Input -> Analysis -> Cases -> Scripts -> Execution -> Report
```

## Module Structure

### Core (`testforge.core`)
- **pipeline.py** -- Orchestrates the full pipeline
- **project.py** -- Project CRUD operations
- **config.py** -- YAML-based configuration management

### Input (`testforge.input`)
Parsers for different input formats:
- PDF (PyMuPDF)
- Office (python-pptx, python-docx, openpyxl)
- Images (base64 encoding for LLM vision)
- URLs (httpx crawler)
- GitHub repos (API metadata)

### Analysis (`testforge.analysis`)
LLM-powered extraction:
- **Features** -- Testable functionality
- **Personas** -- User types and behaviors
- **Rules** -- Business constraints

### Cases (`testforge.cases`)
Test case generation:
- Functional test cases
- Use case scenarios
- Manual test checklists

### Scripts (`testforge.scripts`)
Automation script generation:
- Playwright browser tests
- Script validation

### Execution (`testforge.execution`)
Test runners and connectors:
- Browser (Playwright)
- HTTP API (httpx)
- Shell (subprocess)
- SSH (placeholder)

### Assertions (`testforge.assertions`)
Verification logic:
- Image comparison
- API response validation
- Text matching
- File checks
- Custom callables

### Report (`testforge.report`)
Output formats:
- Markdown
- HTML

### LLM (`testforge.llm`)
Provider adapters:
- Anthropic Claude
- OpenAI GPT
- CLI tools (claude, codex)

## Data Flow

1. **Input stage** produces structured documents (dicts with text, metadata)
2. **Analysis stage** sends documents to LLM, extracts features/personas/rules
3. **Cases stage** generates test cases from analysis output
4. **Scripts stage** produces runnable automation scripts
5. **Execution stage** runs scripts, collects evidence (screenshots, logs)
6. **Report stage** aggregates results into human-readable reports
