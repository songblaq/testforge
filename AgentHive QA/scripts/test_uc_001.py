"""Playwright test: AI Agent -- primary workflow

Case ID: UC-001
Description: End-to-end scenario for AI Agent
"""

import re

from playwright.sync_api import Page, expect


def test_uc_001(page: Page) -> None:
    """AI Agent -- primary workflow."""
    # Preconditions:
    #   - User is authenticated
    #   - System is in default state

    page.goto("http://localhost:3000")

    # No steps defined

    expect(page).to_have_url(re.compile(r".*"))

    page.screenshot(path="evidence/uc_001.png")
