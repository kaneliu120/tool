from src.free_tier import clamp_max_results, is_paying_user
from src.input_model import parse_input
from src.worker_client import resolve_worker_endpoint, worker_provides_proxy


def test_empty_input_defaults():
    cfg = parse_input({})
    assert cfg.mode == "search"
    assert cfg.q == "flashlight"
    assert cfg.market == "us"
    payload = cfg.to_worker_payload()
    assert "proxyUrl" not in payload
    assert payload["q"] == "flashlight"


def test_clamp_free():
    assert clamp_max_results(5000, is_limited=True) == (200, True)
    assert clamp_max_results(50, is_limited=True) == (50, False)


def test_paying_local_bypass():
    from types import SimpleNamespace

    actor = SimpleNamespace(
        is_at_home=lambda: False,
        configuration=SimpleNamespace(user_is_paying=False),
    )
    assert is_paying_user(actor) is True


def test_resolve_prefers_input(monkeypatch):
    monkeypatch.setenv("WORKER_BASE_URL", "https://env.example.run.app")
    ep = resolve_worker_endpoint("https://input.example.run.app")
    assert ep.source == "input"
    assert ep.base_url == "https://input.example.run.app"


def test_resolve_uses_env(monkeypatch):
    monkeypatch.setenv("WORKER_BASE_URL", "https://env.example.run.app/")
    ep = resolve_worker_endpoint(None)
    assert ep.base_url == "https://env.example.run.app"
    assert ep.source == "env"


def test_reject_http_remote(monkeypatch):
    monkeypatch.delenv("WORKER_BASE_URL", raising=False)
    from src.errors import AcquisitionError
    import pytest

    with pytest.raises(AcquisitionError):
        resolve_worker_endpoint("http://evil.example.com")


def test_worker_provides_proxy(monkeypatch):
    monkeypatch.setenv("WORKER_PROVIDES_PROXY", "1")
    assert worker_provides_proxy() is True


def test_browserforge_pin_avoids_data_files_crash():
    from pathlib import Path

    req = Path(__file__).resolve().parents[1].joinpath("requirements.txt").read_text()
    assert "browserforge==1.2.3" in req


def test_omit_nulls_drops_json_nulls():
    from src.rows import omit_nulls

    out = omit_nulls({"name": "Bloom Tiles", "developer": None, "ratingValue": None, "n": 0})
    assert out == {"name": "Bloom Tiles", "n": 0}


def test_actor_matrix_covers_secondary_and_enrich():
    import json
    from pathlib import Path

    matrix = json.loads(Path(__file__).resolve().parents[1].joinpath("coverage-matrix.json").read_text())
    markets = {c["market"] for c in matrix["cells"]}
    assert {"us", "jp", "de", "br"} <= markets
    assert any(c.get("template", {}).get("enrichDetails") for c in matrix["cells"])
    assert any(c.get("template", {}).get("category") == "GAME_WORD" for c in matrix["cells"])
