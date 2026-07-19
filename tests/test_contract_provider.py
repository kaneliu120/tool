"""4-URL contract tests against mock provider (software canary)."""

from __future__ import annotations

import yaml
from pathlib import Path

import pytest

from rea_unblocker.classifier.html import classify_html
from rea_unblocker.parser.argonaut import parse_listings_from_html
from rea_unblocker.providers.mock import MockHtmlProvider

PROFILE = Path(__file__).resolve().parents[1] / "config" / "rea-target-profile.yaml"


@pytest.mark.asyncio
async def test_four_url_contract_mock_provider():
    profile = yaml.safe_load(PROFILE.read_text(encoding="utf-8"))
    provider = MockHtmlProvider()
    for case in profile["contractTests"]:
        result = await provider.fetch(case["url"], kind=case["kind"])
        c = classify_html(result.html)
        assert c["bytes"] >= case["minBytes"], case["id"]
        assert c["hasArgonaut"] is case["requireArgonaut"], case["id"]
        assert result.blocked is False, case["id"]
        rows = parse_listings_from_html(result.html, kind=case["kind"])
        if case.get("minListings"):
            assert len(rows) >= case["minListings"], case["id"]
        if case.get("requireDetailId"):
            assert rows and rows[0].get("listingId"), case["id"]


@pytest.mark.asyncio
async def test_kpsdk_shell_fail_closed():
    provider = MockHtmlProvider()
    result = await provider.fetch(
        "https://www.realestate.com.au/buy/in-melbourne,+vic/list-1",
        kind="sale_search",
        context={"forceKpsdkShell": True},
    )
    c = classify_html(result.html)
    assert c["tinyKasadaShell"] is True
    assert result.blocked is True
    assert result.status_code == 429
