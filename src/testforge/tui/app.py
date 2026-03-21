"""TestForge TUI -- main Textual application."""

from __future__ import annotations

from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TabbedContent, TabPane

from testforge.tui.screens.dashboard import DashboardScreen
from testforge.tui.screens.cases import CasesScreen
from testforge.tui.screens.runner import RunnerScreen
from testforge.tui.screens.manual import ManualQAScreen
from testforge.tui.widgets.status_bar import StatusBar


class TestForgeApp(App):  # type: ignore[type-arg]
    """TestForge interactive terminal UI."""

    TITLE = "TestForge"
    SUB_TITLE = "LLM-powered QA automation"

    CSS = """
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        padding: 0;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("tab", "focus_next", "Next tab", show=False),
        Binding("shift+tab", "focus_previous", "Prev tab", show=False),
        Binding("?", "show_help", "Help", show=False),
    ]

    def __init__(self, project_path: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._project_path = project_path

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent():
            with TabPane("Dashboard", id="tab-dashboard"):
                yield DashboardScreen(project_path=self._project_path)
            with TabPane("Cases", id="tab-cases"):
                yield CasesScreen(project_path=self._project_path)
            with TabPane("Run", id="tab-runner"):
                yield RunnerScreen(project_path=self._project_path)
            with TabPane("Manual QA", id="tab-manual"):
                yield ManualQAScreen(project_path=self._project_path)
        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        if self._project_path:
            try:
                status = self.query_one(StatusBar)
                from pathlib import Path
                status.project_name = Path(self._project_path).name
            except Exception:
                pass

    def action_show_help(self) -> None:
        self.notify(
            "q=Quit  Tab=Switch tab  Space=Select  a=Approve  x=Reject  r=Run  ?=Help",
            title="Key bindings",
            timeout=6,
        )
