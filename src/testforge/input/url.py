"""URL crawling -- fetch and extract content from web pages."""

from __future__ import annotations

import ipaddress
import socket
from typing import Any
from urllib.parse import urlparse


def _is_private_url(url: str) -> bool:
    """Check if URL resolves to a private/internal IP."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return True
        ip = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
        addr = ipaddress.ip_address(ip)
        return (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
        )
    except Exception:
        return True  # fail closed


def parse_url(url: str) -> dict[str, Any]:
    """Fetch a URL and extract text content."""
    import httpx

    if _is_private_url(url):
        raise ValueError("URL resolves to a private or disallowed address")

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
