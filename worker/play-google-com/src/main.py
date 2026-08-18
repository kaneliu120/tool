"""FastAPI Cloud Run entry: OpenAPI + health public; scrape routes authenticated."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from src import SCHEMA_VERSION, WORKER_NAME
from src.auth import require_api_key
from src.collector import run_listings, run_search
from src import egress_control_client
from src.markets import categories_payload
from src.models import ListingsRequest, SearchRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = ROOT / "openapi" / "openapi.yaml"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    status = egress_control_client.apply_runtime_env(WORKER_NAME)
    logger.info("startup egress source=%s worker=%s", status.get("source"), status.get("workerId"))
    yield


app = FastAPI(
    title="play-google-com",
    version=SCHEMA_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)


def _load_openapi() -> dict:
    return yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "worker": WORKER_NAME,
        "schemaVersion": SCHEMA_VERSION,
        "kService": os.getenv("K_SERVICE") or "",
    }


@app.get("/openapi.json")
def openapi_json() -> JSONResponse:
    return JSONResponse(_load_openapi())


@app.get("/openapi.yaml")
def openapi_yaml() -> PlainTextResponse:
    return PlainTextResponse(
        OPENAPI_PATH.read_text(encoding="utf-8"),
        media_type="application/yaml",
    )


@app.get("/docs")
def docs() -> HTMLResponse:
    html = """<!DOCTYPE html>
<html><head><title>play-google-com docs</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head><body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
window.ui = SwaggerUIBundle({ url: '/openapi.json', dom_id: '#swagger-ui' });
</script>
</body></html>
"""
    return HTMLResponse(html)


@app.get("/v1/categories")
def categories(_: None = Depends(require_api_key)) -> dict:
    items = categories_payload()
    return {
        "status": "ok",
        "items": items,
        "diagnostics": {"count": len(items)},
        "provider": "static",
        "warnings": [],
        "worker": WORKER_NAME,
        "schemaVersion": SCHEMA_VERSION,
    }


@app.post("/v1/search")
def search(body: SearchRequest, _: None = Depends(require_api_key)) -> dict:
    return run_search(body)


@app.post("/v1/listings")
def listings(body: ListingsRequest, _: None = Depends(require_api_key)) -> dict:
    return run_listings(body)


def main() -> None:
    import uvicorn

    egress_control_client.apply_runtime_env(WORKER_NAME)
    port = int(os.getenv("PORT") or "8080")
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
