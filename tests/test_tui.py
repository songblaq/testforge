"""Tests for TestForge TUI -- requires textual to be installed."""

from __future__ import annotations

import importlib
import sys

import pytest


# ---------------------------------------------------------------------------
# Guard: skip entire module if textual is not installed
# ---------------------------------------------------------------------------

textual_available = importlib.util.find_spec("textual") is not None
skip_no_textual = pytest.mark.skipif(
    not textual_available,
    reason="textual not installed; install with: pip install 'testforge[tui]'",
)


# ---------------------------------------------------------------------------
# Import tests
# ---------------------------------------------------------------------------


@skip_no_textual
def test_tui_package_importable() -> None:
    """testforge.tui package is importable when textual is installed."""
    import testforge.tui  # noqa: F401


@skip_no_textual
def test_tui_app_importable() -> None:
    """TestForgeApp class is importable."""
    from testforge.tui.app import TestForgeApp

    assert TestForgeApp is not None


@skip_no_textual
def test_tui_screens_importable() -> None:
    """All four screens are importable."""
    from testforge.tui.screens.dashboard import DashboardScreen
    from testforge.tui.screens.cases import CasesScreen
    from testforge.tui.screens.runner import RunnerScreen
    from testforge.tui.screens.manual import ManualQAScreen

    assert DashboardScreen is not None
    assert CasesScreen is not None
    assert RunnerScreen is not None
    assert ManualQAScreen is not None


@skip_no_textual
def test_tui_widgets_importable() -> None:
    """StatusBar and CaseTable widgets are importable."""
    from testforge.tui.widgets.status_bar import StatusBar
    from testforge.tui.widgets.case_table import CaseTable

    assert StatusBar is not None
    assert CaseTable is not None


# ---------------------------------------------------------------------------
# run_tui import path (always runs -- tests the lazy-import guard)
# ---------------------------------------------------------------------------


def test_run_tui_raises_importerror_without_textual(monkeypatch: pytest.MonkeyPatch) -> None:
    """run_tui() raises ImportError with instructions when textual is absent."""
    # Temporarily hide textual from sys.modules
    original = sys.modules.copy()
    # Remove textual so the import inside run_tui fails
    for key in list(sys.modules):
        if key == "textual" or key.startswith("textual."):
            sys.modules[key] = None  # type: ignore[assignment]

    # Also ensure testforge.tui.app is re-imported fresh
    for key in list(sys.modules):
        if "testforge.tui" in key:
            del sys.modules[key]

    try:
        from testforge.tui import run_tui

        with pytest.raises(ImportError, match="textual"):
            run_tui()
    finally:
        # Restore sys.modules
        sys.modules.clear()
        sys.modules.update(original)
