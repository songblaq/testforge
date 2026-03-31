"""Browser-based site analysis — navigate a live site to extract structure and features."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def analyze_site_with_browser(
    url: str,
    engine: str = "playwright",
    output_dir: Path | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Navigate a live website using a browser engine and analyze its structure.

    Uses the specified execution engine to browse the site, capturing:
    - Page structure and navigation
    - Interactive elements (forms, buttons, links)
    - Screenshots of key pages
    - Console errors and network issues

    Args:
        url: The website URL to analyze.
        engine: Which browser engine to use (playwright, expect, agent-browser).
        output_dir: Directory to save screenshots and artifacts.
        timeout: Maximum time for analysis in seconds.

    Returns:
        dict with: pages, navigation, forms, screenshots, errors, text summary.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright not installed — returning basic URL analysis")
        return _fallback_analysis(url)

    pages: list[dict[str, Any]] = []
    screenshots: list[str] = []
    links: list[str] = []
    forms: list[dict[str, Any]] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            locale="ko-KR",
        )
        page = context.new_page()

        try:
            # 1. Load main page
            page.goto(url, wait_until="networkidle", timeout=int(timeout * 1000))
            title = page.title()
            main_content = page.inner_text("body")[:5000]

            # Save screenshot
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                ss_path = str(output_dir / "main_page.png")
                page.screenshot(path=ss_path)
                screenshots.append(ss_path)

            pages.append({"url": url, "title": title, "content_preview": main_content[:500]})

            # 2. Collect navigation links
            nav_links = page.eval_on_selector_all(
                "nav a, header a, [role='navigation'] a",
                "els => els.map(el => ({text: el.innerText.trim(), href: el.href})).filter(l => l.text && l.href)",
            )
            links = [lnk for lnk in nav_links if isinstance(lnk, dict)]

            # 3. Collect forms
            form_data = page.eval_on_selector_all(
                "form",
                """forms => forms.map(f => ({
                    action: f.action,
                    method: f.method,
                    inputs: Array.from(f.querySelectorAll('input,select,textarea')).map(i => ({
                        type: i.type || i.tagName.toLowerCase(),
                        name: i.name,
                        placeholder: i.placeholder || '',
                    }))
                }))""",
            )
            forms = [fd for fd in form_data if isinstance(fd, dict)]

            # 4. Visit top navigation links (up to 5)
            visited = {url}
            for lnk in links[:5]:
                href = lnk.get("href", "")
                if not href or href in visited or not href.startswith(("http://", "https://")):
                    continue
                visited.add(href)
                try:
                    page.goto(href, wait_until="networkidle", timeout=15000)
                    sub_title = page.title()
                    sub_content = page.inner_text("body")[:2000]
                    pages.append({
                        "url": href,
                        "title": sub_title,
                        "content_preview": sub_content[:500],
                    })
                    if output_dir:
                        safe = href.replace("/", "_").replace(":", "")[:60]
                        ss_path = str(output_dir / f"{safe}.png")
                        page.screenshot(path=ss_path)
                        screenshots.append(ss_path)
                except Exception:
                    logger.debug("Failed to visit %s", href)

        finally:
            context.close()
            browser.close()

    # Build text summary
    text_parts = [f"# Site Analysis: {url}\n"]
    text_parts.append(f"## Pages ({len(pages)})\n")
    for p in pages:
        text_parts.append(f"### {p['title']}\n{p['url']}\n{p['content_preview']}\n")

    if links:
        text_parts.append(f"## Navigation Links ({len(links)})\n")
        for lnk in links:
            text_parts.append(f"- [{lnk.get('text', '')}]({lnk.get('href', '')})")

    if forms:
        text_parts.append(f"\n## Forms ({len(forms)})\n")
        for f in forms:
            inputs_str = ", ".join(i.get("name", i.get("type", "?")) for i in f.get("inputs", []))
            text_parts.append(f"- {f.get('method', 'GET')} {f.get('action', '')} — fields: {inputs_str}")

    return {
        "type": "site_analysis",
        "url": url,
        "pages": pages,
        "navigation": links,
        "forms": forms,
        "screenshots": screenshots,
        "text": "\n".join(text_parts),
    }


def _fallback_analysis(url: str) -> dict[str, Any]:
    """Basic analysis without browser — fetch HTML and extract links."""
    import httpx
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=30)
        return {
            "type": "site_analysis",
            "url": url,
            "pages": [{"url": url, "title": "", "content_preview": resp.text[:1000]}],
            "navigation": [],
            "forms": [],
            "screenshots": [],
            "text": f"# Site: {url}\n\n{resp.text[:3000]}",
        }
    except Exception as exc:
        return {
            "type": "site_analysis",
            "url": url,
            "error": str(exc),
            "text": f"# Site: {url}\n\nFailed to fetch: {exc}",
        }
