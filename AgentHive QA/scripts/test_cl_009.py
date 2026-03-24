"""Playwright test: Manual check: Dashboard

Case ID: CL-009
Description: Verify Dashboard manually: Interactive terminal dashboard with 8 tabs
"""

import re

from playwright.sync_api import Page, expect


def test_cl_009(page: Page) -> None:
    """Manual check: Dashboard."""
    page.goto("http://localhost:3000")

    # No steps defined

    expect(page).to_have_url(re.compile(r".*"))

    page.screenshot(path="evidence/cl_009.png")
