"""Engine registry — discover and instantiate execution engines."""
from __future__ import annotations

import logging
from typing import Any

from testforge.execution.engines.base import BaseEngine

logger = logging.getLogger(__name__)

_ENGINES: dict[str, type[BaseEngine]] = {}


def register_engine(cls: type[BaseEngine]) -> type[BaseEngine]:
    """Register an engine class by its name."""
    _ENGINES[cls.name] = cls
    return cls


def get_engine(name: str, **config: Any) -> BaseEngine:
    """Instantiate a named engine with config."""
    if name not in _ENGINES:
        raise ValueError(f"Unknown engine: {name}. Available: {list(_ENGINES.keys())}")
    return _ENGINES[name](**config)


def available_engines() -> list[str]:
    """Return names of engines whose dependencies are installed."""
    available = []
    for name, cls in _ENGINES.items():
        try:
            if cls().is_available():
                available.append(name)
        except Exception:
            logger.debug("Engine %s availability check failed", name)
    return available


def all_engine_names() -> list[str]:
    """Return all registered engine names."""
    return list(_ENGINES.keys())


# Auto-register built-in engines
from testforge.execution.engines.playwright_engine import PlaywrightEngine  # noqa: E402
from testforge.execution.engines.expect_engine import ExpectEngine  # noqa: E402
from testforge.execution.engines.agent_browser_engine import AgentBrowserEngine  # noqa: E402

register_engine(PlaywrightEngine)
register_engine(ExpectEngine)
register_engine(AgentBrowserEngine)
