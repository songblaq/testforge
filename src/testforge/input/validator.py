"""Input validation -- checks parsed document quality and completeness."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from testforge.input.parser import ParsedDocument


@dataclass
class ValidationIssue:
    """A single validation issue found in a parsed document."""

    severity: str  # error, warning, info
    field: str
    message: str


@dataclass
class ValidationResult:
    """Result of validating a parsed document."""

    source_path: str
    source_type: str
    completeness_score: float  # 0.0 to 1.0
    text_length: int
    page_count: int
    heading_count: int
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "source_type": self.source_type,
            "completeness_score": self.completeness_score,
            "text_length": self.text_length,
            "page_count": self.page_count,
            "heading_count": self.heading_count,
            "is_valid": self.is_valid,
            "issues": [
                {"severity": i.severity, "field": i.field, "message": i.message}
                for i in self.issues
            ],
        }


def validate_parsed(doc: ParsedDocument) -> ValidationResult:
    """Validate a ParsedDocument for quality and completeness.

    Checks:
    - Required fields present
    - Text not empty
    - No encoding corruption (mojibake)
    - No empty pages/slides
    - Heading structure present
    """
    issues: list[ValidationIssue] = []
    score_parts: list[float] = []

    # 1. Source metadata
    if not doc.source_path:
        issues.append(ValidationIssue("error", "source_path", "Source path is empty"))
    if not doc.source_type:
        issues.append(ValidationIssue("error", "source_type", "Source type is empty"))

    # 2. Text content
    if not doc.text or not doc.text.strip():
        issues.append(ValidationIssue("error", "text", "No text content extracted"))
        score_parts.append(0.0)
    else:
        score_parts.append(1.0)

        # Check for encoding corruption (common mojibake patterns)
        mojibake_patterns = [
            r'[\ufffd]{3,}',           # replacement characters
            r'Ã[€-¿]{2,}',            # UTF-8 decoded as Latin-1
            r'[\x00-\x08\x0b\x0c\x0e-\x1f]{3,}',  # control characters
        ]
        for pattern in mojibake_patterns:
            if re.search(pattern, doc.text):
                issues.append(
                    ValidationIssue("warning", "text", f"Possible encoding corruption detected (pattern: {pattern})")
                )
                break

    # 3. Pages/slides
    if doc.pages:
        empty_pages = [
            i + 1 for i, p in enumerate(doc.pages)
            if not p.get("text", "").strip()
        ]
        if empty_pages:
            issues.append(
                ValidationIssue(
                    "warning", "pages",
                    f"Empty pages detected: {empty_pages[:5]}{'...' if len(empty_pages) > 5 else ''}"
                )
            )
        page_ratio = (len(doc.pages) - len(empty_pages)) / len(doc.pages)
        score_parts.append(page_ratio)
    else:
        # No pages is not always an error (e.g., markdown)
        if doc.source_type in ("pdf", "pptx", "docx"):
            issues.append(ValidationIssue("warning", "pages", "No page structure extracted"))
            score_parts.append(0.5)
        else:
            score_parts.append(1.0)

    # 4. Headings
    if doc.headings:
        score_parts.append(1.0)
    else:
        if doc.source_type in ("pdf", "pptx", "docx", "markdown"):
            issues.append(ValidationIssue("info", "headings", "No headings extracted"))
            score_parts.append(0.7)
        else:
            score_parts.append(1.0)

    # 5. Text length sanity
    text_len = len(doc.text) if doc.text else 0
    if text_len > 0 and text_len < 50:
        issues.append(
            ValidationIssue("warning", "text", f"Very short text ({text_len} chars) — may be incomplete")
        )
        score_parts.append(0.5)
    elif text_len >= 50:
        score_parts.append(1.0)

    completeness = sum(score_parts) / len(score_parts) if score_parts else 0.0

    return ValidationResult(
        source_path=doc.source_path,
        source_type=doc.source_type,
        completeness_score=round(completeness, 3),
        text_length=text_len,
        page_count=len(doc.pages),
        heading_count=len(doc.headings),
        issues=issues,
    )
