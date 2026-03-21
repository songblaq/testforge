"""Browser connector -- Playwright-based browser automation."""

from __future__ import annotations

import subprocess
import time
from typing import Any

from testforge.execution.connectors.base import BaseConnector


class BrowserConnector(BaseConnector):
    """Execute tests in a browser using Playwright."""

    def __init__(self, headless: bool = True, base_url: str = "") -> None:
        self.headless = headless
        self.base_url = base_url
        self._browser: Any = None
        self._playwright: Any = None

    def connect(self) -> None:
        """Launch browser and optionally verify base_url is reachable."""
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)

        if self.base_url:
            page = self._browser.new_page()
            try:
                page.goto(self.base_url, timeout=10_000)
            finally:
                page.close()

    def execute(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a test script as a subprocess and collect output.

        *command* is interpreted as a Python script path to run.
        """
        start = time.monotonic()
        try:
            result = subprocess.run(
                ["python", command],
                capture_output=True,
                text=True,
                timeout=kwargs.get("timeout", 120),
            )
            duration = time.monotonic() - start
            status = "passed" if result.returncode == 0 else "failed"
            return {
                "status": status,
                "output": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "duration": duration,
            }
        except subprocess.TimeoutExpired:
            duration = time.monotonic() - start
            return {
                "status": "failed",
                "output": "",
                "stderr": "Timeout",
                "returncode": -1,
                "duration": duration,
            }

    def disconnect(self) -> None:
        """Close browser."""
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
