"""Mac Chrome runner worker skeleton.

This module is intentionally a deployable interface for a real macOS host.
In CI/cloud Linux it will raise unless PLAYWRIGHT is available and
REA_ALLOW_LINUX_RUNNER=1 is set for non-production experiments.
"""

from __future__ import annotations

import os
import platform
from typing import Any

from rea_unblocker.classifier.html import classify_html
from rea_unblocker.providers.base import FetchResult


class MacChromeRunner:
    name = "internal_mac_runner"
    engine = "mac-chrome-patchright"

    def __init__(self, *, headless: bool = False, proxy: dict[str, Any] | None = None) -> None:
        self.headless = headless
        self.proxy = proxy or {}

    def _assert_environment(self) -> None:
        system = platform.system().lower()
        if system == "darwin":
            return
        if os.getenv("REA_ALLOW_LINUX_RUNNER") == "1":
            return
        raise RuntimeError(
            "MacChromeRunner requires macOS (or REA_ALLOW_LINUX_RUNNER=1 for experiments). "
            "Do not use Apify Xvfb as the REA default path."
        )

    async def fetch(
        self,
        url: str,
        *,
        kind: str,
        context: dict[str, Any] | None = None,
    ) -> FetchResult:
        self._assert_environment()
        context = context or {}
        try:
            from playwright.async_api import async_playwright  # type: ignore
        except ImportError as exc:
            return FetchResult(
                url=url,
                final_url=None,
                html="",
                status_code=None,
                provider=self.name,
                engine=self.engine,
                blocked=True,
                error=f"playwright/patchright not installed: {exc}",
            )

        timeout_ms = int(context.get("timeoutMs") or 90_000)
        async with async_playwright() as p:
            launch_args: dict[str, Any] = {
                "headless": self.headless,
                "channel": context.get("channel", "chrome"),
            }
            proxy = context.get("proxy") or self.proxy
            if proxy and proxy.get("server"):
                launch_args["proxy"] = {
                    "server": proxy["server"],
                    "username": proxy.get("username"),
                    "password": proxy.get("password"),
                }
            browser = await p.chromium.launch(**launch_args)
            page = await browser.new_page()
            try:
                # Warmup homepage then target URL (document §5.4).
                if context.get("warmup", True):
                    await page.goto(
                        "https://www.realestate.com.au/",
                        wait_until="domcontentloaded",
                        timeout=timeout_ms,
                    )
                response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                # Best-effort wait for Argonaut; ignore timeout.
                try:
                    await page.wait_for_function(
                        "() => document.documentElement.outerHTML.includes('ArgonautExchange')",
                        timeout=min(15_000, timeout_ms),
                    )
                except Exception:
                    pass
                html = await page.content()
                classification = classify_html(html)
                return FetchResult(
                    url=url,
                    final_url=page.url,
                    html=html,
                    status_code=response.status if response else None,
                    provider=self.name,
                    engine=self.engine,
                    blocked=bool(classification["blocked"]),
                    diagnostics={
                        "classification": classification,
                        "kind": kind,
                        "platform": platform.platform(),
                    },
                )
            finally:
                await browser.close()
