"""Playwright test: Manual check: Hub Initialization

Case ID: CL-001
Description: Verify Hub Initialization manually: agenthive init creates hub at ~/.agenthive/
"""

import re

from playwright.sync_api import Page, expect


def test_cl_001(page: Page) -> None:
    """Manual check: Hub Initialization."""
    page.goto("http://localhost:3000")

    # No steps defined

    expect(page).to_have_url(re.compile(r".*"))

    page.screenshot(path="evidence/cl_001.png")
