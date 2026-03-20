"""LLM adapter interface -- abstract base for provider implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """Response from an LLM call."""

    text: str
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMAdapter(ABC):
    """Abstract base class for LLM provider adapters."""

    @abstractmethod
    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Send a completion request to the LLM.

        Parameters
        ----------
        prompt:
            The prompt text.

        Returns
        -------
        LLMResponse:
            The model response.
        """

    @abstractmethod
    def complete_with_images(
        self, prompt: str, images: list[dict[str, str]], **kwargs: Any
    ) -> LLMResponse:
        """Send a multimodal completion request.

        Parameters
        ----------
        prompt:
            The prompt text.
        images:
            List of image dicts with ``media_type`` and ``base64`` keys.

        Returns
        -------
        LLMResponse:
            The model response.
        """
