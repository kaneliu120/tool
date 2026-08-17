"""HTTP client for the self-hosted Mem0 gateway.

Cloud Agents cannot use macOS Keychain or the SSH tunnel to REST
``localhost:8888``. The supported path is the public MCP host with
``MEM0_API_KEY`` (Bearer / X-API-Key). Do not use stdlib ``urllib``:
Cloudflare returns 1010 for that User-Agent.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

DEFAULT_MCP_URL = "https://mem0-mcp.opendata.best"
DEFAULT_USER_ID = "kane"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; mem0ctl/0.1; +https://github.com/kaneliu120/tool)"
)

_SEARCH_TOOLS = ("search_memories", "search", "mem0_search")
_ADD_TOOLS = ("add_memory", "add_memories", "add")
_LIST_TOOLS = ("get_memories", "list_memories", "list")


class Mem0Error(RuntimeError):
    """Raised when the Mem0 gateway rejects or fails a request."""


@dataclass(frozen=True)
class Mem0Config:
    api_key: str | None = None
    mcp_url: str = DEFAULT_MCP_URL
    rest_url: str | None = None
    user_id: str = DEFAULT_USER_ID
    timeout_s: float = 30.0
    user_agent: str = DEFAULT_USER_AGENT

    @classmethod
    def from_env(cls) -> Mem0Config:
        rest = os.environ.get("MEM0_REST_URL", "").strip() or None
        return cls(
            api_key=os.environ.get("MEM0_API_KEY", "").strip() or None,
            mcp_url=os.environ.get("MEM0_MCP_URL", DEFAULT_MCP_URL).rstrip("/"),
            rest_url=rest.rstrip("/") if rest else None,
            user_id=os.environ.get("MEM0_USER_ID", DEFAULT_USER_ID).strip() or DEFAULT_USER_ID,
        )


@dataclass
class Mem0Client:
    config: Mem0Config = field(default_factory=Mem0Config.from_env)
    _http: httpx.Client | None = field(default=None, init=False, repr=False)
    _session_id: str | None = field(default=None, init=False, repr=False)
    _rpc_id: int = field(default=0, init=False, repr=False)
    _mcp_endpoint: str | None = field(default=None, init=False, repr=False)
    _tools: dict[str, dict[str, Any]] | None = field(default=None, init=False, repr=False)

    def close(self) -> None:
        if self._http is not None:
            self._http.close()
            self._http = None

    def __enter__(self) -> Mem0Client:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def health(self) -> dict[str, Any]:
        response = self._client().get(
            self._url(self.config.mcp_url, "/healthz"),
            headers=self._base_headers(),
        )
        self._raise_http(response, auth_required=False)
        data = response.json()
        if not isinstance(data, dict):
            raise Mem0Error(f"unexpected health payload: {data!r}")
        return data

    def search(
        self,
        query: str,
        *,
        user_id: str | None = None,
        top_k: int = 5,
        threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        uid = user_id or self.config.user_id
        if self.config.rest_url:
            payload: dict[str, Any] = {
                "query": query,
                "filters": {"user_id": uid},
                "top_k": top_k,
            }
            if threshold is not None:
                payload["threshold"] = threshold
            data = self._rest_json("POST", "/search", json=payload)
            return _as_results(data)

        args: dict[str, Any] = {
            "query": query,
            "user_id": uid,
            "top_k": top_k,
            "filters": {"user_id": uid},
        }
        if threshold is not None:
            args["threshold"] = threshold
        data = self._call_tool(_SEARCH_TOOLS, args)
        return _as_results(data)

    def add(
        self,
        text: str,
        *,
        user_id: str | None = None,
        infer: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        uid = user_id or self.config.user_id
        messages = [{"role": "user", "content": text}]
        if self.config.rest_url:
            payload: dict[str, Any] = {
                "messages": messages,
                "user_id": uid,
                "infer": infer,
            }
            if metadata:
                payload["metadata"] = metadata
            data = self._rest_json("POST", "/memories", json=payload)
            return _as_dict(data)

        args: dict[str, Any] = {
            "text": text,
            "messages": messages,
            "user_id": uid,
            "infer": infer,
        }
        if metadata:
            args["metadata"] = metadata
        return _as_dict(self._call_tool(_ADD_TOOLS, args))

    def list_memories(
        self,
        *,
        user_id: str | None = None,
        top_k: int = 50,
    ) -> list[dict[str, Any]]:
        uid = user_id or self.config.user_id
        if self.config.rest_url:
            data = self._rest_json(
                "GET",
                "/memories",
                params={"user_id": uid, "top_k": top_k},
            )
            return _as_results(data)

        data = self._call_tool(
            _LIST_TOOLS,
            {"user_id": uid, "top_k": top_k, "filters": {"user_id": uid}},
        )
        return _as_results(data)

    def list_tools(self) -> list[str]:
        self._ensure_mcp()
        assert self._tools is not None
        return sorted(self._tools)

    def _client(self) -> httpx.Client:
        if self._http is None:
            self._http = httpx.Client(
                timeout=self.config.timeout_s,
                follow_redirects=True,
            )
        return self._http

    def _base_headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {"User-Agent": self.config.user_agent}
        if extra:
            headers.update(extra)
        return headers

    def _auth_headers(self) -> dict[str, str]:
        key = self.config.api_key
        if not key:
            raise Mem0Error(
                "MEM0_API_KEY is not set. Add it as a Cloud Agent Runtime Secret "
                "(and/or register HTTP MCP mem0-selfhost at cursor.com/agents with "
                "Authorization: Bearer <key>). Do not commit the key."
            )
        return {
            "Authorization": f"Bearer {key}",
            "X-API-Key": key,
        }

    def _rest_json(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        assert self.config.rest_url
        response = self._client().request(
            method,
            self._url(self.config.rest_url, path),
            headers=self._base_headers(
                {**self._auth_headers(), "Content-Type": "application/json"}
            ),
            json=json,
            params=params,
        )
        self._raise_http(response)
        return response.json()

    def _call_tool(self, names: tuple[str, ...], arguments: dict[str, Any]) -> Any:
        self._ensure_mcp()
        assert self._tools is not None
        tool = next((name for name in names if name in self._tools), None)
        if tool is None:
            available = ", ".join(sorted(self._tools)) or "(none)"
            raise Mem0Error(
                f"MCP gateway has no tool in {names}; available: {available}"
            )
        result = self._rpc(
            "tools/call",
            {"name": tool, "arguments": arguments},
        )
        if not isinstance(result, dict):
            return result
        if result.get("isError"):
            raise Mem0Error(f"MCP tool {tool} error: {_content_text(result)}")
        parsed = _parse_tool_payload(result)
        return parsed if parsed is not None else result

    def _ensure_mcp(self) -> None:
        if self._tools is not None:
            return
        last_error: Exception | None = None
        for endpoint in self._candidate_mcp_endpoints():
            try:
                self._mcp_endpoint = endpoint
                self._session_id = None
                self._rpc_id = 0
                init = self._rpc(
                    "initialize",
                    {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": "mem0ctl", "version": "0.1.0"},
                    },
                )
                if not isinstance(init, dict):
                    raise Mem0Error(f"initialize returned {init!r}")
                self._rpc("notifications/initialized", notification=True)
                listed = self._rpc("tools/list", {})
                tools = listed.get("tools") if isinstance(listed, dict) else None
                if not isinstance(tools, list):
                    raise Mem0Error(f"tools/list returned {listed!r}")
                self._tools = {
                    str(item["name"]): item
                    for item in tools
                    if isinstance(item, dict) and "name" in item
                }
                return
            except Mem0Error as exc:
                if "MEM0_API_KEY is not set" in str(exc):
                    raise
                last_error = exc
            except Exception as exc:  # noqa: BLE001 — try next MCP path
                last_error = exc
                self._session_id = None
                self._mcp_endpoint = None
                self._tools = None
        raise Mem0Error(f"could not initialize Mem0 MCP: {last_error}") from last_error

    def _candidate_mcp_endpoints(self) -> list[str]:
        base = self.config.mcp_url.rstrip("/")
        path = urlparse(base).path.rstrip("/")
        if path.endswith("/mcp"):
            return [base]
        return [f"{base}/mcp", base]

    def _rpc(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        notification: bool = False,
    ) -> Any:
        if not self._mcp_endpoint:
            raise Mem0Error("MCP endpoint is not selected")
        headers = self._base_headers(
            {
                **self._auth_headers(),
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
        )
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if not notification:
            self._rpc_id += 1
            payload["id"] = self._rpc_id
        if params is not None:
            payload["params"] = params
        response = self._client().post(self._mcp_endpoint, headers=headers, json=payload)
        session = response.headers.get("mcp-session-id") or response.headers.get(
            "Mcp-Session-Id"
        )
        if session:
            self._session_id = session
        if notification:
            if response.status_code in {202, 204}:
                return None
            if response.status_code >= 400:
                self._raise_http(response)
            return None
        self._raise_http(response)
        body = _decode_rpc_body(response)
        if not isinstance(body, dict):
            raise Mem0Error(f"MCP {method} returned {body!r}")
        if "error" in body:
            raise Mem0Error(f"MCP {method} error: {body['error']}")
        return body.get("result")

    def _raise_http(self, response: httpx.Response, *, auth_required: bool = True) -> None:
        if response.status_code < 400:
            return
        detail = response.text[:500]
        if response.status_code in {401, 403}:
            hint = (
                " Gateway requires a valid MEM0_API_KEY (Bearer or X-API-Key)."
                if auth_required
                else ""
            )
            raise Mem0Error(f"Mem0 HTTP {response.status_code}: {detail}{hint}")
        raise Mem0Error(f"Mem0 HTTP {response.status_code}: {detail}")

    @staticmethod
    def _url(base: str, path: str) -> str:
        return urljoin(base.rstrip("/") + "/", path.lstrip("/"))


def _decode_rpc_body(response: httpx.Response) -> Any:
    ctype = (response.headers.get("content-type") or "").lower()
    text = response.text
    if "text/event-stream" in ctype:
        last: Any = None
        for line in text.splitlines():
            if not line.startswith("data:"):
                continue
            chunk = line[5:].strip()
            if not chunk or chunk == "[DONE]":
                continue
            last = json.loads(chunk)
        if last is None:
            raise Mem0Error("empty MCP SSE response")
        return last
    if not text:
        raise Mem0Error("empty MCP response")
    return json.loads(text)


def _content_text(result: dict[str, Any]) -> str:
    content = result.get("content")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
        if parts:
            return "\n".join(parts)
    return json.dumps(result)


def _parse_tool_payload(result: dict[str, Any]) -> Any:
    text = _content_text(result)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"text": text}


def _as_dict(data: Any) -> dict[str, Any]:
    if isinstance(data, dict):
        return data
    return {"data": data}


def _as_results(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item if isinstance(item, dict) else {"value": item} for item in data]
    if isinstance(data, dict):
        for key in ("results", "memories", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [item if isinstance(item, dict) else {"value": item} for item in value]
        return [data]
    return [{"value": data}]
