"""Ollama local LLM adapter."""

from __future__ import annotations

import base64
from typing import Any

from testforge.llm.adapter import LLMAdapter, LLMResponse


class OllamaAdapter(LLMAdapter):
    """Ollama local LLM adapter.

    Communicates with a running Ollama server via its HTTP API.

    Parameters
    ----------
    base_url:
        Base URL of the Ollama server.  Defaults to ``http://localhost:11434``.
    model:
        Model name to use.  Defaults to ``llama3``.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _get_client(self) -> Any:
        """Return an httpx client (lazily imported)."""
        try:
            import httpx
        except ImportError as exc:
            raise ImportError(
                "httpx package required: pip install 'testforge[ollama]'"
            ) from exc
        return httpx

    def complete(self, prompt: str, system_prompt: str | None = None, **kwargs: Any) -> LLMResponse:
        """Send a text completion request to Ollama.

        Parameters
        ----------
        prompt:
            The user prompt.
        system_prompt:
            Optional system prompt injected as a system message.
        **kwargs:
            Additional parameters forwarded to the Ollama ``/api/chat`` endpoint
            (e.g. ``temperature``, ``stream``).

        Returns
        -------
        LLMResponse:
            The model response.
        """
        httpx = self._get_client()

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            **kwargs,
        }

        response = httpx.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()

        text = data.get("message", {}).get("content", "")
        usage: dict[str, int] = {}
        if "prompt_eval_count" in data:
            usage["input_tokens"] = data["prompt_eval_count"]
        if "eval_count" in data:
            usage["output_tokens"] = data["eval_count"]

        return LLMResponse(
            text=text,
            model=data.get("model", self.model),
            usage=usage,
            metadata={"done": data.get("done", True)},
        )

    def complete_with_images(
        self,
        prompt: str,
        images: list[dict[str, str]],
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a multimodal completion request to Ollama.

        Parameters
        ----------
        prompt:
            The user prompt.
        images:
            List of image dicts with ``media_type`` and ``base64`` keys.
        system_prompt:
            Optional system prompt.
        **kwargs:
            Additional parameters forwarded to ``/api/chat``.

        Returns
        -------
        LLMResponse:
            The model response.
        """
        httpx = self._get_client()

        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Ollama accepts base64-encoded image strings in the ``images`` field
        image_data = [img["base64"] for img in images]
        messages.append({"role": "user", "content": prompt, "images": image_data})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            **kwargs,
        }

        response = httpx.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()

        text = data.get("message", {}).get("content", "")
        usage: dict[str, int] = {}
        if "prompt_eval_count" in data:
            usage["input_tokens"] = data["prompt_eval_count"]
        if "eval_count" in data:
            usage["output_tokens"] = data["eval_count"]

        return LLMResponse(
            text=text,
            model=data.get("model", self.model),
            usage=usage,
            metadata={"done": data.get("done", True)},
        )
