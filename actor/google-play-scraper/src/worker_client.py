"""HTTPS worker client. Never send auth to arbitrary URLs."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlparse

import httpx

from src.errors import AcquisitionError, NoRowsCollectedError

logger = logging.getLogger(__name__)

DEFAULT_WORKER_BASE_URL = "https://play-google-com-placeholder.run.app"
UrlSource = Literal["input", "env", "default"]
ALLOWED_HOSTS = {"localhost", "127.0.0.1", "::1"}
ALLOWED_SUFFIXES = (".run.app",)


@dataclass(frozen=True)
class WorkerEndpoint:
    base_url: str
    source: UrlSource


def _env_flag(name: str) -> bool:
    return str(os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def worker_provides_proxy() -> bool:
    return _env_flag("WORKER_PROVIDES_PROXY") or _env_flag("SKIP_APIFY_PROXY")


def worker_auth() -> str:
    return (os.getenv("WORKER_AUTH") or os.getenv("WORKER_API_KEY") or "").strip()


def _host_allowed(host: str) -> bool:
    h = (host or "").lower()
    if h in ALLOWED_HOSTS:
        return True
    return any(h.endswith(suf) for suf in ALLOWED_SUFFIXES)


def _validate_base_url(raw: str) -> str:
    root = raw.strip().rstrip("/")
    parsed = urlparse(root)
    host = (parsed.hostname or "").lower()
    local = host in ALLOWED_HOSTS
    if parsed.scheme != "https" and not local:
        raise AcquisitionError(f"WORKER_BASE_URL must use https:// (got {parsed.scheme})")
    if parsed.scheme not in {"http", "https"}:
        raise AcquisitionError("WORKER_BASE_URL scheme not allowed")
    if not _host_allowed(host):
        raise AcquisitionError(f"WORKER_BASE_URL host not allowlisted: {host}")
    return root


def resolve_worker_endpoint(override: str | None = None) -> WorkerEndpoint:
    if (override or "").strip():
        return WorkerEndpoint(_validate_base_url(override), "input")
    env_url = (os.getenv("WORKER_BASE_URL") or "").strip()
    if env_url:
        return WorkerEndpoint(_validate_base_url(env_url), "env")
    logger.warning("WORKER_BASE_URL unset; using built-in default")
    return WorkerEndpoint(_validate_base_url(DEFAULT_WORKER_BASE_URL), "default")


def _headers() -> dict[str, str]:
    key = worker_auth()
    if not key:
        raise AcquisitionError("WORKER_AUTH is not set")
    return {
        "Authorization": f"Bearer {key}",
        "X-Api-Key": key,
        "content-type": "application/json",
        "Accept": "application/json",
    }


def call_worker(
    endpoint: WorkerEndpoint,
    payload: dict[str, Any],
    *,
    path: str = "/v1/search",
    timeout: float = 800.0,
) -> dict[str, Any]:
    url = f"{endpoint.base_url}{path}"
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.post(url, json=payload, headers=_headers())
    except httpx.HTTPError as exc:
        raise AcquisitionError(f"worker request failed: {exc}") from exc
    if resp.status_code in {401, 403}:
        raise AcquisitionError(f"worker auth failed HTTP {resp.status_code}")
    if resp.status_code >= 400:
        raise AcquisitionError(f"worker HTTP {resp.status_code}: {resp.text[:300]}")
    try:
        data = resp.json()
    except ValueError as exc:
        raise AcquisitionError("worker body is not JSON") from exc
    if not isinstance(data, dict):
        raise AcquisitionError("worker envelope is not an object")
    items = data.get("items")
    if not isinstance(items, list):
        raise AcquisitionError("worker envelope items is not a list")
    if len(items) < 1:
        if data.get("status") == "empty":
            return data
        raise NoRowsCollectedError("worker returned 0 items")
    return data
