"""Evidence collection -- screenshots, logs, network traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Evidence:
    """A piece of test evidence."""

    type: str  # screenshot, log, network, video
    path: Path
    test_id: str
    step: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


class EvidenceCollector:
    """Collects and organizes test evidence."""

    def __init__(self, evidence_dir: Path) -> None:
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self._items: list[Evidence] = []

    def add_screenshot(self, test_id: str, data: bytes, step: str = "") -> Evidence:
        """Save a screenshot as evidence."""
        filename = f"{test_id}_{step or 'screenshot'}.png"
        path = self.evidence_dir / filename
        path.write_bytes(data)
        item = Evidence(type="screenshot", path=path, test_id=test_id, step=step)
        self._items.append(item)
        return item

    def add_log(self, test_id: str, content: str, step: str = "") -> Evidence:
        """Save log output as evidence."""
        filename = f"{test_id}_{step or 'log'}.txt"
        path = self.evidence_dir / filename
        path.write_text(content)
        item = Evidence(type="log", path=path, test_id=test_id, step=step)
        self._items.append(item)
        return item

    @property
    def items(self) -> list[Evidence]:
        """Return all collected evidence."""
        return list(self._items)
