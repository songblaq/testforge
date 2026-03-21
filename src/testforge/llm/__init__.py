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
    else:
        raise ValueError(f"Unknown LLM provider: {provider!r}")
