"""FastAPI HTML Provider Gateway — POST /v1/fetch-html."""

from __future__ import annotations

import os
from typing import Any, Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from rea_unblocker.classifier.html import classify_html
from rea_unblocker.providers.registry import build_default_registry

app = FastAPI(
    title="REA HTML Provider Gateway",
    version="0.1.0",
    description="Unified fetch-html gateway for self-hosted unblock runners",
)

ALLOWED_HOST_SUFFIXES = (
    "realestate.com.au",
)


class FetchRequest(BaseModel):
    target: str = "realestate.com.au"
    url: str
    kind: str = "sale_search"
    render: bool = True
    sessionPolicy: str | None = "sticky_au_residential"
    timeoutMs: int = 90_000
    provider: str | None = None
    failover: bool = True
    return_fields: list[Literal["html", "diagnostics"]] = Field(
        default_factory=lambda: ["html", "diagnostics"],
        alias="return",
    )
    context: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


def _assert_url_allowed(url: str) -> None:
    from urllib.parse import urlparse

    host = (urlparse(url).hostname or "").lower()
    if not host or not any(host == s or host.endswith("." + s) for s in ALLOWED_HOST_SUFFIXES):
        raise HTTPException(status_code=400, detail=f"url host not allowlisted: {host}")


def _auth_ok(authorization: str | None) -> bool:
    expected = os.getenv("REA_GATEWAY_TOKEN")
    if not expected:
        return True
    if not authorization or not authorization.startswith("Bearer "):
        return False
    return authorization.removeprefix("Bearer ").strip() == expected


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    registry = build_default_registry(include_mock=os.getenv("REA_INCLUDE_MOCK") == "1")
    return {"ok": True, "providers": registry.names()}


@app.post("/v1/fetch-html")
async def fetch_html(
    body: FetchRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    if not _auth_ok(authorization):
        raise HTTPException(status_code=401, detail="unauthorized")
    _assert_url_allowed(body.url)

    include_mock = os.getenv("REA_INCLUDE_MOCK") == "1"
    registry = build_default_registry(include_mock=include_mock)
    context = {
        **body.context,
        "timeoutMs": body.timeoutMs,
        "sessionPolicy": body.sessionPolicy,
        "render": body.render,
        "target": body.target,
    }
    result = await registry.fetch(
        body.url,
        kind=body.kind,
        provider=body.provider,
        context=context,
        failover=body.failover,
    )
    classification = classify_html(result.html)
    include_html = "html" in body.return_fields
    payload: dict[str, Any] = {
        "ok": not result.blocked and not result.error and classification["hasArgonaut"],
        "provider": result.provider,
        "engine": result.engine,
        "statusCode": result.status_code,
        "finalUrl": result.final_url,
        "bytes": classification["bytes"],
        "hasArgonaut": classification["hasArgonaut"],
        "hasKpsdkShell": classification["tinyKasadaShell"] or classification["hasKpsdk"],
        "blocked": result.blocked or classification["blocked"],
        "error": result.error,
    }
    if include_html:
        payload["html"] = result.html
    if "diagnostics" in body.return_fields:
        payload["diagnostics"] = {
            **(result.diagnostics or {}),
            "classification": classification,
        }
    # Fail closed: never report success for KPSDK shells.
    if classification["tinyKasadaShell"] or (
        classification["hasKpsdk"] and not classification["hasArgonaut"]
    ):
        payload["ok"] = False
        payload["blocked"] = True
        if not payload.get("error"):
            payload["error"] = "kasada shell / missing ArgonautExchange"
    return payload


def main() -> None:
    import uvicorn

    uvicorn.run(
        "rea_unblocker.gateway.app:app",
        host=os.getenv("REA_GATEWAY_HOST", "0.0.0.0"),
        port=int(os.getenv("REA_GATEWAY_PORT", "8080")),
        reload=False,
    )


if __name__ == "__main__":
    main()
