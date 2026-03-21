"""Case table widget for TestForge TUI."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, Label


TIER_COLORS = {
    "MUST": "red",
    "SHOULD": "yellow",
    "NICE": "green",
    "must": "red",
    "should": "yellow",
    "nice": "green",
}

STATUS_SYMBOLS = {
    "pending": "○",
    "approved": "✓",
    "rejected": "✗",
    "running": "▶",
    "passed": "●",
    "failed": "✗",
    "skipped": "-",
}


class CaseTable(Widget):
    """DataTable wrapper that renders test cases with tier/status colouring."""

    DEFAULT_CSS = """
    CaseTable {
        height: 1fr;
    }
    CaseTable DataTable {
        height: 1fr;
    }
    """

    def __init__(self, cases: list[dict[str, Any]] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._cases: list[dict[str, Any]] = cases or []

    def compose(self) -> ComposeResult:
        if not self._cases:
            yield Label("[dim]No cases loaded. Run 'analyze' and 'generate' first.[/dim]")
            return
        table: DataTable[str] = DataTable()
        table.add_columns("ID", "Name", "Tier", "Type", "Status")
        for case in self._cases:
            cid = str(case.get("id", ""))
            name = str(case.get("name", case.get("title", "")))[:50]
            tier = str(case.get("tier", case.get("priority", "-"))).upper()
            ctype = str(case.get("type", case.get("case_type", "-")))
            status = str(case.get("status", "pending"))
            symbol = STATUS_SYMBOLS.get(status, "?")
            color = TIER_COLORS.get(tier, "white")
            table.add_row(
                cid,
                name,
                f"[{color}]{tier}[/{color}]",
                ctype,
                f"{symbol} {status}",
            )
        yield table

    def update_cases(self, cases: list[dict[str, Any]]) -> None:
        """Replace the displayed cases with a new list."""
        self._cases = cases
        self.remove_children()
        self._compose_and_mount()

    def _compose_and_mount(self) -> None:
        for widget in self.compose():
            self.mount(widget)
