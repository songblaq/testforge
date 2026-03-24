"""Playwright test: Manual check: Convention Injection

Case ID: CL-007
Description: Verify Convention Injection manually: Define coding standards once, inject into all tools
"""

import re

from playwright.sync_api import Page, expect


def test_cl_007(page: Page) -> None:
    """Manual check: Convention Injection."""
    page.goto("http://localhost:3000")

    # No steps defined

    expect(page).to_have_url(re.compile(r".*"))

    page.screenshot(path="evidence/cl_007.png")
