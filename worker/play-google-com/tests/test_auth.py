from fastapi.testclient import TestClient

from src.main import app


def test_health_public(monkeypatch):
    monkeypatch.setenv("WORKER_API_KEY", "test-key-play")
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["worker"] == "play-google-com"


def test_search_unauth_401(monkeypatch):
    monkeypatch.setenv("WORKER_API_KEY", "test-key-play")
    client = TestClient(app)
    r = client.post("/v1/search", json={"q": "notes", "maxResults": 2})
    assert r.status_code == 401


def test_search_wrong_key_401(monkeypatch):
    monkeypatch.setenv("WORKER_API_KEY", "test-key-play")
    client = TestClient(app)
    r = client.post(
        "/v1/search",
        json={"q": "notes", "maxResults": 2},
        headers={"X-Api-Key": "nope"},
    )
    assert r.status_code == 401


def test_categories_auth(monkeypatch):
    monkeypatch.setenv("WORKER_API_KEY", "test-key-play")
    client = TestClient(app)
    r = client.get("/v1/categories", headers={"Authorization": "Bearer test-key-play"})
    assert r.status_code == 200
    items = r.json()["items"]
    codes = {row["listingId"] for row in items}
    assert "GAME" in codes
    assert "SPORTS" in codes


def test_openapi_public(monkeypatch):
    client = TestClient(app)
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert spec["components"]["securitySchemes"]["ApiKeyAuth"]["name"] == "X-Api-Key"
    assert "/v1/search" in spec["paths"]
