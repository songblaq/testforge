"""Repository input — clone and analyze repository contents."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Files to look for when analyzing a repo
_KEY_FILES = [
    "README.md", "README.rst", "README.txt", "README",
    "package.json", "pyproject.toml", "setup.py", "setup.cfg",
    "requirements.txt", "Cargo.toml", "go.mod", "pom.xml",
    "Makefile", "Dockerfile", "docker-compose.yml",
    ".env.example", "tsconfig.json", "vite.config.ts",
]

_SOURCE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte",
    ".java", ".go", ".rs", ".rb", ".php", ".cs", ".swift", ".kt",
}

_MAX_FILE_SIZE = 100_000  # 100KB per file
_MAX_SOURCE_FILES = 50


def _build_clone_url(ref: str) -> str:
    """Build a clone URL from a ref string.

    Supports:
      - Full URL: https://github.com/owner/repo
      - GHE URL: https://ghe.company.com/owner/repo
      - Short form: owner/repo (defaults to GitHub)
      - Prefixed: repo:owner/repo, github:owner/repo, gh:owner/repo
    """
    # Strip prefix
    for prefix in ("repo:", "github:", "gh:"):
        if ref.startswith(prefix):
            ref = ref[len(prefix):]
            break

    # Already a full URL
    if ref.startswith(("https://", "http://", "git@")):
        url = ref
    else:
        # Short form owner/repo — try GHE first if env set
        ghe_url = os.environ.get("TESTFORGE_GHE_URL", "").rstrip("/")
        if ghe_url:
            url = f"{ghe_url}/{ref}"
        else:
            url = f"https://github.com/{ref}"

    # Inject auth token if available
    token = os.environ.get("TESTFORGE_GHE_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
    if token and url.startswith("https://"):
        # https://TOKEN@host/path
        url = url.replace("https://", f"https://{token}@", 1)

    return url


def _scan_directory_tree(root: Path, max_depth: int = 3) -> list[str]:
    """Return a compact directory tree listing."""
    lines: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).relative_to(root).parts)
        if depth > max_depth:
            dirnames.clear()
            continue
        # Skip hidden and common noise dirs
        dirnames[:] = sorted(
            d for d in dirnames
            if not d.startswith(".") and d not in ("node_modules", "__pycache__", ".git", "vendor", "dist", "build")
        )
        indent = "  " * depth
        rel = Path(dirpath).relative_to(root)
        if depth > 0:
            lines.append(f"{indent}{rel.name}/")
        for f in sorted(filenames)[:20]:
            lines.append(f"{indent}  {f}")
        if len(filenames) > 20:
            lines.append(f"{indent}  ... and {len(filenames) - 20} more files")
    return lines


def _read_file_safe(path: Path) -> str:
    """Read a file, returning empty string on any error."""
    try:
        if path.stat().st_size > _MAX_FILE_SIZE:
            return f"[File too large: {path.stat().st_size} bytes]\n"
        return path.read_text(errors="replace")
    except Exception:
        return ""


_DEFAULT_ALLOWED_HOSTS = {"github.com", "gitlab.com", "bitbucket.org"}


def _validate_clone_host(url: str) -> None:
    """Reject clone URLs targeting disallowed hosts."""
    from urllib.parse import urlparse

    allowed_str = os.environ.get("TESTFORGE_ALLOWED_GIT_HOSTS", "")
    allowed = set(allowed_str.split(",")) if allowed_str else set()
    ghe = os.environ.get("TESTFORGE_GHE_URL", "")
    if ghe:
        from urllib.parse import urlparse as _up
        ghe_host = _up(ghe).hostname
        if ghe_host:
            allowed.add(ghe_host)
    allowed |= _DEFAULT_ALLOWED_HOSTS

    if url.startswith("git@"):
        host = url.split("@", 1)[1].split(":", 1)[0]
    else:
        host = urlparse(url).hostname or ""

    if host not in allowed:
        raise ValueError(f"Git host not allowed: {host}. Allowed: {', '.join(sorted(allowed))}")


def parse_repository(ref: str, clone_dir: Path | None = None) -> dict[str, Any]:
    """Clone a repository and analyze its contents.

    Args:
        ref: Repository URL or owner/repo format.
        clone_dir: Target directory for clone. Uses temp dir if None.

    Returns:
        dict with type, source, text (combined analysis), tree, key_files, source_summary.
    """
    url = _build_clone_url(ref)
    _validate_clone_host(url)
    use_temp = clone_dir is None
    if use_temp:
        clone_dir = Path(tempfile.mkdtemp(prefix="testforge_repo_"))

    try:
        # Shallow clone
        token = os.environ.get("TESTFORGE_GHE_TOKEN") or os.environ.get("GITHUB_TOKEN", "")

        result = subprocess.run(
            ["git", "clone", "--depth=1", "--single-branch", url, str(clone_dir)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if token:
                stderr = stderr.replace(token, "***")
            raise RuntimeError(f"git clone failed: {stderr}")

        parts: list[str] = []

        # 1. README
        readme_text = ""
        for name in ("README.md", "README.rst", "README.txt", "README"):
            rp = clone_dir / name
            if rp.exists():
                readme_text = _read_file_safe(rp)
                parts.append(f"# README ({name})\n\n{readme_text}")
                break

        # 2. Key config files
        key_files: dict[str, str] = {}
        for kf in _KEY_FILES:
            fp = clone_dir / kf
            if fp.exists():
                content = _read_file_safe(fp)
                if content:
                    key_files[kf] = content
                    parts.append(f"# {kf}\n\n```\n{content}\n```")

        # 3. Directory tree
        tree_lines = _scan_directory_tree(clone_dir)
        tree_text = "\n".join(tree_lines)
        parts.append(f"# Directory Structure\n\n```\n{tree_text}\n```")

        # 4. Source file summary (first N source files, just names and first few lines)
        source_files: list[str] = []
        for dirpath, _, filenames in os.walk(clone_dir):
            dp = Path(dirpath)
            if any(skip in dp.parts for skip in (".git", "node_modules", "__pycache__", "vendor", "dist")):
                continue
            for f in filenames:
                fp = dp / f
                if fp.suffix in _SOURCE_EXTENSIONS:
                    source_files.append(str(fp.relative_to(clone_dir)))
                    if len(source_files) >= _MAX_SOURCE_FILES:
                        break
            if len(source_files) >= _MAX_SOURCE_FILES:
                break

        if source_files:
            parts.append(f"# Source Files ({len(source_files)} files)\n\n" + "\n".join(f"- {sf}" for sf in source_files))

        text = "\n\n---\n\n".join(parts)

        token = os.environ.get("TESTFORGE_GHE_TOKEN", "")
        safe_clone_url = url.replace(token, "***") if token else url

        return {
            "type": "repository",
            "source": ref,
            "clone_url": safe_clone_url,
            "text": text,
            "readme": readme_text,
            "tree": tree_text,
            "key_files": list(key_files.keys()),
            "source_file_count": len(source_files),
        }
    finally:
        if use_temp and clone_dir.exists():
            shutil.rmtree(clone_dir, ignore_errors=True)
