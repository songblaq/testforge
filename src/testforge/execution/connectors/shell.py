"""Shell connector -- execute commands in a local shell."""

from __future__ import annotations

import subprocess
import time
from typing import Any

from testforge.execution.connectors.base import BaseConnector


class ShellConnector(BaseConnector):
    """Execute tests via local shell commands."""

    def __init__(self, cwd: str | None = None, timeout: float = 60.0) -> None:
        self.cwd = cwd
        self.timeout = timeout

    def connect(self) -> None:
        """No-op for shell connector."""

    def execute(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a shell command.

        *command* is expected to be a path to a Python script.  It is split
        into ``["python", <path>]`` so that ``shell=True`` is never used,
        preventing command-injection attacks.
        """
        start = time.monotonic()
        result = subprocess.run(
            ["python", str(command)],
            shell=False,
            capture_output=True,
            text=True,
            cwd=self.cwd,
            timeout=self.timeout,
        )
        duration = time.monotonic() - start

        return {
            "status": "passed" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "duration": duration,
        }

    def disconnect(self) -> None:
        """No-op for shell connector."""
