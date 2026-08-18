"""Scrape-route auth: Bearer and/or X-Api-Key. Constant-time compare."""

from __future__ import annotations

import hmac
import os

from fastapi import HTTPException, Request


def configured_keys() -> list[str]:
    raw = os.getenv("WORKER_API_KEY") or ""
    return [part.strip() for part in raw.split(",") if part.strip()]


def _matches(provided: str, expected: str) -> bool:
    if not provided or not expected:
        return False
    if len(provided) != len(expected):
        hmac.compare_digest(provided.encode("utf-8")[:32], expected.encode("utf-8")[:32])
        return False
    return hmac.compare_digest(provided, expected)


def require_api_key(request: Request) -> None:
    keys = configured_keys()
    if not keys:
        raise HTTPException(status_code=503, detail="WORKER_API_KEY not configured")
    candidates: list[str] = []
    auth = (request.headers.get("authorization") or "").strip()
    if auth.lower().startswith("bearer "):
        candidates.append(auth.split(" ", 1)[1].strip())
    xkey = (request.headers.get("x-api-key") or "").strip()
    if xkey:
        candidates.append(xkey)
    for cand in candidates:
        for key in keys:
            if _matches(cand, key):
                return
    raise HTTPException(status_code=401, detail="unauthorized")
