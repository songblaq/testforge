"""GitHub repository analysis -- fetch repo metadata and contents."""

from __future__ import annotations

from typing import Any


def parse_github(ref: str) -> dict[str, Any]:
    """Fetch GitHub repository information.

    *ref* should be in the form ``github:owner/repo`` or ``gh:owner/repo``.
    """
    import httpx

    repo = ref.split(":", 1)[1] if ":" in ref else ref
    api_url = f"https://api.github.com/repos/{repo}"

    response = httpx.get(api_url, timeout=30)
    response.raise_for_status()

    data = response.json()
    return {
        "type": "github",
        "source": ref,
        "repo": repo,
        "description": data.get("description", ""),
        "language": data.get("language", ""),
        "topics": data.get("topics", []),
        "default_branch": data.get("default_branch", "main"),
        "stars": data.get("stargazers_count", 0),
    }
