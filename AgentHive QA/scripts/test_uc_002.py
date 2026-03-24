"""Playwright test: Developer -- primary workflow

Case ID: UC-002
Description: End-to-end scenario for Developer
"""

import re

from playwright.sync_api import Page, expect


def test_uc_002(page: Page) -> None:
    """Developer -- primary workflow."""
    # Preconditions:
    #   - User is authenticated
    #   - System is in default state

    page.goto("http://localhost:3000")

    # No steps defined

    expect(page).to_have_url(re.compile(r".*"))

    page.screenshot(path="evidence/uc_002.png")
