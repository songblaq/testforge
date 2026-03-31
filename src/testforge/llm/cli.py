"""CLI tool adapter -- use Claude Code, Codex, Cursor, or other CLI tools as LLM backends."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any

from testforge.llm.adapter import LLMAdapter, LLMResponse


@dataclass
class CLIProfile:
    """Configuration profile for a CLI-based LLM tool."""

    name: str
    command: str
    args_template: list[str]  # use {prompt} as placeholder
    supports_images: bool = False
    timeout: float = 120.0
    env: dict[str, str] = field(default_factory=dict)


# Built-in profiles
BUILTIN_PROFILES: dict[str, CLIProfile] = {
    "claude": CLIProfile(
        name="claude",
        command="claude",
        args_template=["--print", "{prompt}"],
    ),
    "codex": CLIProfile(
        name="codex",
        command="codex",
        args_template=["-q", "{prompt}"],
        timeout=180.0,
    ),
    "cursor": CLIProfile(
        name="cursor",
        command="cursor",
        args_template=["--message", "{prompt}"],
    ),
    "aider": CLIProfile(
        name="aider",
        command="aider",
        args_template=["--message", "{prompt}", "--yes"],
        timeout=180.0,
    ),
    "copilot": CLIProfile(
        name="copilot",
        command="gh",
        args_template=["copilot", "suggest", "-t", "shell", "{prompt}"],
        timeout=120.0,
    ),
}


def get_profile(name: str) -> CLIProfile | None:
    """Get a built-in CLI profile by name."""
    return BUILTIN_PROFILES.get(name)


def list_profiles() -> list[str]:
    """List all available built-in profile names."""
    return list(BUILTIN_PROFILES.keys())


class CLIAdapter(LLMAdapter):
    """LLM adapter that delegates to a CLI tool (e.g. claude, codex, cursor)."""

    def __init__(
        self,
        command: str = "claude",
        timeout: float = 120.0,
        profile: CLIProfile | None = None,
    ) -> None:
        if profile:
            self.profile = profile
        elif command in BUILTIN_PROFILES:
            self.profile = BUILTIN_PROFILES[command]
        else:
            # Custom command — use generic args pattern
            self.profile = CLIProfile(
                name=command,
                command=command,
                args_template=["--print", "{prompt}"],
                timeout=timeout,
            )

        self.command = self.profile.command
        self.timeout = self.profile.timeout

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Send a prompt to the CLI tool."""
        args = [
            arg.replace("{prompt}", prompt) for arg in self.profile.args_template
        ]

        result = subprocess.run(
            [self.command, *args],
            capture_output=True,
            text=True,
            timeout=self.timeout,
            env=self.profile.env or None,
        )

        if result.returncode != 0:
            raise RuntimeError(f"CLI command failed ({self.command}): {result.stderr}")

        return LLMResponse(
            text=result.stdout.strip(),
            model=f"cli:{self.profile.name}",
        )

    def complete_with_images(
        self, prompt: str, images: list[dict[str, str]], **kwargs: Any
    ) -> LLMResponse:
        """CLI tools typically do not support multimodal input directly."""
        if self.profile.supports_images:
            # Future: implement image passing for tools that support it
            pass
        raise NotImplementedError(
            f"Multimodal input not supported by CLI adapter ({self.command})"
        )
