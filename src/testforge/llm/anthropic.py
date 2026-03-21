"""Anthropic Claude adapter."""

from __future__ import annotations

from typing import Any

from testforge.llm.adapter import LLMAdapter, LLMResponse


class AnthropicAdapter(LLMAdapter):
    """LLM adapter for Anthropic Claude models."""

    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: str | None = None) -> None:
        self.model = model
        self._api_key = api_key

    def _get_client(self) -> Any:
        """Lazily create the Anthropic client."""
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "anthropic package required: pip install 'testforge[anthropic]'"
            ) from exc

        return anthropic.Anthropic(api_key=self._api_key)

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Send a text completion request to Claude."""
        client = self._get_client()
        max_tokens = kwargs.pop("max_tokens", 4096)

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )

        return LLMResponse(
            text=response.content[0].text if response.content else "",
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

    def complete_with_images(
        self, prompt: str, images: list[dict[str, str]], **kwargs: Any
    ) -> LLMResponse:
        """Send a multimodal request to Claude."""
        client = self._get_client()
        max_tokens = kwargs.pop("max_tokens", 4096)

        content: list[dict[str, Any]] = []
        for img in images:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img["media_type"],
                    "data": img["base64"],
                },
            })
        content.append({"type": "text", "text": prompt})

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": content}],
            **kwargs,
        )

        return LLMResponse(
            text=response.content[0].text if response.content else "",
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )
