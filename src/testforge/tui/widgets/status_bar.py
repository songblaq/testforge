"""Status bar widget for TestForge TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class StatusBar(Widget):
    """A bottom status bar showing project info and key hints."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: $accent;
        color: $text;
        dock: bottom;
        layout: horizontal;
    }
    StatusBar Label {
        padding: 0 1;
    }
    StatusBar .spacer {
        width: 1fr;
    }
    StatusBar .hints {
        color: $text-muted;
    }
    """

    project_name: reactive[str] = reactive("")
    status_text: reactive[str] = reactive("Ready")

    def compose(self) -> ComposeResult:
        yield Label(self._project_label(), id="project-label")
        yield Label("", classes="spacer")
        yield Label(self._hints(), classes="hints")

    def _project_label(self) -> str:
        if self.project_name:
            return f" TestForge | {self.project_name}"
        return " TestForge"

    def _hints(self) -> str:
        return "q Quit  Tab Switch  Space Select  ? Help "

    def watch_project_name(self, value: str) -> None:
        try:
            lbl = self.query_one("#project-label", Label)
            lbl.update(f" TestForge | {value}" if value else " TestForge")
        except Exception:
            pass

    def set_status(self, text: str) -> None:
        self.status_text = text
