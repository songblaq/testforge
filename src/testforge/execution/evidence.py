"""Evidence collection -- screenshots, logs, network traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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

    def capture_screenshot(self, name: str, page: Any) -> Evidence:
        """Capture a Playwright screenshot as evidence.

        Parameters
        ----------
        name:
            Logical name / test_id for this screenshot.
        page:
            Playwright ``Page`` object.

        Returns
        -------
        Evidence:
            Saved screenshot evidence item.
        """
        path = self.evidence_dir / f"{name}.png"
        page.screenshot(path=str(path))
        item = Evidence(type="screenshot", path=path, test_id=name, step="screenshot")
        self._items.append(item)
        return item

    def capture_console_log(self, name: str, logs: list[Any]) -> Evidence:
        """Save console log entries as JSON evidence.

        Parameters
        ----------
        name:
            Logical name / test_id for this log.
        logs:
            List of console log entries (strings or dicts).

        Returns
        -------
        Evidence:
            Saved log evidence item.
        """
        import json

        path = self.evidence_dir / f"{name}_console.json"
        path.write_text(json.dumps(logs, default=str, indent=2))
        item = Evidence(type="log", path=path, test_id=name, step="console")
        self._items.append(item)
        return item

    def capture_network(self, name: str, har_path: str) -> Evidence:
        """Reference a HAR file as network evidence.

        Parameters
        ----------
        name:
            Logical name / test_id.
        har_path:
            Path to an existing HAR file to reference.

        Returns
        -------
        Evidence:
            Network evidence item pointing to the HAR file.
        """
        import shutil

        src = Path(har_path)
        dest = self.evidence_dir / f"{name}_network.har"
        if src.exists() and src != dest:
            shutil.copy2(src, dest)
        else:
            dest = src
        item = Evidence(type="network", path=dest, test_id=name, step="network")
        self._items.append(item)
        return item

    @property
    def items(self) -> list[Evidence]:
        """Return all collected evidence."""
        return list(self._items)
