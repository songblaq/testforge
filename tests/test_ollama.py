"""Tests for the Ollama LLM adapter (httpx mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from testforge.llm import create_adapter
from testforge.llm.ollama import OllamaAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(text: str = "hello", model: str = "llama3") -> MagicMock:
    """Build a fake httpx response for Ollama /api/chat."""
    resp = MagicMock()
    resp.json.return_value = {
        "model": model,
        "message": {"role": "assistant", "content": text},
        "done": True,
        "prompt_eval_count": 10,
        "eval_count": 5,
    }
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class TestCreateAdapterOllama:
    def test_factory_returns_ollama_adapter(self):
        adapter = create_adapter("ollama")
        assert isinstance(adapter, OllamaAdapter)

    def test_factory_passes_kwargs(self):
        adapter = create_adapter("ollama", base_url="http://myhost:11434", model="mistral")
        assert adapter.base_url == "http://myhost:11434"
        assert adapter.model == "mistral"

    def test_factory_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_adapter("nonexistent_provider_xyz")


# ---------------------------------------------------------------------------
# OllamaAdapter defaults
# ---------------------------------------------------------------------------


class TestOllamaAdapterDefaults:
    def test_default_base_url(self):
        adapter = OllamaAdapter()
        assert adapter.base_url == "http://localhost:11434"

    def test_default_model(self):
        adapter = OllamaAdapter()
        assert adapter.model == "llama3"

    def test_trailing_slash_stripped(self):
        adapter = OllamaAdapter(base_url="http://localhost:11434/")
        assert adapter.base_url == "http://localhost:11434"


# ---------------------------------------------------------------------------
# complete()
# ---------------------------------------------------------------------------


class TestOllamaComplete:
    def _adapter(self):
        return OllamaAdapter(base_url="http://localhost:11434", model="llama3")

    @patch("testforge.llm.ollama.OllamaAdapter._get_client")
    def test_complete_returns_text(self, mock_get_client):
        httpx_mock = MagicMock()
        httpx_mock.post.return_value = _mock_response("world")
        mock_get_client.return_value = httpx_mock

        adapter = self._adapter()
        result = adapter.complete("say hello")

        assert result.text == "world"
        assert result.model == "llama3"

    @patch("testforge.llm.ollama.OllamaAdapter._get_client")
    def test_complete_populates_usage(self, mock_get_client):
        httpx_mock = MagicMock()
        httpx_mock.post.return_value = _mock_response()
        mock_get_client.return_value = httpx_mock

        result = self._adapter().complete("prompt")

        assert result.usage["input_tokens"] == 10
        assert result.usage["output_tokens"] == 5

    @patch("testforge.llm.ollama.OllamaAdapter._get_client")
    def test_complete_sends_user_message(self, mock_get_client):
        httpx_mock = MagicMock()
        httpx_mock.post.return_value = _mock_response()
        mock_get_client.return_value = httpx_mock

        self._adapter().complete("my prompt")

        call_kwargs = httpx_mock.post.call_args
        payload = call_kwargs[1]["json"]
        assert any(m["role"] == "user" and m["content"] == "my prompt" for m in payload["messages"])

    @patch("testforge.llm.ollama.OllamaAdapter._get_client")
    def test_complete_with_system_prompt(self, mock_get_client):
        httpx_mock = MagicMock()
        httpx_mock.post.return_value = _mock_response()
        mock_get_client.return_value = httpx_mock

        self._adapter().complete("user msg", system_prompt="you are a tester")

        payload = httpx_mock.post.call_args[1]["json"]
        roles = [m["role"] for m in payload["messages"]]
        assert roles[0] == "system"
        assert payload["messages"][0]["content"] == "you are a tester"

    @patch("testforge.llm.ollama.OllamaAdapter._get_client")
    def test_complete_no_system_prompt_by_default(self, mock_get_client):
        httpx_mock = MagicMock()
        httpx_mock.post.return_value = _mock_response()
        mock_get_client.return_value = httpx_mock

        self._adapter().complete("hi")

        payload = httpx_mock.post.call_args[1]["json"]
        assert all(m["role"] != "system" for m in payload["messages"])

    @patch("testforge.llm.ollama.OllamaAdapter._get_client")
    def test_complete_posts_to_correct_url(self, mock_get_client):
        httpx_mock = MagicMock()
        httpx_mock.post.return_value = _mock_response()
        mock_get_client.return_value = httpx_mock

        self._adapter().complete("test")

        url = httpx_mock.post.call_args[0][0]
        assert url == "http://localhost:11434/api/chat"

    @patch("testforge.llm.ollama.OllamaAdapter._get_client")
    def test_complete_metadata_done_flag(self, mock_get_client):
        httpx_mock = MagicMock()
        httpx_mock.post.return_value = _mock_response()
        mock_get_client.return_value = httpx_mock

        result = self._adapter().complete("test")
        assert result.metadata["done"] is True


# ---------------------------------------------------------------------------
# complete_with_images()
# ---------------------------------------------------------------------------


class TestOllamaCompleteWithImages:
    def _adapter(self):
        return OllamaAdapter()

    @patch("testforge.llm.ollama.OllamaAdapter._get_client")
    def test_images_passed_in_payload(self, mock_get_client):
        httpx_mock = MagicMock()
        httpx_mock.post.return_value = _mock_response("described")
        mock_get_client.return_value = httpx_mock

        images = [
            {"media_type": "image/png", "base64": "aGVsbG8="},
            {"media_type": "image/jpeg", "base64": "d29ybGQ="},
        ]
        result = self._adapter().complete_with_images("describe this", images)

        assert result.text == "described"
        payload = httpx_mock.post.call_args[1]["json"]
        user_msg = next(m for m in payload["messages"] if m["role"] == "user")
        assert user_msg["images"] == ["aGVsbG8=", "d29ybGQ="]

    @patch("testforge.llm.ollama.OllamaAdapter._get_client")
    def test_images_with_system_prompt(self, mock_get_client):
        httpx_mock = MagicMock()
        httpx_mock.post.return_value = _mock_response()
        mock_get_client.return_value = httpx_mock

        self._adapter().complete_with_images(
            "describe",
            [{"media_type": "image/png", "base64": "abc"}],
            system_prompt="vision model",
        )

        payload = httpx_mock.post.call_args[1]["json"]
        assert payload["messages"][0]["role"] == "system"


# ---------------------------------------------------------------------------
# Missing httpx raises ImportError
# ---------------------------------------------------------------------------


class TestOllamaImportError:
    def test_missing_httpx_raises_import_error(self):
        import sys
        # Temporarily remove httpx from sys.modules
        original = sys.modules.pop("httpx", None)
        try:
            adapter = OllamaAdapter()
            # Force re-import by bypassing any cached reference
            with patch.dict(sys.modules, {"httpx": None}):
                with pytest.raises(ImportError, match="httpx"):
                    adapter._get_client()
        finally:
            if original is not None:
                sys.modules["httpx"] = original
