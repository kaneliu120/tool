"""Minimal runner HTTP server: POST /v1/fetch (deploy on Mac/Windows host)."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from rea_unblocker.classifier.html import classify_html
from rea_unblocker.runner.mac_chrome import MacChromeRunner

app = FastAPI(title="REA Chrome Runner", version="0.1.0")


class RunnerFetchRequest(BaseModel):
    url: str
    kind: str = "sale_search"
    profilePolicy: str | None = None
    proxy: dict[str, Any] = Field(default_factory=dict)
    timeoutMs: int = 90_000
    return_fields: list[str] = Field(default_factory=lambda: ["html", "diagnostics"], alias="return")

    model_config = {"populate_by_name": True}


def _auth_ok(authorization: str | None) -> bool:
    expected = os.getenv("REA_RUNNER_TOKEN") or os.getenv("REA_MAC_RUNNER_TOKEN")
    if not expected:
        return True
    if not authorization or not authorization.startswith("Bearer "):
        return False
    return authorization.removeprefix("Bearer ").strip() == expected


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"ok": "true", "engine": "mac-chrome-patchright"}


@app.post("/v1/fetch")
async def fetch(
    body: RunnerFetchRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    if not _auth_ok(authorization):
        raise HTTPException(status_code=401, detail="unauthorized")
    runner = MacChromeRunner(proxy=body.proxy)
    result = await runner.fetch(
        body.url,
        kind=body.kind,
        context={"timeoutMs": body.timeoutMs, "proxy": body.proxy, "warmup": True},
    )
    classification = classify_html(result.html)
    payload: dict[str, Any] = {
        "ok": not result.blocked and classification["hasArgonaut"],
        "provider": result.provider,
        "engine": result.engine,
        "statusCode": result.status_code,
        "finalUrl": result.final_url,
        "bytes": classification["bytes"],
        "hasArgonaut": classification["hasArgonaut"],
        "hasKpsdkShell": classification["tinyKasadaShell"],
        "blocked": result.blocked or classification["blocked"],
        "error": result.error,
        "html": result.html if "html" in body.return_fields else None,
        "diagnostics": {
            **(result.diagnostics or {}),
            "classification": classification,
            "profilePolicy": body.profilePolicy,
        },
    }
    return payload


def main() -> None:
    import uvicorn

    uvicorn.run(
        "rea_unblocker.runner.server:app",
        host=os.getenv("REA_RUNNER_HOST", "0.0.0.0"),
        port=int(os.getenv("REA_RUNNER_PORT", "8090")),
    )


if __name__ == "__main__":
    main()
