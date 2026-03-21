"""Dashboard screen -- project summary and quick actions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Rule, Static


class DashboardScreen(Screen):  # type: ignore[type-arg]
    """Main dashboard showing project overview and quick-action shortcuts."""

    BINDINGS = [
        ("a", "analyze", "Analyze"),
        ("g", "generate", "Generate"),
        ("r", "run", "Run"),
    ]

    DEFAULT_CSS = """
    DashboardScreen {
        layout: vertical;
        padding: 1 2;
    }
    DashboardScreen .title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    DashboardScreen .section-header {
        text-style: bold underline;
        margin-top: 1;
    }
    DashboardScreen .stat-row {
        margin-left: 2;
    }
    DashboardScreen .actions {
        margin-top: 1;
        color: $text-muted;
    }
    """

    def __init__(self, project_path: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._project_path = Path(project_path) if project_path else None
        self._summary = self._load_summary()

    def _load_summary(self) -> dict[str, Any]:
        """Load project summary data safely."""
        summary: dict[str, Any] = {
            "name": "-",
            "total": 0,
            "must": 0,
            "should": 0,
            "nice": 0,
            "last_run": None,
            "passed": 0,
            "failed": 0,
        }
        if self._project_path is None or not self._project_path.exists():
            return summary

        try:
            from testforge.core.config import load_config
            from testforge.core.project import load_cases

            config = load_config(self._project_path)
            summary["name"] = config.project_name

            cases = load_cases(self._project_path)
            summary["total"] = len(cases)
            for c in cases:
                tier = str(c.get("tier", c.get("priority", ""))).upper()
                if tier == "MUST":
                    summary["must"] += 1
                elif tier == "SHOULD":
                    summary["should"] += 1
                elif tier in ("NICE", "NICE_TO_HAVE"):
                    summary["nice"] += 1
        except Exception:
            pass

        return summary

    def compose(self) -> ComposeResult:
        s = self._summary
        yield Label(f"TestForge Dashboard -- {s['name']}", classes="title")
        yield Rule()

        yield Label("Case Summary", classes="section-header")
        yield Static(
            f"  Total: [bold]{s['total']}[/bold]    "
            f"[red]MUST: {s['must']}[/red]    "
            f"[yellow]SHOULD: {s['should']}[/yellow]    "
            f"[green]NICE: {s['nice']}[/green]",
            classes="stat-row",
        )

        yield Label("Last Run", classes="section-header")
        if s["last_run"]:
            yield Static(
                f"  [green]Passed: {s['passed']}[/green]    [red]Failed: {s['failed']}[/red]",
                classes="stat-row",
            )
        else:
            yield Static("  No runs yet.", classes="stat-row")

        yield Rule()
        yield Static(
            "[bold][A][/bold]nalyze  [bold][G][/bold]enerate  [bold][R][/bold]un  "
            "  Tab=Switch screen",
            classes="actions",
        )

    def action_analyze(self) -> None:
        self.app.notify("Run: testforge analyze <project>", title="Analyze")

    def action_generate(self) -> None:
        self.app.notify("Run: testforge generate <project>", title="Generate")

    def action_run(self) -> None:
        self.app.notify("Run: testforge run <project>", title="Run")
