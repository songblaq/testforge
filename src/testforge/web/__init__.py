"""TestForge Web GUI -- FastAPI backend with static SPA frontend."""

from __future__ import annotations


def create_app():
    """Create and configure the FastAPI application."""
    from testforge.web.app import create_app as _create

    return _create()
