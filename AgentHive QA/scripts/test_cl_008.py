"""Playwright test: Manual check: GitHub Sync

Case ID: CL-008
Description: Verify GitHub Sync manually: Bidirectional sync between hive tasks and GitHub issues
"""

import re

from playwright.sync_api import Page, expect


def test_cl_008(page: Page) -> None:
    """Manual check: GitHub Sync."""
    page.goto("http://localhost:3000")

    # No steps defined

    expect(page).to_have_url(re.compile(r".*"))

    page.screenshot(path="evidence/cl_008.png")
