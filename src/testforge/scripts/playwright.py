"""Playwright script generation -- produce browser automation scripts."""

from __future__ import annotations

import ast
import json
import logging
import re
from pathlib import Path
from typing import Any

from testforge.core.config import (
    append_locale_user_facing_instruction,
    effective_locale,
    load_config,
)
from testforge.core.locale_strings import s
from testforge.core.project import load_cases

logger = logging.getLogger(__name__)


def _case_steps(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve steps for a case, including legacy scenario_steps / check_steps."""
    steps = case.get("steps", [])
    if not steps:
        for alt_key in ("scenario_steps", "check_steps"):
            alt = case.get(alt_key, [])
            if alt:
                steps = [
                    {"order": i + 1, "action": s, "expected_result": "", "input_data": ""}
                    for i, s in enumerate(alt)
                ]
                break
    return steps


def generate_playwright_scripts(project_dir: Path, no_llm: bool = False) -> list[dict[str, Any]]:
    """Generate Playwright test scripts from test cases.

    Parameters
    ----------
    project_dir:
        Root of the TestForge project.

    Returns
    -------
    list[dict]:
        Generated Playwright script metadata.  Each entry has keys
        ``case_id``, ``title``, ``path``, and ``source``.
    """
    cases = load_cases(project_dir)
    if not cases:
        logger.info("No test cases found; skipping Playwright script generation")
        return []

    config = load_config(project_dir)
    base_url = config.extra.get("base_url", "http://localhost:3000")

    locale = effective_locale(config)

    if no_llm:
        return _generate_skeleton_scripts(cases, base_url, locale)

    # Try LLM-powered generation
    from testforge.llm import create_adapter

    adapter_kwargs: dict[str, Any] = {}
    if config.llm_model:
        adapter_kwargs["model"] = config.llm_model

    try:
        adapter = create_adapter(config.llm_provider, **adapter_kwargs)
    except (ValueError, ImportError) as exc:
        logger.warning("LLM unavailable (%s), generating skeleton scripts", exc)
        return _generate_skeleton_scripts(cases, base_url, locale)

    try:
        return _llm_generate_scripts(
            adapter, cases, base_url, locale
        )
    except Exception as exc:
        logger.warning("LLM generation failed (%s), generating skeleton scripts", exc)
        return _generate_skeleton_scripts(cases, base_url, locale)


def _llm_generate_scripts(
    adapter: Any,
    cases: list[dict[str, Any]],
    base_url: str,
    locale: str = "ko",
) -> list[dict[str, Any]]:
    """Use LLM to generate Playwright Python scripts for each test case."""
    results: list[dict[str, Any]] = []

    for case in cases:
        case_id = case.get("id", "TC-UNKNOWN")
        title = case.get("title", "Untitled")
        steps = _case_steps(case)

        steps_text = "\n".join(
            f"  {s.get('order', i+1)}. Action: {s.get('action', '')} "
            f"-> Expected: {s.get('expected_result', '')}"
            for i, s in enumerate(steps)
        )

        prompt = f"""Generate a Playwright Python test script for the following test case.

TEST CASE:
- ID: {case_id}
- Title: {title}
- Description: {case.get('description', '')}
- Preconditions: {json.dumps(case.get('preconditions', []))}
- Steps:
{steps_text}
- Expected Result: {case.get('expected_result', '')}

BASE URL: {base_url}

Requirements:
- Use `playwright.sync_api` (sync mode)
- Include `import re` and `from playwright.sync_api import Page, expect`
- Define a function `test_{_sanitize_id(case_id)}(page: Page) -> None`
- Navigate to the base URL first
- Implement each step as Playwright actions with comments
- Add assertions matching expected results
- Take a screenshot at the end
- Use `expect()` for assertions where possible

Return ONLY the Python code, no markdown fences or explanation."""
        prompt = append_locale_user_facing_instruction(prompt, locale)

        response = adapter.complete(prompt, max_tokens=2048)
        source = _extract_python_code(response.text)

        # Validate syntax
        if not _is_valid_python(source):
            logger.warning(
                "LLM-generated script for %s failed syntax check, using skeleton",
                case_id,
            )
            source = _skeleton_script(case, base_url, locale)

        results.append(
            {
                "case_id": case_id,
                "title": title,
                "path": f"test_{_sanitize_id(case_id)}.py",
                "source": source,
            }
        )

    return results


def _generate_skeleton_scripts(
    cases: list[dict[str, Any]], base_url: str, locale: str = "ko"
) -> list[dict[str, Any]]:
    """Generate minimal skeleton Playwright scripts without LLM."""
    results: list[dict[str, Any]] = []

    for case in cases:
        case_id = case.get("id", "TC-UNKNOWN")
        title = case.get("title", "Untitled")
        source = _skeleton_script(case, base_url, locale)

        results.append(
            {
                "case_id": case_id,
                "title": title,
                "path": f"test_{_sanitize_id(case_id)}.py",
                "source": source,
            }
        )

    return results


def _skeleton_script(case: dict[str, Any], base_url: str, locale: str = "ko") -> str:
    """Build a skeleton Playwright Python test script for a single case."""
    case_id = case.get("id", "TC-UNKNOWN")
    title = case.get("title", "Untitled")
    description = case.get("description", "")
    preconditions = case.get("preconditions", [])
    steps = _case_steps(case)
    expected_result = case.get("expected_result", "")

    func_name = f"test_{_sanitize_id(case_id)}"

    lines: list[str] = []
    lines.append(f'"""Playwright test: {title}')
    lines.append("")
    lines.append(f"Case ID: {case_id}")
    if description:
        lines.append(f"Description: {description}")
    lines.append('"""')
    lines.append("")
    lines.append("import re")
    lines.append("")
    lines.append("from playwright.sync_api import Page, expect")
    lines.append("")
    lines.append("")

    # Function definition
    lines.append(f"def {func_name}(page: Page) -> None:")
    lines.append(f'    """{title}."""')

    # Preconditions as comments
    if preconditions:
        lines.append("    # Preconditions:")
        for pre in preconditions:
            lines.append(f"    #   - {pre}")
        lines.append("")

    # Skip skeleton tests when no real target URL is configured
    if base_url == "http://localhost:3000":
        lines.append('    import pytest')
        lines.append('    if not page.context.browser:')
        lines.append('        pytest.skip("Skeleton test -- configure base_url in .testforge/config.yaml")')
        lines.append('    try:')
        lines.append(f'        page.goto("{base_url}", timeout=5000)')
        lines.append('    except Exception:')
        lines.append(f'        pytest.skip("Target {base_url} not reachable -- skeleton test")')
    else:
        lines.append(f'    page.goto("{base_url}")')
    lines.append("")

    # Steps
    if steps:
        for i, step in enumerate(steps):
            order = step.get("order", i + 1)
            action = step.get("action", "Perform action")
            exp = step.get("expected_result", "")
            lines.append(f"    # {s('step_n', locale, n=order)}: {action}")
            if exp:
                lines.append(f"    # Expected: {exp}")
            lines.append(f"    {s('todo_implement', locale)}")
            lines.append("")
    else:
        lines.append("    # No steps defined")
        lines.append("")

    # Final assertion
    if expected_result:
        lines.append(f"    # Overall expected result: {expected_result}")
    lines.append('    expect(page).to_have_url(re.compile(r".*"))')
    lines.append("")

    # Screenshot
    lines.append(f'    page.screenshot(path="evidence/{_sanitize_id(case_id)}.png")')
    lines.append("")

    # Main block for direct execution (pytest collects test_* without this)
    lines.append("")
    lines.append("")
    lines.append('if __name__ == "__main__":')
    lines.append("    from playwright.sync_api import sync_playwright")
    lines.append("    with sync_playwright() as pw:")
    lines.append('        browser = pw.chromium.launch(headless=True)')
    lines.append("        page = browser.new_page()")
    lines.append("        try:")
    lines.append(f"            {func_name}(page)")
    lines.append('            print("PASSED")')
    lines.append("        except Exception as e:")
    lines.append('            print(f"FAILED: {e}")')
    lines.append("            raise")
    lines.append("        finally:")
    lines.append("            browser.close()")

    return "\n".join(lines)


# Written alongside generated scripts by generator.generate_scripts (if missing).
PLAYWRIGHT_CONFTEST_PY = '''"""Shared Playwright fixtures for TestForge generated tests."""
import pytest

try:
    from playwright.sync_api import sync_playwright
    _HAS_PLAYWRIGHT = True
except ImportError:
    _HAS_PLAYWRIGHT = False


@pytest.fixture(scope="session")
def browser():
    """Launch browser once per test session."""
    if not _HAS_PLAYWRIGHT:
        pytest.skip("Playwright not installed or browser not available")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            yield browser
            browser.close()
    except Exception:
        pytest.skip("Playwright not installed or browser not available")


@pytest.fixture
def page(browser):
    """Create a new page for each test."""
    page = browser.new_page()
    yield page
    page.close()
'''


def _sanitize_id(case_id: str) -> str:
    """Convert a case ID to a valid Python identifier fragment."""
    return re.sub(r"[^a-zA-Z0-9]", "_", case_id).strip("_").lower()


def _extract_python_code(text: str) -> str:
    """Extract Python code from LLM response, stripping markdown fences."""
    cleaned = text.strip()

    # Strip markdown code fences
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Drop opening fence (```python or ```)
        lines = lines[1:]
        # Drop closing fence
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    return cleaned.strip()


def _is_valid_python(source: str) -> bool:
    """Check whether *source* is syntactically valid Python."""
    try:
        ast.parse(source)
        return True
    except SyntaxError:
        return False
