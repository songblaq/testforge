"""Agent-mode LLM adapter — delegates to the hosting AI agent runtime."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from typing import Any

from testforge.llm.adapter import LLMAdapter, LLMResponse

logger = logging.getLogger(__name__)


def detect_agent_runtime() -> str | None:
    """Detect if running inside an AI agent runtime.

    Returns the runtime name or None if not in an agent environment.
    """
    runtime = os.environ.get("ARIA_RUNTIME", "")
    if runtime:
        return runtime

    if os.environ.get("CURSOR_SESSION_ID"):
        return "cursor"
    if os.environ.get("CLAUDE_CODE"):
        return "claude-code"
    if os.environ.get("CODEX_ENV"):
        return "codex"
    if os.environ.get("AIDER_MODEL"):
        return "aider"
    if os.environ.get("GITHUB_COPILOT") or os.environ.get("COPILOT_ENV"):
        return "copilot"

    ppid = os.getppid()
    try:
        import psutil

        parent = psutil.Process(ppid)
        pname = parent.name().lower()
        if "cursor" in pname:
            return "cursor"
        if "claude" in pname:
            return "claude-code"
    except (ImportError, Exception):
        pass

    return None


class AgentAdapter(LLMAdapter):
    """LLM adapter that works in agent mode.

    In agent mode, TestForge generates structured prompts that the hosting
    agent can process. This adapter uses the CLI adapter pattern but with
    awareness of the agent environment.
    """

    def __init__(self, runtime: str | None = None, **kwargs: Any) -> None:
        _ = kwargs
        self.runtime = runtime or detect_agent_runtime() or "unknown"
        self._cli_command = self._resolve_cli_command()
        logger.info("AgentAdapter initialized for runtime: %s", self.runtime)

    def _resolve_cli_command(self) -> list[str] | None:
        """Find a CLI command that can process prompts."""
        candidates = {
            "cursor": None,
            "claude-code": ["claude", "--print"],
            "codex": ["codex", "--quiet"],
            "aider": ["aider", "--message"],
            "copilot": ["gh", "copilot", "suggest", "-t", "shell"],
        }
        cmd = candidates.get(self.runtime)
        if cmd and self._command_exists(cmd[0]):
            return cmd

        for tool_cmd in (["claude", "--print"], ["codex", "--quiet"]):
            if self._command_exists(tool_cmd[0]):
                return tool_cmd

        return None

    @staticmethod
    def _command_exists(cmd: str) -> bool:
        return shutil.which(cmd) is not None

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Complete using the agent's CLI tool or fallback."""
        if self._cli_command:
            return self._cli_complete(prompt, **kwargs)
        return self._fallback_complete(prompt, **kwargs)

    def complete_with_images(
        self, prompt: str, images: list[dict[str, str]], **kwargs: Any
    ) -> LLMResponse:
        """Multimodal completion — delegate to CLI with image descriptions."""
        enhanced_prompt = (
            f"{prompt}\n\n[Note: {len(images)} image(s) provided but cannot be "
            "processed in CLI mode. Analyze based on text context only.]"
        )
        return self.complete(enhanced_prompt, **kwargs)

    def _cli_complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Run completion via CLI tool."""
        _ = kwargs
        if not self._cli_command:
            raise RuntimeError("Agent CLI command not resolved")
        cmd = [*self._cli_command, prompt]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Agent CLI failed ({cmd[0]}): {result.stderr or result.stdout}"
                )
            return LLMResponse(
                text=result.stdout.strip(),
                model=f"agent:{self.runtime}",
                metadata={"runtime": self.runtime, "returncode": result.returncode},
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            logger.warning("Agent CLI failed: %s", exc)
            raise RuntimeError(f"Agent CLI unavailable: {exc}") from exc

    def _fallback_complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Try other available adapters as fallback."""
        try:
            from testforge.llm.ollama import OllamaAdapter

            adapter = OllamaAdapter()
            return adapter.complete(prompt, **kwargs)
        except Exception:
            pass

        from testforge.llm import create_adapter

        for env_key, provider in (
            ("ANTHROPIC_API_KEY", "anthropic"),
            ("OPENAI_API_KEY", "openai"),
        ):
            if os.environ.get(env_key):
                try:
                    adapter = create_adapter(provider)
                    return adapter.complete(prompt, **kwargs)
                except Exception:
                    continue

        raise RuntimeError(
            "No LLM available. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, "
            "run Ollama locally, or use TestForge inside an AI agent."
        )
