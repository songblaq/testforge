"""Agent Browser execution engine — Vercel's headless browser automation."""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from testforge.execution.engines.base import BaseEngine, EngineResult


class AgentBrowserEngine(BaseEngine):
    """Run tests using Vercel's agent-browser."""

    name = "agent-browser"

    def __init__(self, timeout: float = 180.0, **kwargs: Any):
        self.timeout = timeout

    def is_available(self) -> bool:
        return shutil.which("npx") is not None

    def _build_task(self, script_path: Path) -> str:
        """Build a task description from a test script or case file."""
        content = script_path.read_text(errors="replace")
        if script_path.suffix == ".json":
            try:
                case = json.loads(content)
                return json.dumps({
                    "url": case.get("base_url", "http://localhost:3000"),
                    "task": case.get("title", ""),
                    "steps": [
                        s.get("action", "") if isinstance(s, dict) else str(s)
                        for s in case.get("steps", [])
                    ],
                    "expected": case.get("expected_result", ""),
                })
            except json.JSONDecodeError:
                pass
        return content[:2000]

    def execute(self, script_path: Path, case_id: str, **kwargs: Any) -> EngineResult:
        timeout = kwargs.get("timeout", self.timeout)
        task = self._build_task(script_path)

        pkg = kwargs.get("package", "agent-browser@latest")
        cmd = ["npx", "-y", pkg, "--task", task]

        start = time.monotonic()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(script_path.parent),
            )
            duration_ms = int((time.monotonic() - start) * 1000)
            status = "passed" if result.returncode == 0 else "failed"

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
