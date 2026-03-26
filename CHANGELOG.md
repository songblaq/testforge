# Changelog

All notable changes to TestForge are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Version tags follow **Semantic Versioning** (`MAJOR.MINOR.PATCH`).

---

## [0.5.0] — 2026-03-26

### Added

- Security hardening: form validation, XSS-focused defenses, upload size limits, focus trap, and loading states for critical Web GUI flows.
- Phantom Panel review sign-off and supporting hardening.

---

## [0.4.0] — 2026-03-26

### Added

- CLI and GUI dogfooding test suites.

### Changed

- Playwright `conftest.py` auto-generation when needed for generated suites.
- README and docs accuracy aligned with shipped behavior.

---

## [0.3.0] — 2026-03-25

### Added

- Web GUI (FastAPI + SPA): project workflow, visual test case **CRUD**, and pipeline-oriented UX.
- Internationalization for three languages (English, Korean, Vietnamese).
- Test runner integration in the GUI and **LLM setup wizard** flows.

---

## [0.1.0] — 2026-03-22

### Added

- **Core pipeline** — `init`, `analyze`, `generate`, `script`, `run`, `report`, `pipeline` commands
- **Multi-format input parsing** — PDF (PyMuPDF), PowerPoint (python-pptx), Word (python-docx),
  Excel (openpyxl), plain text, images, and URL scraping
- **LLM-powered analysis** — feature extraction, persona derivation, and business-rule identification
  via Anthropic Claude, OpenAI GPT, or CLI tools (`claude`, `codex`)
- **Test case generation** — functional tests, use-case scenarios, and manual QA checklists
- **Script generation** — Playwright-based Python test scripts only (LLM-powered with skeleton fallback);
  additional frameworks not yet implemented
- **Default execution** — `testforge run` executes generated Playwright-based tests via pytest; HTTP and
  shell connector usage is partial or extension-focused (SSH placeholder)
- **Evidence collection** — screenshots and logs per test run; HAR capture planned (helper plumbing only)
- **Rich reports** — Markdown and HTML report formats with evidence attachments
- **Manual QA workflow** — `testforge manual start/check/progress/finish` checklist commands
- **Coverage tracking** — `testforge coverage` shows feature and rule coverage gaps
- **TUI interface** — full interactive terminal UI via `textual` (optional extra)
- **Multi-project management** — `testforge projects` lists all local projects
- **Self-test / dogfooding** — `testforge selftest` runs TestForge against itself
- **`--no-llm` flag** — global CLI option to force offline mode and suppress LLM warnings
- **`--non-interactive` / `-y` flag** — global CLI option to skip confirmation prompts

### Notes

- **Ollama** is supported via `llm_provider: ollama` and local model configuration (see README).
- `playwright` is an **optional dependency** (`pip install "testforge[browser]"`)
- SSH connector is a placeholder; full implementation is planned for a future release

[0.5.0]: https://github.com/songblaq/testforge/releases/tag/v0.5.0
[0.4.0]: https://github.com/songblaq/testforge/releases/tag/v0.4.0
[0.3.0]: https://github.com/songblaq/testforge/releases/tag/v0.3.0
[0.1.0]: https://github.com/songblaq/testforge/releases/tag/v0.1.0
