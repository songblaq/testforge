# Changelog

All notable changes to TestForge are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
TestForge uses [calendar versioning](https://calver.org/) for releases.

---

## [0.1.0] — 2026-03-22

### Added

- **Core pipeline** — `init`, `analyze`, `generate`, `script`, `run`, `report`, `pipeline` commands
- **Multi-format input parsing** — PDF (PyMuPDF), PowerPoint (python-pptx), Word (python-docx),
  Excel (openpyxl), plain text, images, and URL scraping
- **LLM-powered analysis** — feature extraction, persona derivation, and business-rule identification
  via Anthropic Claude, OpenAI GPT, or CLI tools (`claude`, `codex`)
- **Test case generation** — functional tests, use-case scenarios, and manual QA checklists
- **Script generation** — Playwright browser tests (LLM-powered with skeleton fallback),
  HTTP API scripts, and shell scripts
- **Execution connectors** — Browser (Playwright, optional), HTTP (httpx), Shell (subprocess);
  SSH connector placeholder for future extension
- **Evidence collection** — screenshots, logs, and HAR traces per test run
- **Rich reports** — Markdown and HTML report formats with evidence attachments
- **Manual QA workflow** — `testforge manual start/check/progress/finish` checklist commands
- **Coverage tracking** — `testforge coverage` shows feature and rule coverage gaps
- **TUI interface** — full interactive terminal UI via `textual` (optional extra)
- **Multi-project management** — `testforge projects` lists all local projects
- **Self-test / dogfooding** — `testforge selftest` runs TestForge against itself
- **`--no-llm` flag** — global CLI option to force offline mode and suppress LLM warnings
- **`--non-interactive` / `-y` flag** — global CLI option to skip confirmation prompts

### Notes

- Ollama local-inference support is **coming in v0.2**
- `playwright` is now an **optional dependency** (`pip install "testforge[browser]"`)
- SSH connector is a placeholder; full implementation is planned for a future release

[0.1.0]: https://github.com/songblaq/testforge/releases/tag/v0.1.0
