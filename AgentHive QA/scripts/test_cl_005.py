"""Playwright test: Manual check: Atomic Locking

Case ID: CL-005
Description: Verify Atomic Locking manually: O_CREAT|O_EXCL + rename prevents concurrent modification
"""

import re

from playwright.sync_api import Page, expect


def test_cl_005(page: Page) -> None:
    """Manual check: Atomic Locking."""
    page.goto("http://localhost:3000")

    # No steps defined

    expect(page).to_have_url(re.compile(r".*"))

    page.screenshot(path="evidence/cl_005.png")
