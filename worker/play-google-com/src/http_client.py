"""HTTP fetch with curl_cffi Chrome impersonation (recon floor)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.proxy_provider import http_proxies

logger = logging.getLogger(__name__)

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
)
IMPERSONATE_CANDIDATES = ("chrome136", "chrome131", "chrome124")


@dataclass
class FetchResult:
    url: str
    status_code: int
    text: str
    nbytes: int
    provider: str
    error: str | None = None


def _headers() -> dict[str, str]:
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": CHROME_UA,
    }


def fetch_html(url: str, *, timeout: float = 60.0) -> FetchResult:
    proxies = http_proxies()
    last_err: str | None = None
    try:
        from curl_cffi import requests as cf

        impersonate = None
        session = None
        for cand in IMPERSONATE_CANDIDATES:
            try:
                session = cf.Session(impersonate=cand)
                impersonate = cand
                break
            except Exception as exc:
                last_err = str(exc)
                session = None
        if session is None:
            raise RuntimeError(last_err or "curl_cffi impersonate failed")
        kw: dict[str, Any] = {
            "headers": _headers(),
            "timeout": timeout,
            "allow_redirects": True,
        }
        if proxies:
            kw["proxies"] = proxies
        resp = session.get(url, **kw)
        text = resp.text or ""
        return FetchResult(
            url=str(resp.url or url),
            status_code=int(resp.status_code),
            text=text,
            nbytes=len(text.encode("utf-8", errors="replace")),
            provider=f"curl_cffi:{impersonate}",
        )
    except Exception as exc:
        last_err = str(exc)
        logger.warning("curl_cffi fetch failed; falling back to httpx: %s", exc)

    try:
        import httpx

        proxy_url = (proxies or {}).get("https") if proxies else None
        kwargs: dict[str, Any] = {
            "timeout": timeout,
            "follow_redirects": True,
            "headers": _headers(),
        }
        try:
            client_cm = httpx.Client(**kwargs, proxy=proxy_url)
        except TypeError:
            client_cm = httpx.Client(**kwargs, proxies=proxies)
        with client_cm as client:
            resp = client.get(url)
        text = resp.text or ""
        return FetchResult(
            url=str(resp.url or url),
            status_code=int(resp.status_code),
            text=text,
            nbytes=len(text.encode("utf-8", errors="replace")),
            provider="httpx",
            error=last_err,
        )
    except Exception as exc:
        return FetchResult(
            url=url,
            status_code=0,
            text="",
            nbytes=0,
            provider="failed",
            error=str(exc),
        )
