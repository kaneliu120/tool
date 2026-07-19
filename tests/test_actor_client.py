import pytest

from rea_unblocker.actor.client import ActorHtmlClient


@pytest.mark.asyncio
async def test_actor_canary_with_mock():
    client = ActorHtmlClient(
        provider_name="mock_fixture",
        use_mock_if_missing=True,
    )
    sale = await client.fetch_and_parse(
        "https://www.realestate.com.au/buy/in-melbourne,+vic/list-1",
        kind="sale_search",
    )
    rent = await client.fetch_and_parse(
        "https://www.realestate.com.au/rent/in-melbourne,+vic/list-1",
        kind="rent_search",
    )
    rows = sale + rent
    assert len(rows) >= 2
    for row in rows:
        assert row.get("listingId")
        assert row.get("url")
        assert row.get("address")
        assert row.get("price")
        assert row.get("listingType")
    client.summary.datasetRows = len(rows)
    client.summary.assert_canary(min_rows=2)
    summary = client.summary.to_dict()
    assert summary["provider"] == "mock_fixture"
    assert summary["blockedCount"] == 0
    assert summary["hasArgonautCount"] >= 2


@pytest.mark.asyncio
async def test_shell_does_not_produce_rows():
    client = ActorHtmlClient(provider_name="mock_fixture", use_mock_if_missing=True)
    rows = await client.fetch_and_parse(
        "https://www.realestate.com.au/buy/in-melbourne,+vic/list-1",
        kind="sale_search",
        context={"forceKpsdkShell": True},
    )
    assert rows == []
    assert client.summary.blockedCount >= 1
