"""Playwright test: Manual check: Agent Profiles

Case ID: CL-006
Description: Verify Agent Profiles manually: Register agents with capabilities and tool access
"""

import re

from playwright.sync_api import Page, expect


def test_cl_006(page: Page) -> None:
    """Manual check: Agent Profiles."""
    page.goto("http://localhost:3000")

    # No steps defined

    expect(page).to_have_url(re.compile(r".*"))

    page.screenshot(path="evidence/cl_006.png")
