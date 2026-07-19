"""Deterministic fixture provider for contract tests and local CI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rea_unblocker.classifier.html import classify_html
from rea_unblocker.providers.base import FetchResult

FIXTURES = Path(__file__).resolve().parents[3] / "tests" / "fixtures"


class MockHtmlProvider:
    """Serves local fixtures keyed by kind. Never hits the network."""

    name = "mock_fixture"

    def __init__(self, fixtures_dir: Path | None = None) -> None:
        self.fixtures_dir = fixtures_dir or FIXTURES
        self._map = {
            "sale_search": "argonaut_sale_srp.html",
            "rent_search": "argonaut_rent_srp.html",
            "sale_detail": "argonaut_sale_ldp.html",
            "rent_detail": "argonaut_rent_ldp.html",
            "kpsdk_shell": "kpsdk_shell_live.html",
        }

    async def fetch(
        self,
        url: str,
        *,
        kind: str,
        context: dict[str, Any] | None = None,
    ) -> FetchResult:
        context = context or {}
        force_shell = bool(context.get("forceKpsdkShell"))
        key = "kpsdk_shell" if force_shell else kind
        filename = self._map.get(key)
        if not filename:
            return FetchResult(
                url=url,
                final_url=url,
                html="",
                status_code=None,
                provider=self.name,
                engine="fixture",
                blocked=True,
                error=f"unsupported kind: {kind}",
            )

        path = self.fixtures_dir / filename
        html = path.read_text(encoding="utf-8")
        classification = classify_html(html)
        return FetchResult(
            url=url,
            final_url=url,
            html=html,
            status_code=429 if classification["tinyKasadaShell"] else 200,
            provider=self.name,
            engine="fixture",
            blocked=bool(classification["blocked"]),
            diagnostics={
                "classification": classification,
                "fixture": filename,
            },
        )
