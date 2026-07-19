"""HTTP client for external real Chrome runners (Mac/Windows)."""

from __future__ import annotations

import os
from typing import Any

import httpx

from rea_unblocker.classifier.html import classify_html
from rea_unblocker.providers.base import FetchResult


class RemoteRunnerProvider:
    """Calls a self-hosted runner gateway implementing POST /v1/fetch."""

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        token: str | None = None,
        timeout_ms: int = 90_000,
        engine_hint: str | None = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_ms = timeout_ms
        self.engine_hint = engine_hint or name

    async def fetch(
        self,
        url: str,
        *,
        kind: str,
        context: dict[str, Any] | None = None,
    ) -> FetchResult:
        context = context or {}
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        payload = {
            "url": url,
            "kind": kind,
            "profilePolicy": context.get("profilePolicy", "sticky_by_target_region"),
            "proxy": context.get("proxy")
            or {
                "country": context.get("proxyCountry", "AU"),
                "sessionId": context.get("sessionId"),
            },
            "timeoutMs": context.get("timeoutMs", self.timeout_ms),
            "return": ["html", "diagnostics"],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_ms / 1000) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/fetch",
                    json=payload,
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            return FetchResult(
                url=url,
                final_url=None,
                html="",
                status_code=None,
                provider=self.name,
                engine=self.engine_hint,
                blocked=True,
                error=f"runner transport error: {exc}",
            )

        if resp.status_code >= 400:
            return FetchResult(
                url=url,
                final_url=None,
                html="",
                status_code=resp.status_code,
                provider=self.name,
                engine=self.engine_hint,
                blocked=True,
                error=f"runner http {resp.status_code}: {resp.text[:300]}",
            )

        data = resp.json()
        html = data.get("html") or ""
        classification = classify_html(html)
        blocked = bool(data.get("blocked", classification["blocked"]))
        return FetchResult(
            url=url,
            final_url=data.get("finalUrl") or data.get("final_url"),
            html=html,
            status_code=data.get("statusCode") or data.get("status_code"),
            provider=self.name,
            engine=data.get("engine") or self.engine_hint,
            blocked=blocked,
            error=data.get("error"),
            diagnostics={
                "classification": classification,
                "runner": data.get("diagnostics") or {},
            },
        )


def mac_runner_from_env() -> RemoteRunnerProvider | None:
    base = os.getenv("REA_MAC_RUNNER_URL")
    if not base:
        return None
    return RemoteRunnerProvider(
        name="internal_mac_runner",
        base_url=base,
        token=os.getenv("REA_MAC_RUNNER_TOKEN"),
        engine_hint="mac-chrome-patchright",
    )


def windows_runner_from_env() -> RemoteRunnerProvider | None:
    base = os.getenv("REA_WIN_RUNNER_URL")
    if not base:
        return None
    return RemoteRunnerProvider(
        name="internal_windows_runner",
        base_url=base,
        token=os.getenv("REA_WIN_RUNNER_TOKEN"),
        engine_hint="win-chrome",
    )
