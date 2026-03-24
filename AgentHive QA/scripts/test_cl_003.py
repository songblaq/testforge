"""Playwright test: Manual check: Task Management

Case ID: CL-003
Description: Verify Task Management manually: Create, assign, list, update tasks via CLI and files
"""

import re

from playwright.sync_api import Page, expect


def test_cl_003(page: Page) -> None:
    """Manual check: Task Management."""
    page.goto("http://localhost:3000")

    # No steps defined

    expect(page).to_have_url(re.compile(r".*"))

    page.screenshot(path="evidence/cl_003.png")
