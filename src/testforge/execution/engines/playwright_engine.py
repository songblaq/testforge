"""Playwright execution engine — runs pytest with Playwright fixtures."""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from testforge.execution.engines.base import BaseEngine, EngineResult


class PlaywrightEngine(BaseEngine):
    """Run Playwright test scripts via pytest."""

    name = "playwright"

    def __init__(self, headless: bool = True, timeout: float = 120.0, **kwargs: Any):
        self.headless = headless
        self.timeout = timeout

    def is_available(self) -> bool:
        try:
            import playwright  # noqa: F401
            return True
        except ImportError:
            return shutil.which("playwright") is not None

    def execute(self, script_path: Path, case_id: str, **kwargs: Any) -> EngineResult:
        timeout = kwargs.get("timeout", self.timeout)
        start = time.monotonic()
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(script_path), "-v", "--tb=short", "-q", "--no-header"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(script_path.parent.parent),
                env={**__import__("os").environ, "HEADLESS": "1" if self.headless else "0"},
            )
            duration_ms = int((time.monotonic() - start) * 1000)
            if result.returncode == 0:
                status = "passed"
            elif result.returncode in (4, 5):
                status = "skipped"
            else:
                status = "failed"
            return EngineResult(
                engine=self.name,
                case_id=case_id,
                status=status,
                duration_ms=duration_ms,
                output=result.stdout,
                error=result.stderr or None,
            )
        except subprocess.TimeoutExpired:
            duration_ms = int((time.monotonic() - start) * 1000)
            return EngineResult(
                engine=self.name, case_id=case_id, status="error",
                duration_ms=duration_ms, error="Timeout expired",
            )
        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            return EngineResult(
                engine=self.name, case_id=case_id, status="error",
                duration_ms=duration_ms, error=str(exc),
            )
