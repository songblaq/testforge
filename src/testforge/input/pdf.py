"""PDF parsing using PyMuPDF (fitz)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def parse_file(path: Path) -> dict[str, Any]:
    """Extract text and metadata from a PDF file."""
    import fitz  # PyMuPDF

    doc = fitz.open(str(path))
    pages: list[dict[str, Any]] = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        pages.append({
            "page": page_num,
            "text": text,
            "images": len(page.get_images()),
        })

    metadata = doc.metadata or {}
    doc.close()

    return {
        "type": "pdf",
        "source": str(path),
        "pages": pages,
        "page_count": len(pages),
        "metadata": metadata,
    }
