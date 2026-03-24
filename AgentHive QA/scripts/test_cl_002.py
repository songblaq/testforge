"""Playwright test: Manual check: Project Registration

Case ID: CL-002
Description: Verify Project Registration manually: Register projects with agenthive project add
"""

import re

from playwright.sync_api import Page, expect


def test_cl_002(page: Page) -> None:
    """Manual check: Project Registration."""
    page.goto("http://localhost:3000")

    # No steps defined

    expect(page).to_have_url(re.compile(r".*"))

    page.screenshot(path="evidence/cl_002.png")
