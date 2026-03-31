"""Expect execution engine — AI-powered browser testing via expect-cli."""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from testforge.execution.engines.base import BaseEngine, EngineResult


class ExpectEngine(BaseEngine):
    """Run tests using the expect CLI (AI-powered browser testing)."""

    name = "expect"

    def __init__(
        self,
        agent: str = "claude",
        headed: bool = False,
        ci: bool = False,
        timeout: float = 300.0,
        **kwargs: Any,
    ):
        self.agent = agent
        self.headed = headed
        self.ci = ci
        self.timeout = timeout

    def is_available(self) -> bool:
        return shutil.which("expect") is not None

    def _build_message(self, script_path: Path) -> str:
        """Build a natural-language test message from the script or case file."""
        content = script_path.read_text(errors="replace")
        # If it's a JSON case file, extract structured info
        if script_path.suffix == ".json":
            try:
                case = json.loads(content)
                parts = [f"Test: {case.get('title', '')}"]
                for step in case.get("steps", []):
                    action = step.get("action", "") if isinstance(step, dict) else str(step)
                    parts.append(f"- {action}")
                if case.get("expected_result"):
                    parts.append(f"Expected: {case['expected_result']}")
                return "\n".join(parts)
            except json.JSONDecodeError:
                pass
        # If it's a Python script, extract docstring or comments
        lines = content.split("\n")
        doc_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                doc_lines.append(stripped.strip('"').strip("'"))
            elif stripped.startswith("#") and not stripped.startswith("#!"):
                doc_lines.append(stripped.lstrip("# "))
        if doc_lines:
            return "\n".join(doc_lines[:20])
        return f"{script_path.stem} 기능 테스트"

    def execute(self, script_path: Path, case_id: str, **kwargs: Any) -> EngineResult:
        timeout = kwargs.get("timeout", self.timeout)
        message = self._build_message(script_path)

        cmd = ["expect", "-m", message, "-y", "--output", "json"]
        if self.agent:
            cmd.extend(["-a", self.agent])
        if self.headed:
            cmd.append("--headed")
        if self.ci:
            cmd.append("--ci")
        cmd.extend(["--timeout", str(int(timeout * 1000))])

        start = time.monotonic()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 30,  # extra buffer
                cwd=str(script_path.parent),
            )
            duration_ms = int((time.monotonic() - start) * 1000)

            # Parse JSON output if available
            output = result.stdout
            try:
                data = json.loads(output)
                status = "passed" if data.get("success", False) else "failed"
                artifacts = data.get("artifacts", [])
            except (json.JSONDecodeError, TypeError):
                status = "passed" if result.returncode == 0 else "failed"
                artifacts = []

            return EngineResult(
                engine=self.name,
                case_id=case_id,
                status=status,
                duration_ms=duration_ms,
                output=output,
                error=result.stderr or None,
                artifacts=artifacts,
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
