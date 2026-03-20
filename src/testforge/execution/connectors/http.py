"""HTTP API connector -- execute API tests via httpx."""

from __future__ import annotations

import time
from typing import Any

import httpx

from testforge.execution.connectors.base import BaseConnector


class HttpConnector(BaseConnector):
    """Execute tests against HTTP APIs."""

    def __init__(self, base_url: str = "", timeout: float = 30.0) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self._client: httpx.Client | None = None

    def connect(self) -> None:
        """Create HTTP client."""
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def execute(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Execute an HTTP request.

        *command* should be in the form ``METHOD /path``, e.g. ``GET /api/users``.
        """
        assert self._client is not None, "Not connected"

        parts = command.split(None, 1)
        method = parts[0].upper()
        path = parts[1] if len(parts) > 1 else "/"

        start = time.monotonic()
        response = self._client.request(method, path, **kwargs)
        duration = time.monotonic() - start

        return {
            "status": "passed" if response.is_success else "failed",
            "output": response.text,
            "status_code": response.status_code,
            "duration": duration,
        }

    def disconnect(self) -> None:
        """Close HTTP client."""
        if self._client:
            self._client.close()
