"""Runner screen -- execute tests and monitor live progress."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Log, Rule, Static


class RunnerScreen(Screen):  # type: ignore[type-arg]
    """Test execution monitor showing live log output."""

    BINDINGS = [
        ("r", "start_run", "Start run"),
        ("s", "stop_run", "Stop"),
    ]

    DEFAULT_CSS = """
    RunnerScreen {
        layout: vertical;
        padding: 0 1;
    }
    RunnerScreen .run-title {
        text-style: bold;
        color: $accent;
        margin: 1 0;
    }
    RunnerScreen #run-status {
        height: 3;
        padding: 0 1;
        background: $surface;
    }
    RunnerScreen Log {
        height: 1fr;
        border: solid $panel;
    }
    RunnerScreen .hint {
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(self, project_path: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._project_path = Path(project_path) if project_path else None
        self._running = False

    def compose(self) -> ComposeResult:
        yield Label("Test Runner", classes="run-title")
        yield Rule()
        yield Static("Status: [dim]idle[/dim]", id="run-status")
        yield Log(id="run-log", auto_scroll=True)
        yield Static("[bold][R][/bold] Start  [bold][S][/bold] Stop", classes="hint")

    def action_start_run(self) -> None:
        if self._running:
            self.app.notify("Already running.", title="Runner")
            return
        if self._project_path is None:
            self.app.notify("No project loaded.", title="Runner")
            return
        self._running = True
        self._update_status("running")
        log = self.query_one("#run-log", Log)
        log.clear()
        log.write_line("Starting test run...")
        self.run_worker(self._do_run(), exclusive=True)

    async def _do_run(self) -> None:
        """Execute tests in a worker thread to keep UI responsive."""
        log = self.query_one("#run-log", Log)
        try:
            from testforge.execution.runner import run_tests

            import asyncio

            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: run_tests(self._project_path, [], 1),  # type: ignore[arg-type]
            )
            passed = sum(1 for r in results if r.get("status") == "passed")
            failed = len(results) - passed
            log.write_line(f"Done. Passed: {passed}  Failed: {failed}")
            self._update_status(f"done — {passed}P / {failed}F")
        except Exception as exc:
            log.write_line(f"[red]Error: {exc}[/red]")
            self._update_status("error")
        finally:
            self._running = False

    def action_stop_run(self) -> None:
        if self._running:
            self._running = False
            self._update_status("stopped")
            try:
                self.query_one("#run-log", Log).write_line("Run stopped by user.")
            except Exception:
                pass

    def _update_status(self, text: str) -> None:
        try:
            self.query_one("#run-status", Static).update(f"Status: {text}")
        except Exception:
            pass
