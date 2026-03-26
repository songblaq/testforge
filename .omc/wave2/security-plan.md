# Security Fix Plan v0.6

Synthesis of Wave 1 diagnostics: `path-traversal.json`, `xss-vectors.json`, `ssrf-lfi.json`, `auth-audit.json`. Classifications apply to TestForge as shipped today (local dev tool, default `127.0.0.1`).

---

## FIX NOW

### 1. Path Traversal — `manual.py` `session_id`

**File**: `src/testforge/web/routers/manual.py`  
**Lines**: `121–129` (`get_session`)

**Issue**: `session_id` is interpolated into `p / ".testforge" / "manual" / f"{session_id}.json"` with no checks; `..`, `/`, or `\` can escape the manual directory after normalization.

**Fix**: Allow only a safe session id charset, then verify the resolved file stays under `.testforge/manual/`.

```python
import re
from pathlib import Path

from fastapi import HTTPException

_SAFE_SESSION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@router.get("/{project_path:path}/manual/sessions/{session_id}")
async def get_session(project_path: str, session_id: str):
    """Get a specific completed session."""
    p = resolve_project(project_path)
    if not _SAFE_SESSION_ID.match(session_id) or ".." in session_id:
        raise HTTPException(status_code=400, detail="Invalid session_id")
    manual_root = (p / ".testforge" / "manual").resolve()
    session_path = (manual_root / f"{session_id}.json").resolve()
    if not session_path.is_relative_to(manual_root):
        raise HTTPException(status_code=400, detail="Invalid session_id")
    if not session_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    data = json.loads(session_path.read_text())
    return {"session": data}
```

---

### 2. Path Traversal — `projects.py` `directory` query (`list_projects`)

**File**: `src/testforge/web/routers/projects.py`  
**Lines**: `82–100` (`list_projects`)

**Issue**: `base = Path(directory)` allows arbitrary filesystem roots (including traversal via `..` in parts) for discovery/listing.

**Fix**: Reject traversal components, resolve, and require the path to exist as a directory.

```python
@router.get("")
async def list_projects(directory: str = Query(".", description="Base directory to scan")):
    """List TestForge projects in a directory."""
    from testforge.core.project import list_projects as _list

    base = Path(directory)
    if ".." in base.parts:
        raise HTTPException(status_code=403, detail="Access denied: path traversal not allowed")
    base = base.resolve()
    if not base.exists():
        raise HTTPException(status_code=404, detail=f"Directory not found: {directory}")
    if not base.is_dir():
        raise HTTPException(status_code=400, detail="Not a directory")

    names = _list(base)
    # ... unchanged ...
```

---

### 3. Path Traversal — `projects.py` `create_project` (`body.directory`, `body.name`)

**File**: `src/testforge/web/routers/projects.py`  
**Lines**: `59–79` (`create_project`)

**Issue**: `Path(body.directory) / body.name` allows `..` segments and multi-segment `name`, creating or targeting paths outside the intended parent.

**Fix**: Reject `..` in both parts; use a single path segment for `name` (basename-only); resolve parent and assert the final project directory is under the resolved parent.

```python
@router.post("")
async def create_project(body: ProjectCreate):
    """Create a new TestForge project."""
    from testforge.core.config import TestForgeConfig, save_config
    from testforge.core.project import create_project as _create

    dir_path = Path(body.directory)
    if ".." in dir_path.parts:
        raise HTTPException(status_code=403, detail="Access denied: invalid directory")
    name = body.name.strip()
    if not name or Path(name).name != name or "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="Invalid project name")
    if ".." in Path(name).parts:
        raise HTTPException(status_code=403, detail="Access denied: invalid name")

    parent = dir_path.resolve()
    project_dir = (parent / name).resolve()
    try:
        project_dir.relative_to(parent)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project path")

    if project_dir.exists():
        raise HTTPException(status_code=409, detail=f"Directory already exists: {project_dir}")

    _create(project_dir)
    # ... rest unchanged, use project_dir instead of Path(body.directory) / body.name ...
```

(Apply the same `project_dir` variable in the `TestForgeConfig` / `save_config` block where `project_dir` is referenced.)

---

### 4. LFI + SSRF entry — `analysis.py` `body.inputs`

**File**: `src/testforge/web/routers/analysis.py`  
**Lines**: `18–40` (`run_analysis`)

**Issue**: Non-empty `body.inputs` is passed straight to `run_analysis` → `parse()`. Local strings become arbitrary `Path(path)` reads; URLs trigger server-side fetch without API-level policy.

**Fix**: After `resolve_project`, normalize every explicit input: **http(s)** only via a shared URL safety check (see item 5); **local** inputs as **basename-only** joined with `resolve_project`’s `input_dir`, then `resolve()` + `is_relative_to(input_dir)`.

```python
@router.post("/{project_path:path}/analysis")
async def run_analysis(project_path: str, body: AnalysisRequest):
    """Run analysis on a project."""
    from testforge.analysis.analyzer import run_analysis as _analyze
    from testforge.core.config import load_config
    from testforge.web.deps import resolve_project
    from testforge.input.url import assert_safe_http_url  # new helper in url.py

    p = resolve_project(project_path)

    inputs = body.inputs
    if not inputs:
        config = load_config(p)
        input_dir = p / config.input_dir
        if input_dir.exists():
            inputs = [
                str(f) for f in input_dir.iterdir()
                if f.is_file() and not f.name.startswith(".")
            ]
    else:
        config = load_config(p)
        input_dir = (p / config.input_dir).resolve()
        input_dir.mkdir(parents=True, exist_ok=True)
        coerced: list[str] = []
        for raw in inputs:
            s = raw.strip()
            if s.startswith(("http://", "https://")):
                assert_safe_http_url(s)
                coerced.append(s)
            elif "://" in s:
                raise HTTPException(
                    status_code=400,
                    detail="Only http(s) URLs or files in the project input folder are allowed",
                )
            else:
                base = Path(s).name
                if not base or base != Path(s).name:
                    raise HTTPException(status_code=400, detail="Invalid input file reference")
                cand = (input_dir / base).resolve()
                if not cand.is_relative_to(input_dir):
                    raise HTTPException(status_code=403, detail="Input path outside input_dir")
                if not cand.is_file():
                    raise HTTPException(status_code=404, detail=f"Input not found: {base}")
                coerced.append(str(cand))
        inputs = coerced

    if not inputs:
        raise HTTPException(status_code=400, detail="No input files found or specified")

    results = _analyze(p, inputs, no_llm=body.no_llm)
    return {"results": results, "source_count": len(results)}
```

---

### 5. SSRF — `url.py` private / link-local blocking

**File**: `src/testforge/input/url.py`  
**Lines**: `8–22` (`parse_url`)

**Issue**: `httpx.get(url, follow_redirects=True)` can reach RFC1918, loopback, link-local, and cloud metadata; redirects can bypass hostname-only checks.

**Fix**: Add `assert_safe_http_url(url: str) -> None` (raise `ValueError` with a clear message). Call it from `parse_url` and from the analysis router (item 4). For v0.6: resolve the request **host** to IP(s) via `socket.getaddrinfo`, reject if **any** resolved address is private, loopback, link-local, multicast, reserved, or matches documented metadata endpoints; reject non-`http`/`https` schemes and missing hostnames. **Set `follow_redirects=False`** in v0.6 (or manually follow with per-hop host re-validation — defer full hop validation to v0.7).

```python
"""URL crawling -- fetch and extract content from web pages."""

from __future__ import annotations

import ipaddress
import socket
from typing import Any
from urllib.parse import urlparse


def assert_safe_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http and https URLs are allowed")
    host = parsed.hostname
    if not host:
        raise ValueError("URL has no host")
    host_l = host.lower()
    if host_l in ("metadata.google.internal",):
        raise ValueError("Host not allowed")
    try:
        ip = ipaddress.ip_address(host)
        _reject_ip(ip)
    except ValueError:
        for res in socket.getaddrinfo(host, None):
            addr = res[4][0]
            _reject_ip(ipaddress.ip_address(addr))


def _reject_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        raise ValueError("URL resolves to a disallowed address")
    if ip.version == 4:
        if ip == ipaddress.IPv4Address("169.254.169.254"):
            raise ValueError("URL resolves to a disallowed address")


def parse_url(url: str) -> dict[str, Any]:
    """Fetch a URL and extract text content."""
    import httpx

    assert_safe_http_url(url)
    response = httpx.get(url, follow_redirects=False, timeout=30)
    response.raise_for_status()
    # ... return dict unchanged ...
```

(Map `ValueError` from `assert_safe_http_url` to HTTP 400 in FastAPI routes if needed.)

---

### 6. XSS — `safeHref` protocol-relative URLs

**File**: `src/testforge/web/static/app.js`  
**Lines**: `233–236` (`safeHref`)

**Issue**: Leading `/` in the regex allows `//evil.com` (protocol-relative) through to `href` / `src`.

**Fix**: Only allow `http:`, `https:`, `mailto:`, same-origin relative paths that are not `//`, plus `#` and `./` style if desired.

```javascript
function safeHref(url) {
  if (!url || typeof url !== "string") return "#";
  var u = url.trim();
  if (/^mailto:/i.test(u)) return u;
  if (/^https?:\/\//i.test(u)) return u;
  if (u.charAt(0) === "#") return u;
  if (u.charAt(0) === "/" && u.charAt(1) !== "/") return u;
  if (u.charAt(0) === ".") return u;
  return "#";
}
```

---

### 7. XSS — `simpleMarkdown` / `inlineFormat` image `alt` attribute

**File**: `src/testforge/web/static/app.js`  
**Lines**: `249–252` (image branch inside `inlineFormat`)

**Issue**: `alt` is concatenated raw into a double-quoted HTML attribute; a crafted alt can break out of `alt="..."`.

**Fix**: Escape `alt` the same way as other user text (reuse `esc`).

```javascript
  text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, function(_, alt, url) {
    return '<img src="' + safeHref(url) + '" alt="' + esc(alt) + '">';
  });
```

---

### 8. Auth — document localhost-only security boundary

**Files**: `README.md` and/or `CLAUDE.md` (or a short `docs/SECURITY.md` only if the project already uses a docs security section — prefer extending an existing “Running the server” section).

**Change**: No authentication code in v0.6. Explicitly document:

- The API is **unauthenticated** by design for local workflows.
- **Bind to `127.0.0.1`** (default); binding to `0.0.0.0` or exposing the port via tunnels **voids** the “local tool” threat model.
- Destructive and code-execution-class endpoints (delete project, PUT scripts, POST run) are **only acceptable** when network access to the server is restricted to the operator’s machine.

---

## ACCEPT (localhost context)

- **No auth layer** (`auth-audit.json`): Acceptable when the server listens on loopback and is operated as a single-user local tool; document boundary (see FIX NOW #8). Not acceptable for LAN/Internet exposure without future auth.
- **Realistic remote threat** to default CLI: auditor notes **low** for typical `127.0.0.1:8000`; residual risks are same-machine actors and browser-driven edge cases, not Internet-wide scraping.
- **Config test endpoint** (`GET .../config/test`): Acceptable informational leakage (key *presence*, Ollama probe) on localhost; still optionally tighten messaging in a later release.
- **Low-severity XSS maintenance notes** (`detail-body` pattern, static `onclick` on checkboxes, `className` from API status): Accept with continued discipline on `esc()`; not blocking for v0.6 if pipeline `data-tab` fixes are deferred.

---

## DEFER v0.7

- **Path traversal (medium)**: `scripts.py` `script_name` — require `Path(script_name).name == script_name` and reject `os.sep`; resolve under `p / "scripts"` with `is_relative_to` (`path-traversal.json`, ~line 84).
- **Path traversal (medium)**: `reports.py` `report_id` — strict charset or resolved path under `reports_dir` (~line 88).
- **Path traversal (medium)**: `execution.py` `run_id` — same hardening as report/script ids (~line 123).
- **LFI hardening in `parser.py`**: Central `allowed_file_root` / jail for **CLI and API** so `parse()` cannot open arbitrary paths when given a relative name; reject `file://` and exotic schemes at the parser boundary (`ssrf-lfi.json`).
- **`analyzer.py`**: Single shared “coerce inputs” helper used by web **and** CLI before `parse()` (or call validated API-layer helper from CLI).
- **SSRF advanced**: Re-enable redirects with **per-hop** host/IP validation and response size limits; optional domain allowlist for enterprises.
- **XSS — defense in depth**: DOMPurify (or sandboxed iframe) for `simpleMarkdown` output; `esc()` on `data-tab` / `nextTab` in pipeline stepper (~lines 1086, 1101); `esc` on link label text inside `inlineFormat` (~line 246); harden report/history `innerHTML` paths (~lines 2191, 3040).
- **XSS — low**: Regex-only script stripping in `simpleMarkdown` (~line 212–213) replaced by allowlist sanitization.
- **`validator.py`**: If wired into flows, separate path/URL gates from content-quality checks (`ssrf-lfi.json`).
- **Auth product work**: API tokens, localhost-only middleware toggle, CSRF considerations if cookies are ever introduced.

---

## Traceability (diagnostic → action)

| Diagnostic | FIX NOW | ACCEPT | DEFER v0.7 |
|------------|---------|--------|------------|
| `path-traversal.json` | `manual.py`, `projects.py` (list + create), `analysis.py` inputs | — | `scripts.py`, `reports.py`, `execution.py` |
| `xss-vectors.json` | `safeHref`, `img` `alt` + `esc` | Low-risk patterns on localhost | DOMPurify / sandbox, pipeline attrs, bulk `innerHTML` sites |
| `ssrf-lfi.json` | `url.py` + `analysis.py` coercion | — | Redirect hops, `parser.py` jail, CLI parity, scheme rejects |
| `auth-audit.json` | Document boundary | Unauthenticated API on loopback | Tokens, bind enforcement, production hardening |
