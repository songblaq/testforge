"""Manual QA screen -- interactive checklist for manual test review."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Checkbox, Label, Rule, ScrollableContainer, Static

from testforge.core.locale_strings import s


class ManualQAScreen(Screen):  # type: ignore[type-arg]
    """Manual QA checklist -- check off items as they are verified."""

    BINDINGS = [
        ("space", "toggle_item", "Toggle"),
        ("c", "clear_all", "Clear all"),
    ]

    DEFAULT_CSS = """
    ManualQAScreen {
        layout: vertical;
        padding: 0 1;
    }
    ManualQAScreen .qa-title {
        text-style: bold;
        color: $accent;
        margin: 1 0;
    }
    ManualQAScreen #checklist-container {
        height: 1fr;
        border: solid $panel;
        padding: 0 1;
    }
    ManualQAScreen #progress {
        margin-top: 1;
        color: $text-muted;
    }
    """

    def __init__(self, project_path: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._project_path = Path(project_path) if project_path else None
        self._locale = self._resolve_locale()
        self._items = self._load_checklist_cases()

    def _resolve_locale(self) -> str:
        try:
            from testforge.core.config import effective_locale, load_config

            if self._project_path and self._project_path.exists():
                return effective_locale(load_config(self._project_path))
        except Exception:
            pass
        return "ko"

    def _load_checklist_cases(self) -> list[dict[str, Any]]:
        if self._project_path is None or not self._project_path.exists():
            return self._default_checklist(self._locale)
        try:
            from testforge.core.project import load_cases

            all_cases = load_cases(self._project_path)
            checklist = [c for c in all_cases if c.get("type") in ("checklist", "manual")]
            return checklist if checklist else self._default_checklist(self._locale)
        except Exception:
            return self._default_checklist(self._locale)

    @staticmethod
    def _default_checklist(locale: str = "ko") -> list[dict[str, Any]]:
        return [
            {"id": "c1", "name": s("tui_init", locale)},
            {"id": "c2", "name": s("tui_analysis", locale)},
            {"id": "c3", "name": s("tui_cases_gen", locale)},
            {"id": "c4", "name": s("tui_run", locale)},
            {"id": "c5", "name": s("tui_report", locale)},
        ]

    def compose(self) -> ComposeResult:
        yield Label("Manual QA Checklist", classes="qa-title")
        yield Rule()
        with ScrollableContainer(id="checklist-container"):
            if not self._items:
                yield Static("[dim]No checklist items found.[/dim]")
            else:
                for item in self._items:
                    label = str(item.get("name", item.get("title", item.get("id", ""))))
                    yield Checkbox(label, id=f"chk-{item['id']}")
        yield Static(self._progress_label(), id="progress")

    def _progress_label(self) -> str:
        if not self._items:
            return ""
        checked = sum(
            1
            for item in self._items
            if self._is_checked(item["id"])
        )
        return f"Progress: {checked}/{len(self._items)} checked"

    def _is_checked(self, item_id: str) -> bool:
        try:
            chk = self.query_one(f"#chk-{item_id}", Checkbox)
            return chk.value
        except Exception:
            return False

    def on_checkbox_changed(self, _event: Checkbox.Changed) -> None:
        try:
            self.query_one("#progress", Static).update(self._progress_label())
        except Exception:
            pass

    def action_toggle_item(self) -> None:
        # Focus-based toggle is handled natively by Textual's Checkbox
        self.app.notify("Use Space/Enter on a focused checkbox to toggle.", title="Manual QA")

    def action_clear_all(self) -> None:
        for item in self._items:
            try:
                chk = self.query_one(f"#chk-{item['id']}", Checkbox)
                chk.value = False
            except Exception:
                pass
        try:
            self.query_one("#progress", Static).update(self._progress_label())
        except Exception:
            pass
