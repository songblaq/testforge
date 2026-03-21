"""Cases screen -- browse, filter, and approve/reject test cases."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Label, Rule


class CasesScreen(Screen):  # type: ignore[type-arg]
    """Interactive test case browser with approve/reject actions."""

    BINDINGS = [
        ("a", "approve", "Approve"),
        ("x", "reject", "Reject"),
        ("f", "focus_filter", "Filter"),
        ("escape", "clear_filter", "Clear filter"),
    ]

    DEFAULT_CSS = """
    CasesScreen {
        layout: vertical;
    }
    CasesScreen #filter-bar {
        height: 3;
        padding: 0 1;
        background: $surface;
    }
    CasesScreen #filter-input {
        width: 1fr;
    }
    CasesScreen #case-count {
        padding: 0 2;
        color: $text-muted;
    }
    CasesScreen DataTable {
        height: 1fr;
    }
    """

    def __init__(self, project_path: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._project_path = Path(project_path) if project_path else None
        self._all_cases: list[dict[str, Any]] = self._load_cases()
        self._filter: str = ""

    def _load_cases(self) -> list[dict[str, Any]]:
        if self._project_path is None or not self._project_path.exists():
            return []
        try:
            from testforge.core.project import load_cases
            return load_cases(self._project_path)
        except Exception:
            return []

    def _filtered_cases(self) -> list[dict[str, Any]]:
        if not self._filter:
            return self._all_cases
        q = self._filter.lower()
        return [
            c for c in self._all_cases
            if q in str(c.get("name", c.get("title", ""))).lower()
            or q in str(c.get("tier", c.get("priority", ""))).lower()
            or q in str(c.get("type", c.get("case_type", ""))).lower()
        ]

    def compose(self) -> ComposeResult:
        yield Label("Test Cases", id="screen-title")
        yield Rule()
        yield Input(placeholder="Filter by name / tier / type...", id="filter-input")
        yield Label(self._count_label(), id="case-count")
        yield self._build_table()

    def _count_label(self) -> str:
        cases = self._filtered_cases()
        return f"{len(cases)} case(s)"

    def _build_table(self) -> DataTable:  # type: ignore[type-arg]
        table: DataTable[str] = DataTable(id="cases-table")
        table.add_columns("ID", "Name", "Tier", "Type", "Status")
        for case in self._filtered_cases():
            self._add_row(table, case)
        return table

    def _add_row(self, table: DataTable, case: dict[str, Any]) -> None:  # type: ignore[type-arg]
        cid = str(case.get("id", ""))
        name = str(case.get("name", case.get("title", "")))[:55]
        tier = str(case.get("tier", case.get("priority", "-"))).upper()
        ctype = str(case.get("type", case.get("case_type", "-")))
        status = str(case.get("status", "pending"))

        tier_markup = {
            "MUST": f"[red]{tier}[/red]",
            "SHOULD": f"[yellow]{tier}[/yellow]",
            "NICE": f"[green]{tier}[/green]",
        }.get(tier, tier)

        status_markup = {
            "approved": "[green]✓ approved[/green]",
            "rejected": "[red]✗ rejected[/red]",
            "pending": "[dim]○ pending[/dim]",
        }.get(status, status)

        table.add_row(cid, name, tier_markup, ctype, status_markup)

    def on_input_changed(self, event: Input.Changed) -> None:
        self._filter = event.value
        self._refresh_table()
        try:
            self.query_one("#case-count", Label).update(self._count_label())
        except Exception:
            pass

    def _refresh_table(self) -> None:
        try:
            table = self.query_one("#cases-table", DataTable)
            table.clear()
            for case in self._filtered_cases():
                self._add_row(table, case)
        except Exception:
            pass

    def action_approve(self) -> None:
        self._set_selected_status("approved")

    def action_reject(self) -> None:
        self._set_selected_status("rejected")

    def _set_selected_status(self, status: str) -> None:
        try:
            table = self.query_one("#cases-table", DataTable)
            row_key = table.cursor_row
            if row_key < len(self._all_cases):
                self._all_cases[row_key]["status"] = status
                self._refresh_table()
                self.app.notify(f"Case {status}.", title="Status updated")
        except Exception:
            pass

    def action_focus_filter(self) -> None:
        try:
            self.query_one("#filter-input", Input).focus()
        except Exception:
            pass

    def action_clear_filter(self) -> None:
        try:
            inp = self.query_one("#filter-input", Input)
            inp.value = ""
            inp.blur()
        except Exception:
            pass
