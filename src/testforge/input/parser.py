"""File parsing dispatcher -- routes input files to the appropriate parser."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def parse(path: str) -> dict[str, Any]:
    """Parse an input file or URL and return structured content.

    Dispatches to the appropriate parser based on file extension or URL scheme.
    """
    if path.startswith(("http://", "https://")):
        from testforge.input.url import parse_url

        return parse_url(path)

    if path.startswith("github:") or path.startswith("gh:"):
        from testforge.input.github import parse_github

        return parse_github(path)

    p = Path(path)
    suffix = p.suffix.lower()

    parsers: dict[str, str] = {
        ".pdf": "testforge.input.pdf",
        ".pptx": "testforge.input.office",
        ".ppt": "testforge.input.office",
        ".docx": "testforge.input.office",
        ".doc": "testforge.input.office",
        ".xlsx": "testforge.input.office",
        ".xls": "testforge.input.office",
        ".png": "testforge.input.image",
        ".jpg": "testforge.input.image",
        ".jpeg": "testforge.input.image",
        ".gif": "testforge.input.image",
        ".webp": "testforge.input.image",
    }

    if suffix not in parsers:
        raise ValueError(f"Unsupported file format: {suffix}")

    # Dynamic import to avoid loading unused dependencies
    import importlib

    module = importlib.import_module(parsers[suffix])
    return module.parse_file(p)  # type: ignore[attr-defined]
