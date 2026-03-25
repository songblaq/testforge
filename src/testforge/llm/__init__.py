"""LLM module -- adapters for various LLM providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from testforge.llm.adapter import LLMAdapter


def create_adapter(provider: str = "anthropic", **kwargs) -> "LLMAdapter":
    """Factory to create an LLM adapter by provider name.

    Parameters
    ----------
    provider:
        One of ``anthropic``, ``openai``, or ``cli``.
    **kwargs:
        Passed through to the adapter constructor.

    Returns
    -------
    LLMAdapter:
        Configured adapter instance.
    """
    if provider == "anthropic":
        from testforge.llm.anthropic import AnthropicAdapter

        return AnthropicAdapter(**kwargs)
    elif provider == "openai":
        from testforge.llm.openai import OpenAIAdapter

        return OpenAIAdapter(**kwargs)
    elif provider == "cli":
        from testforge.llm.cli import CLIAdapter

        return CLIAdapter(**kwargs)
    elif provider == "ollama":
        from testforge.llm.ollama import OllamaAdapter

        return OllamaAdapter(**kwargs)
    elif provider == "agent":
        from testforge.llm.agent import AgentAdapter

        return AgentAdapter(**kwargs)
    else:
        raise ValueError(f"Unknown LLM provider: {provider!r}")


def auto_create_adapter(**kwargs) -> "LLMAdapter":
    """Auto-detect and create the best available LLM adapter.

    Priority: agent runtime > environment API keys > Ollama > error
    """
    import os
    import urllib.error
    import urllib.request

    from testforge.llm.agent import detect_agent_runtime

    runtime = detect_agent_runtime()
    if runtime:
        from testforge.llm.agent import AgentAdapter

        return AgentAdapter(runtime=runtime, **kwargs)

    if os.environ.get("ANTHROPIC_API_KEY"):
        return create_adapter("anthropic", **kwargs)
    if os.environ.get("OPENAI_API_KEY"):
        return create_adapter("openai", **kwargs)

    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
    except (OSError, urllib.error.URLError):
        pass
    else:
        return create_adapter("ollama", **kwargs)

    raise ValueError(
        "No LLM provider available. Options:\n"
        "  1. Run inside an AI agent (Cursor, Claude Code)\n"
        "  2. Set ANTHROPIC_API_KEY or OPENAI_API_KEY\n"
        "  3. Run Ollama locally (free): ollama serve"
    )
