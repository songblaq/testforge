"""Image analysis -- extract information from screenshots and designs."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any


def parse_file(path: Path) -> dict[str, Any]:
    """Read an image file and prepare it for LLM analysis."""
    data = path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")

    suffix = path.suffix.lower().lstrip(".")
    media_type = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
    }.get(suffix, "application/octet-stream")

    return {
        "type": "image",
        "source": str(path),
        "media_type": media_type,
        "base64": encoded,
        "size_bytes": len(data),
    }
