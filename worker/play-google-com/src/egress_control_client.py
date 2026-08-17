"""egress-control runtime-config client (factory). Admin key must never live here."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

APPLY_KEYS = (
    "PROXY_URL",
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "SCRAPE_PROVIDER",
    "BRIGHTDATA_UNLOCKER_ZONE",
    "BRIGHTDATA_UNLOCKER_PASSWORD",
    "CAPSOLVER_API_KEY",
)


def apply_runtime_env(worker_name: str) -> dict[str, Any]:
    base = (os.getenv("EGRESS_CONTROL_BASE_URL") or "").strip().rstrip("/")
    key = (os.getenv("EGRESS_CONTROL_API_KEY") or "").strip()
    wid = (os.getenv("EGRESS_CONTROL_WORKER_ID") or worker_name).strip()
    if not base or not key:
        return {"source": "env_fallback", "workerId": wid, "applied": []}
    url = f"{base}/v1/workers/{wid}/runtime-config"
    try:
        import httpx

        headers = {
            "X-Api-Key": key,
            "Authorization": f"Bearer {key}",
            "User-Agent": "play-google-com-worker/1.0",
        }
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
        if resp.status_code != 200:
            logger.warning("egress-control runtime-config HTTP %s", resp.status_code)
            return {
                "source": "env_fallback",
                "workerId": wid,
                "applied": [],
                "httpStatus": resp.status_code,
            }
        data = resp.json() if resp.content else {}
    except Exception as exc:
        logger.warning("egress-control fetch failed: %s", exc)
        return {"source": "env_fallback", "workerId": wid, "applied": []}

    env_map: dict[str, Any] = {}
    if isinstance(data, dict):
        if isinstance(data.get("env"), dict):
            env_map.update(data["env"])
        proxy = data.get("proxyUrl") or data.get("proxy_url")
        if not proxy and isinstance(data.get("proxy"), dict):
            proxy = data["proxy"].get("url") or data["proxy"].get("proxyUrl")
        if proxy:
            env_map.setdefault("PROXY_URL", proxy)
        version = data.get("version")
    else:
        version = None

    applied: list[str] = []
    for name in APPLY_KEYS:
        val = env_map.get(name)
        if val is None or str(val).strip() == "":
            continue
        os.environ[name] = str(val)
        applied.append(name)
    logger.info(
        "egress-control ready worker=%s version=%s keys=%s",
        wid,
        version,
        ",".join(applied),
    )
    return {
        "source": "control_plane",
        "workerId": wid,
        "version": version,
        "applied": applied,
    }
