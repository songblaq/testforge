"""OpenAI GPT adapter."""

from __future__ import annotations

from typing import Any

from testforge.llm.adapter import LLMAdapter, LLMResponse


class OpenAIAdapter(LLMAdapter):
    """LLM adapter for OpenAI models."""

    def __init__(self, model: str = "gpt-4o", api_key: str | None = None) -> None:
        self.model = model
        self._api_key = api_key

    def _get_client(self) -> Any:
        """Lazily create the OpenAI client."""
        try:
            import openai
        except ImportError as exc:
            raise ImportError(
                "openai package required: pip install 'testforge[openai]'"
            ) from exc

        return openai.OpenAI(api_key=self._api_key)

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Send a text completion request to OpenAI."""
        client = self._get_client()

        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            text=choice.message.content or "",
            model=response.model,
            usage={
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
            },
        )

    def complete_with_images(
        self, prompt: str, images: list[dict[str, str]], **kwargs: Any
    ) -> LLMResponse:
        """Send a multimodal request to OpenAI."""
        client = self._get_client()

        content: list[dict[str, Any]] = []
        for img in images:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{img['media_type']};base64,{img['base64']}",
                },
            })
        content.append({"type": "text", "text": prompt})

        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
            **kwargs,
        )

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            text=choice.message.content or "",
            model=response.model,
            usage={
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
            },
        )
