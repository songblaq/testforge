"""URL crawling -- fetch and extract content from web pages."""

from __future__ import annotations

from typing import Any


def parse_url(url: str) -> dict[str, Any]:
    """Fetch a URL and extract text content."""
    import httpx

    response = httpx.get(url, follow_redirects=True, timeout=30)
    response.raise_for_status()

    return {
        "type": "url",
        "source": url,
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type", ""),
        "text": response.text,
        "content_length": len(response.text),
    }
