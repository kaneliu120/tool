#!/usr/bin/env python3
"""Cloud Agent substitute for macOS chrome_js_bridge.py.

Loads the stock website-page-research probe JS in headless Chrome/Chromium
and prints the probe JSON. Does not click Apply / pay / login, solve
captchas, or forge signatures.

  .venv/bin/python scripts/playwright_page_probe.py --url 'https://example.com/'
  .venv/bin/python scripts/playwright_page_probe.py --url URL --js rsc
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

SKILL_SCRIPTS = Path(__file__).resolve().parent
JS_ALIASES = {
    "generic": SKILL_SCRIPTS / "generic_page_probe.js",
    "rsc": SKILL_SCRIPTS / "rsc_keyword_grep.js",
}
MAX_OUTPUT = 200_000


def _js_path(value: str) -> Path:
    alias = JS_ALIASES.get(value)
    if alias is not None:
        return alias
    path = Path(value)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"JS file not found: {value}")
    return path


def _launch_chromium(playwright):  # noqa: ANN001 — playwright type is optional at import
    chrome = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    kwargs: dict = {"headless": True}
    if chrome:
        kwargs["channel"] = "chrome"
    try:
        return playwright.chromium.launch(**kwargs)
    except Exception:
        kwargs.pop("channel", None)
        return playwright.chromium.launch(**kwargs)


def probe(url: str, js_path: Path, timeout_ms: int) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover — install.sh extra
        raise SystemExit(
            "FAIL: playwright missing. Run ./.cursor/install.sh "
            '(pip extra "recon").'
        ) from exc

    source = js_path.read_text(encoding="utf-8")
    with sync_playwright() as playwright:
        browser = _launch_chromium(playwright)
        try:
            page = browser.new_page()
            page.set_default_timeout(timeout_ms)
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(1500)
            raw = page.evaluate(source)
        finally:
            browser.close()

    if raw is None:
        return json.dumps({"error": "probe returned null"})
    if isinstance(raw, (dict, list)):
        text = json.dumps(raw, ensure_ascii=False)
    else:
        text = str(raw)
    if len(text) > MAX_OUTPUT:
        return json.dumps(
            {
                "error": "probe output truncated",
                "bytes": len(text),
                "preview": text[:8000],
            },
            ensure_ascii=False,
        )
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Exact URL to open (one surface)")
    parser.add_argument(
        "--js",
        default="generic",
        type=_js_path,
        help="generic | rsc | path to a probe JS file",
    )
    parser.add_argument("--timeout-ms", type=int, default=25000)
    args = parser.parse_args()
    # argparse does not run `type` on the default; normalize here.
    js_path = args.js if isinstance(args.js, Path) else _js_path(str(args.js))
    print(probe(args.url, js_path, args.timeout_ms))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
