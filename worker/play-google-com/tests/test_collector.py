from src.models import SearchRequest
from src.parse import parse_search_cards


def test_collector_mocked_search(monkeypatch):
    from src import collector

    html = open(
        "tests/fixtures/search_card.html", encoding="utf-8"
    ).read()
    html = "AF_initDataCallback({key: 'ds:0'});" + html

    class Fake:
        url = "https://play.google.com/store/search?q=notes&c=apps"
        status_code = 200
        text = html
        nbytes = len(html)
        provider = "curl_cffi:chrome136"
        error = None

    monkeypatch.setattr(collector, "fetch_html", lambda url, **kw: Fake())
    monkeypatch.setattr(collector.egress_control_client, "apply_runtime_env", lambda n: {"source": "env_fallback"})
    env = collector.run_search(SearchRequest(q="notes", maxResults=5, market="us"))
    assert env["status"] == "ok"
    assert env["worker"] == "play-google-com"
    assert env["schemaVersion"] == "2026-08-18.2"
    assert env["items"][0]["listingId"] == "com.google.android.keep"
    assert parse_search_cards(html, channel="search", hl="en", gl="US")


def test_collector_empty_shelf(monkeypatch):
    from src import collector

    html = "AF_initDataCallback({key:'ds:0'}); <html><title>Dating</title></html>"

    class Fake:
        url = "https://play.google.com/store/apps/category/DATING"
        status_code = 200
        text = html
        nbytes = len(html)
        provider = "curl_cffi:chrome136"
        error = None

    monkeypatch.setattr(collector, "fetch_html", lambda url, **kw: Fake())
    monkeypatch.setattr(collector.egress_control_client, "apply_runtime_env", lambda n: {"source": "env_fallback"})
    env = collector.run_search(SearchRequest(mode="category", category="DATING", market="us"))
    assert env["status"] == "empty"
    assert env["items"] == []
    assert env["warnings"]
