"""CLI tool adapter -- use Claude Code, Codex, or other CLI tools as LLM backends."""

from __future__ import annotations

import subprocess
from typing import Any

from testforge.llm.adapter import LLMAdapter, LLMResponse


class CLIAdapter(LLMAdapter):
    """LLM adapter that delegates to a CLI tool (e.g. claude, codex)."""

    def __init__(self, command: str = "claude", timeout: float = 120.0) -> None:
        self.command = command
        self.timeout = timeout

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Send a prompt to the CLI tool via stdin."""
        result = subprocess.run(
            [self.command, "--print", prompt],
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )

        if result.returncode != 0:
            raise RuntimeError(f"CLI command failed: {result.stderr}")

        return LLMResponse(
            text=result.stdout.strip(),
            model=self.command,
        )

    def complete_with_images(
        self, prompt: str, images: list[dict[str, str]], **kwargs: Any
    ) -> LLMResponse:
        """CLI tools typically do not support multimodal input directly."""
        raise NotImplementedError(
            f"Multimodal input not supported by CLI adapter ({self.command})"
        )
