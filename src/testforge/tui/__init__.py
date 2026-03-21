"""TestForge TUI -- Textual-based interactive interface."""

from __future__ import annotations

__all__ = ["run_tui"]


def run_tui(project_path: str | None = None) -> None:
    """Launch the TestForge TUI application.

    Raises ImportError with a helpful message if textual is not installed.
    """
    try:
        from testforge.tui.app import TestForgeApp  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "The TUI requires 'textual'. Install it with:\n"
            "  pip install 'testforge[tui]'\n"
            "or:  pip install textual>=0.80"
        ) from exc

    app = TestForgeApp(project_path=project_path)
    app.run()
