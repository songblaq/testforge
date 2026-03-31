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


_MAX_RESPONSE_SIZE = 5 * 1024 * 1024  # 5MB


def parse_url(url: str) -> dict[str, Any]:
    """Fetch a URL and extract text content with SSRF protection."""
    import httpx

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

    if _is_private_url(url):
        raise ValueError("URL resolves to a private or disallowed address")

    # Disable auto-redirects; validate each hop manually
    response = httpx.get(url, follow_redirects=False, timeout=30)
    hops = 0
    while response.is_redirect and hops < 5:
        hops += 1
        redirect_url = str(response.next_request.url) if response.next_request else ""
        if not redirect_url:
            break
        redirect_parsed = urlparse(redirect_url)
        if redirect_parsed.scheme not in ("http", "https"):
            raise ValueError(f"Redirect to disallowed scheme: {redirect_parsed.scheme}")
        if _is_private_url(redirect_url):
            raise ValueError("Redirect target resolves to a private or disallowed address")
        response = httpx.get(redirect_url, follow_redirects=False, timeout=30)

    response.raise_for_status()

    text = response.text[:_MAX_RESPONSE_SIZE]

    return {
        "type": "url",
        "source": url,
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type", ""),
        "text": text,
        "content_length": len(text),
    }
