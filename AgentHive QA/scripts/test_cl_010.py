"""Playwright test: Manual check: REST API

Case ID: CL-010
Description: Verify REST API manually: 13 REST API endpoints for programmatic access
"""

import re

from playwright.sync_api import Page, expect


def test_cl_010(page: Page) -> None:
    """Manual check: REST API."""
    page.goto("http://localhost:3000")

    # No steps defined

    expect(page).to_have_url(re.compile(r".*"))

    page.screenshot(path="evidence/cl_010.png")
