import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("REA_INCLUDE_MOCK", "1")
    monkeypatch.delenv("REA_GATEWAY_TOKEN", raising=False)
    from rea_unblocker.gateway.app import app

    return TestClient(app)


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert "mock_fixture" in resp.json()["providers"]


def test_fetch_html_success(client):
    resp = client.post(
        "/v1/fetch-html",
        json={
            "target": "realestate.com.au",
            "url": "https://www.realestate.com.au/buy/in-melbourne,+vic/list-1",
            "kind": "sale_search",
            "provider": "mock_fixture",
            "return": ["html", "diagnostics"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["hasArgonaut"] is True
    assert data["bytes"] > 100_000
    assert "ArgonautExchange" in data["html"]


def test_fetch_html_rejects_non_allowlisted_host(client):
    resp = client.post(
        "/v1/fetch-html",
        json={
            "url": "https://example.com/",
            "kind": "sale_search",
        },
    )
    assert resp.status_code == 400


def test_fetch_html_shell_not_ok(client):
    resp = client.post(
        "/v1/fetch-html",
        json={
            "url": "https://www.realestate.com.au/buy/in-melbourne,+vic/list-1",
            "kind": "sale_search",
            "provider": "mock_fixture",
            "context": {"forceKpsdkShell": True},
            "return": ["diagnostics"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is False
    assert data["blocked"] is True
