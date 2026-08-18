"""Proxy helpers. Ignore Actor-minted apify_actor_run URLs on Cloud Run."""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def _env_flag(name: str) -> bool:
    return str(os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def current_proxy_url() -> str:
    raw = (os.getenv("PROXY_URL") or os.getenv("HTTPS_PROXY") or "").strip()
    if not raw:
        return ""
    if "apify_actor_run" in raw:
        logger.info("ignoring apify_actor_run proxy on Cloud Run")
        return ""
    return raw


def http_proxies() -> dict[str, str] | None:
    url = current_proxy_url()
    if not url:
        return None
    return {"http": url, "https": url}


def proxy_diagnostics() -> dict[str, Any]:
    url = current_proxy_url()
    if not url:
        return {"proxySource": "none", "proxyHost": None}
    host = urlparse(url).hostname
    return {
        "proxySource": "worker-env",
        "proxyHost": host,
        "k8s": _env_flag("K_SERVICE"),
    }
