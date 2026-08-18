"""Standby Live View: OpenAPI + health. Scrape still goes to the worker."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from aiohttp import web

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]


def _openapi() -> dict:
    path = ROOT / ".actor" / "openapi.json"
    return json.loads(path.read_text(encoding="utf-8"))


async def handle_health(_request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "actor": "google-play-scraper"})


async def handle_openapi(_request: web.Request) -> web.Response:
    return web.json_response(_openapi())


async def handle_root(request: web.Request) -> web.Response:
    if request.method == "GET":
        return await handle_health(request)
    return web.json_response(
        {
            "status": "ok",
            "message": "Standby façade. Start a normal Actor run to scrape via the Cloud Run worker.",
        }
    )


async def serve() -> None:
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_post("/", handle_root)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/openapi.json", handle_openapi)
    port = int(
        os.getenv("ACTOR_WEB_SERVER_PORT")
        or os.getenv("APIFY_CONTAINER_PORT")
        or os.getenv("PORT")
        or "4321"
    )
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("standby listening on %s", port)
    import asyncio

    await asyncio.Event().wait()
