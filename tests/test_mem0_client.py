from __future__ import annotations

import json

import httpx
import pytest

from mem0_client.client import (
    DEFAULT_MCP_URL,
    Mem0Client,
    Mem0Config,
    Mem0Error,
)


def _rpc_result(result: object, *, rpc_id: int = 1) -> httpx.Response:
    return httpx.Response(
        200,
        json={"jsonrpc": "2.0", "id": rpc_id, "result": result},
        headers={"content-type": "application/json", "mcp-session-id": "sess-1"},
    )


def test_from_env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MEM0_API_KEY", raising=False)
    monkeypatch.delenv("MEM0_MCP_URL", raising=False)
    monkeypatch.delenv("MEM0_REST_URL", raising=False)
    monkeypatch.delenv("MEM0_USER_ID", raising=False)
    cfg = Mem0Config.from_env()
    assert cfg.mcp_url == DEFAULT_MCP_URL
    assert cfg.user_id == "kane"
    assert cfg.api_key is None
    assert cfg.rest_url is None


def test_search_requires_api_key() -> None:
    client = Mem0Client(Mem0Config(api_key=None, mcp_url="https://mem0-mcp.opendata.best"))
    with pytest.raises(Mem0Error, match="MEM0_API_KEY"):
        client.search("hiking Taipei")


def test_health_uses_public_healthz() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == "https://mem0-mcp.opendata.best/healthz"
        assert "Mozilla" in request.headers["user-agent"]
        return httpx.Response(200, json={"status": "ok", "service": "mem0-mcp"})

    client = Mem0Client(Mem0Config(mcp_url="https://mem0-mcp.opendata.best"))
    client._http = httpx.Client(transport=httpx.MockTransport(handler))
    assert client.health() == {"status": "ok", "service": "mem0-mcp"}


def test_rest_search_and_add() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        assert request.headers["x-api-key"] == "test-key"
        assert request.headers["authorization"] == "Bearer test-key"
        if request.url.path == "/search":
            body = json.loads(request.content)
            assert body["query"] == "hiking Taipei"
            assert body["filters"] == {"user_id": "kane"}
            return httpx.Response(
                200,
                json={"results": [{"memory": "Kane hikes in Taipei", "score": 0.95}]},
            )
        if request.url.path == "/memories" and request.method == "POST":
            body = json.loads(request.content)
            assert body["infer"] is False
            assert body["messages"][0]["content"] == "Backup runs 03:30 UTC"
            return httpx.Response(200, json={"id": "m1"})
        raise AssertionError(f"unexpected {request.method} {request.url}")

    cfg = Mem0Config(
        api_key="test-key",
        rest_url="http://127.0.0.1:8888",
        mcp_url="https://mem0-mcp.opendata.best",
    )
    client = Mem0Client(cfg)
    client._http = httpx.Client(transport=httpx.MockTransport(handler))
    results = client.search("hiking Taipei")
    assert results[0]["score"] == 0.95
    added = client.add("Backup runs 03:30 UTC", infer=False)
    assert added["id"] == "m1"
    assert len(seen) == 2


def test_mcp_search_discovers_tools() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://mem0-mcp.opendata.best/mcp"
        if request.method == "POST":
            payload = json.loads(request.content)
            calls.append(payload["method"])
            if payload["method"] == "initialize":
                return _rpc_result({"protocolVersion": "2025-03-26", "capabilities": {}})
            if payload["method"] == "notifications/initialized":
                return httpx.Response(202)
            if payload["method"] == "tools/list":
                return _rpc_result(
                    {
                        "tools": [
                            {"name": "search_memories"},
                            {"name": "add_memory"},
                            {"name": "handoff"},
                            {"name": "get"},
                        ]
                    },
                    rpc_id=2,
                )
            if payload["method"] == "tools/call":
                assert payload["params"]["name"] == "search_memories"
                assert payload["params"]["arguments"]["query"] == "Kane deploy"
                assert payload["params"]["arguments"]["meta_json"] == '{"kind":"handoff"}'
                return _rpc_result(
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {"results": [{"memory": "Cloud Run worker", "score": 0.8}]}
                                ),
                            }
                        ]
                    },
                    rpc_id=3,
                )
        raise AssertionError(request.content)

    client = Mem0Client(
        Mem0Config(api_key="test-key", mcp_url="https://mem0-mcp.opendata.best")
    )
    client._http = httpx.Client(transport=httpx.MockTransport(handler))
    results = client.search("Kane deploy", meta_json='{"kind":"handoff"}')
    assert results[0]["memory"] == "Cloud Run worker"
    assert calls[:4] == [
        "initialize",
        "notifications/initialized",
        "tools/list",
        "tools/call",
    ]


def test_mcp_handoff_calls_handoff_tool() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        if payload["method"] == "initialize":
            return _rpc_result({"protocolVersion": "2025-03-26", "capabilities": {}})
        if payload["method"] == "notifications/initialized":
            return httpx.Response(202)
        if payload["method"] == "tools/list":
            return _rpc_result({"tools": [{"name": "handoff"}]}, rpc_id=2)
        if payload["method"] == "tools/call":
            assert payload["params"]["name"] == "handoff"
            args = payload["params"]["arguments"]
            assert args["project"] == "tool"
            assert args["next_steps"] == "open PR"
            return _rpc_result(
                {"content": [{"type": "text", "text": json.dumps({"id": "h1"})}]},
                rpc_id=3,
            )
        raise AssertionError(payload)

    client = Mem0Client(
        Mem0Config(api_key="test-key", mcp_url="https://mem0-mcp.opendata.best")
    )
    client._http = httpx.Client(transport=httpx.MockTransport(handler))
    result = client.handoff(
        project="tool",
        verdict="hooks were incomplete",
        done="added handoff CLI",
        status="fixed",
        next_steps="open PR",
        gotchas="system python3 lacked httpx",
        evidence="pytest",
    )
    assert result["id"] == "h1"


def test_unauthorized_is_mem0_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": "unauthorized", "message": "Valid Bearer or X-API-Key required"},
        )

    client = Mem0Client(
        Mem0Config(api_key="bad", mcp_url="https://mem0-mcp.opendata.best")
    )
    client._http = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(Mem0Error, match="401"):
        client.health()


def test_cli_handoff_help_exits_zero() -> None:
    from mem0_client.cli import main

    with pytest.raises(SystemExit) as exc:
        main(["handoff", "--help"])
    assert exc.value.code == 0


def test_live_public_healthz() -> None:
    with Mem0Client(Mem0Config(mcp_url=DEFAULT_MCP_URL)) as client:
        data = client.health()
    assert data.get("status") == "ok"
    assert data.get("service") == "mem0-mcp"
