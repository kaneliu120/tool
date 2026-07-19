"""Apify Actor-facing HTML acquisition client (copy/import into Actor code)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import httpx

from rea_unblocker.classifier.html import classify_html
from rea_unblocker.parser.argonaut import parse_listings_from_html
from rea_unblocker.providers.base import FetchResult
from rea_unblocker.providers.mock import MockHtmlProvider
from rea_unblocker.providers.registry import ProviderRegistry, build_default_registry


@dataclass
class RunSummary:
    provider: str
    requestedProvider: str | None
    totalFetches: int = 0
    blockedCount: int = 0
    hasArgonautCount: int = 0
    datasetRows: int = 0
    errors: list[str] = field(default_factory=list)
    bytesTotal: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def assert_canary(self, *, min_rows: int = 2) -> None:
        if self.datasetRows < min_rows:
            raise AssertionError(f"canary failed: datasetRows={self.datasetRows} < {min_rows}")
        if self.blockedCount > 0:
            raise AssertionError(f"canary failed: blockedCount={self.blockedCount}")
        if self.hasArgonautCount < min_rows:
            raise AssertionError(
                f"canary failed: hasArgonautCount={self.hasArgonautCount} < {min_rows}"
            )


class ActorHtmlClient:
    """Thin acquisition layer used by the REA Actor business logic."""

    def __init__(
        self,
        *,
        provider_name: str | None = "internal_mac_runner",
        gateway_url: str | None = None,
        gateway_token: str | None = None,
        registry: ProviderRegistry | None = None,
        use_mock_if_missing: bool = False,
    ) -> None:
        self.provider_name = provider_name
        self.gateway_url = gateway_url.rstrip("/") if gateway_url else None
        self.gateway_token = gateway_token
        self.registry = registry or build_default_registry(include_mock=use_mock_if_missing)
        if use_mock_if_missing and "mock_fixture" not in self.registry.names():
            self.registry.register(MockHtmlProvider())
        self.summary = RunSummary(
            provider=provider_name or "auto",
            requestedProvider=provider_name,
        )

    async def fetch(self, url: str, *, kind: str, context: dict[str, Any] | None = None) -> FetchResult:
        if self.gateway_url:
            result = await self._fetch_via_gateway(url, kind=kind, context=context or {})
        else:
            result = await self.registry.fetch(
                url,
                kind=kind,
                provider=self.provider_name if self.provider_name != "auto" else None,
                context=context,
                failover=True,
            )
        self._update_summary(result)
        return result

    async def _fetch_via_gateway(
        self,
        url: str,
        *,
        kind: str,
        context: dict[str, Any],
    ) -> FetchResult:
        headers = {"Content-Type": "application/json"}
        if self.gateway_token:
            headers["Authorization"] = f"Bearer {self.gateway_token}"
        payload = {
            "target": "realestate.com.au",
            "url": url,
            "kind": kind,
            "provider": self.provider_name,
            "return": ["html", "diagnostics"],
            "context": context,
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                f"{self.gateway_url}/v1/fetch-html",
                json=payload,
                headers=headers,
            )
        data = resp.json()
        html = data.get("html") or ""
        classification = classify_html(html)
        return FetchResult(
            url=url,
            final_url=data.get("finalUrl"),
            html=html,
            status_code=data.get("statusCode"),
            provider=data.get("provider") or "gateway",
            engine=data.get("engine"),
            blocked=bool(data.get("blocked") or classification["blocked"]),
            error=data.get("error"),
            diagnostics=data.get("diagnostics") or {"classification": classification},
        )

    def _update_summary(self, result: FetchResult) -> None:
        self.summary.totalFetches += 1
        self.summary.provider = result.provider
        classification = (result.diagnostics or {}).get("classification") or classify_html(
            result.html
        )
        self.summary.bytesTotal += int(classification.get("bytes") or 0)
        if result.blocked or classification.get("blocked"):
            self.summary.blockedCount += 1
        if classification.get("hasArgonaut"):
            self.summary.hasArgonautCount += 1
        if result.error:
            self.summary.errors.append(result.error)

    async def fetch_and_parse(
        self,
        url: str,
        *,
        kind: str,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        result = await self.fetch(url, kind=kind, context=context)
        if result.blocked or not result.html:
            return []
        rows = parse_listings_from_html(result.html, kind=kind)
        # Fail closed: never invent rows from a shell page.
        classification = classify_html(result.html)
        if classification["blocked"] or not classification["hasArgonaut"]:
            self.summary.blockedCount = max(self.summary.blockedCount, 1)
            return []
        self.summary.datasetRows += len(rows)
        return rows
