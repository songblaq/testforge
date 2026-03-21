"""File parsing dispatcher -- routes input files to the appropriate parser."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ParsedDocument:
    """Structured representation of a parsed input document."""

    # source metadata
    source_type: str  # pdf, pptx, docx, xlsx, image, url, markdown
    source_path: str
    source_format: str  # file extension or mime hint

    # content
    text: str = ""
    pages: list[dict[str, Any]] = field(default_factory=list)

    # structure
    headings: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)

    # raw dict from the underlying parser (preserved for downstream consumers)
    raw: dict[str, Any] = field(default_factory=dict)


def parse(path: str) -> ParsedDocument:
    """Parse an input file or URL and return structured content.

    Dispatches to the appropriate parser based on file extension or URL scheme.
    """
    if path.startswith(("http://", "https://")):
        from testforge.input.url import parse_url

        raw = parse_url(path)
        return ParsedDocument(
            source_type="url",
            source_path=path,
            source_format="html",
            text=raw.get("text", ""),
            raw=raw,
        )

    if path.startswith("github:") or path.startswith("gh:"):
        from testforge.input.github import parse_github

        raw = parse_github(path)
        return ParsedDocument(
            source_type="github",
            source_path=path,
            source_format="github",
            text=raw.get("text", ""),
            raw=raw,
        )

    p = Path(path)
    suffix = p.suffix.lower()

    # Markdown: load directly without a sub-module
    if suffix in (".md", ".markdown"):
        text = p.read_text(encoding="utf-8")
        headings = [
            line.lstrip("#").strip()
            for line in text.splitlines()
            if line.startswith("#")
        ]
        return ParsedDocument(
            source_type="markdown",
            source_path=str(p),
            source_format=suffix.lstrip("."),
            text=text,
            headings=headings,
            raw={"type": "markdown", "source": str(p), "text": text},
        )

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
    raw: dict[str, Any] = module.parse_file(p)  # type: ignore[attr-defined]
    return _wrap_raw(raw, str(p), suffix)


def _wrap_raw(raw: dict[str, Any], source_path: str, suffix: str) -> ParsedDocument:
    """Convert a raw parser dict into a ParsedDocument."""
    doc_type = raw.get("type", suffix.lstrip("."))
    suffix_fmt = suffix.lstrip(".")

    # Collect full text from pages/slides/paragraphs
    text_parts: list[str] = []
    pages: list[dict[str, Any]] = []

    if doc_type == "pdf":
        pages = raw.get("pages", [])
        text_parts = [p.get("text", "") for p in pages]
    elif doc_type == "pptx":
        for slide in raw.get("slides", []):
            texts = slide.get("texts", [])
            combined = "\n".join(texts)
            pages.append({"page": slide.get("slide"), "text": combined})
            text_parts.append(combined)
    elif doc_type == "docx":
        paras = raw.get("paragraphs", [])
        text_parts = paras
        pages = [{"page": 1, "text": "\n".join(paras)}]
    elif doc_type == "xlsx":
        for sheet in raw.get("sheets", []):
            rows_text = "\n".join(
                "\t".join("" if v is None else str(v) for v in row)
                for row in sheet.get("rows", [])
            )
            pages.append({"page": sheet.get("name"), "text": rows_text})
            text_parts.append(rows_text)
    elif doc_type == "image":
        # No extractable text — downstream LLM handles it
        text_parts = []
        pages = []

    full_text = "\n".join(t for t in text_parts if t)

    return ParsedDocument(
        source_type=doc_type,
        source_path=source_path,
        source_format=suffix_fmt,
        text=full_text,
        pages=pages,
        raw=raw,
    )
