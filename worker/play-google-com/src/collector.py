"""Site scrape orchestration. HTML first-pack only — no batchexecute forge."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

from src import PLAY_ORIGIN, SCHEMA_VERSION, WORKER_NAME
from src import egress_control_client
from src.http_client import fetch_html
from src.markets import catalog_status, category_status, resolve_market
from src.models import ListingsRequest, SearchRequest
from src.parse import (
    details_url,
    extract_package_ids,
    is_negative_page,
    is_ready_detail,
    is_ready_list,
    package_from_url,
    parse_datasafety,
    parse_detail,
    parse_search_cards,
)
from src.proxy_provider import proxy_diagnostics

logger = logging.getLogger(__name__)

MAX_ENRICH = 20


def _envelope(
    *,
    status: str,
    items: list[dict[str, Any]],
    diagnostics: dict[str, Any],
    provider: str,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "status": status,
        "items": items,
        "diagnostics": diagnostics,
        "provider": provider,
        "warnings": warnings,
        "worker": WORKER_NAME,
        "schemaVersion": SCHEMA_VERSION,
    }


def _project(items: list[dict[str, Any]], fields: list[str] | None) -> list[dict[str, Any]]:
    if not fields:
        return items
    keep = set(fields) | {"listingId", "name", "type", "status", "country", "authority"}
    return [{k: row.get(k) for k in keep if k in row} for row in items]


def _ids_from_request(package_ids: list[str], detail_urls: list[str]) -> list[str]:
    out: list[str] = []
    for raw in list(package_ids) + list(detail_urls):
        pkg = package_from_url(raw)
        if pkg and pkg not in out:
            out.append(pkg)
    return out


def _play_url(path: str, params: dict[str, str]) -> str:
    q = urlencode({k: v for k, v in params.items() if v})
    return f"{PLAY_ORIGIN}{path}?{q}" if q else f"{PLAY_ORIGIN}{path}"


def run_search(req: SearchRequest) -> dict[str, Any]:
    egress_control_client.apply_runtime_env(WORKER_NAME)
    market = resolve_market(req.market, req.hl, req.gl)
    hl, gl = market["hl"], market["gl"]
    warnings: list[str] = []
    if market["status"] == "未验证":
        warnings.append(f"market {market['market']} ({hl}/{gl}) 未验证")
    if req.includeReviews:
        warnings.append("review bodies are not collected (overlay batchexecute not forged)")

    ids = _ids_from_request(req.packageIds, req.detailUrls)
    if req.mode in {"detail", "datasafety"} or ids:
        listing_req = ListingsRequest(
            packageIds=ids,
            hl=hl,
            gl=gl,
            market=req.market,
            maxResults=req.maxResults,
            includeDataSafety=req.includeDataSafety or req.mode == "datasafety",
            includeReviews=req.includeReviews,
            fields=req.fields,
        )
        if req.mode == "datasafety":
            listing_req.includeDataSafety = True
        return run_listings(listing_req, channel=req.mode if req.mode in {"detail", "datasafety"} else "detail")

    cat = catalog_status(req.c)
    if cat == "closed":
        return _envelope(
            status="failed",
            items=[],
            diagnostics={"reason": f"search catalog c={req.c} HTTP 404 this session", **proxy_diagnostics()},
            provider="curl",
            warnings=warnings + [f"c={req.c} is not an opened Play catalog (c=apps is)"],
        )

    if req.mode == "category":
        code = (req.category or "").strip().upper()
        if not code:
            return _envelope(
                status="failed",
                items=[],
                diagnostics={"reason": "category mode requires category CODE", **proxy_diagnostics()},
                provider="curl",
                warnings=warnings,
            )
        st = category_status(code)
        if st == "未验证":
            warnings.append(f"category {code} 未验证")
        url = _play_url(f"/store/apps/category/{code}", {"hl": hl, "gl": gl})
        channel = "category"
    elif req.mode == "home":
        url = _play_url("/store/apps", {"hl": hl, "gl": gl, "pli": "1"})
        channel = "home"
    elif req.mode == "developer":
        dev = (req.developerId or "").strip()
        if not dev.isdigit():
            return _envelope(
                status="failed",
                items=[],
                diagnostics={"reason": "developer mode requires numeric developerId", **proxy_diagnostics()},
                provider="curl",
                warnings=warnings,
            )
        url = _play_url("/store/apps/dev", {"id": dev, "hl": hl, "gl": gl})
        channel = "developer"
    else:
        q = (req.q or "").strip()
        if not q:
            return _envelope(
                status="failed",
                items=[],
                diagnostics={"reason": "search mode requires q", **proxy_diagnostics()},
                provider="curl",
                warnings=warnings,
            )
        url = _play_url("/store/search", {"q": q, "c": req.c or "apps", "hl": hl, "gl": gl})
        channel = "search"

    fetched = fetch_html(url)
    diagnostics: dict[str, Any] = {
        "url": fetched.url,
        "httpStatus": fetched.status_code,
        "nbytes": fetched.nbytes,
        "market": market,
        "channel": channel,
        "afInit": "AF_initDataCallback" in fetched.text,
        "packageIdCount": len(extract_package_ids(fetched.text)),
        **proxy_diagnostics(),
    }
    if fetched.error:
        diagnostics["fetchError"] = fetched.error
    provider = "curl" if fetched.provider.startswith("curl") else fetched.provider.split(":")[0]

    if fetched.status_code == 0 or is_negative_page(fetched.text, status_code=fetched.status_code):
        return _envelope(
            status="blocked" if fetched.status_code in {0, 403, 429} else "failed",
            items=[],
            diagnostics=diagnostics,
            provider=provider,
            warnings=warnings + ["negative or empty Play HTML"],
        )
    if not is_ready_list(fetched.text):
        return _envelope(
            status="failed",
            items=[],
            diagnostics=diagnostics,
            provider=provider,
            warnings=warnings + ["ready signal missing: no details?id= + AF_initDataCallback"],
        )

    items = parse_search_cards(fetched.text, channel=channel, hl=hl, gl=gl)[: req.maxResults]
    if req.enrichDetails:
        items = _enrich_details(items, hl=hl, gl=gl, include_safety=req.includeDataSafety)
    elif req.includeDataSafety:
        warnings.append("includeDataSafety on list mode requires enrichDetails=true or /v1/listings")

    status = "ok" if items else "failed"
    return _envelope(
        status=status,
        items=_project(items, req.fields),
        diagnostics=diagnostics,
        provider=provider,
        warnings=warnings,
    )


def _enrich_details(
    items: list[dict[str, Any]],
    *,
    hl: str,
    gl: str,
    include_safety: bool,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in items[:MAX_ENRICH]:
        pkg = row.get("packageId") or row.get("listingId")
        if not pkg:
            out.append(row)
            continue
        merged = dict(row)
        fetched = fetch_html(details_url(str(pkg), hl, gl))
        if is_ready_detail(fetched.text):
            detail = parse_detail(fetched.text, package_id=str(pkg), hl=hl, gl=gl)
            merged.update({k: v for k, v in detail.items() if v is not None})
            merged["channel"] = row.get("channel") or "detail"
        if include_safety:
            safety = fetch_html(
                f"{PLAY_ORIGIN}/store/apps/datasafety?id={pkg}&hl={hl}&gl={gl}"
            )
            merged["dataSafety"] = parse_datasafety(
                safety.text, package_id=str(pkg), hl=hl, gl=gl
            )
        out.append(merged)
    return out


def run_listings(req: ListingsRequest, *, channel: str = "detail") -> dict[str, Any]:
    egress_control_client.apply_runtime_env(WORKER_NAME)
    market = resolve_market(req.market, req.hl, req.gl)
    hl, gl = market["hl"], market["gl"]
    warnings: list[str] = []
    if market["status"] == "未验证":
        warnings.append(f"market {market['market']} ({hl}/{gl}) 未验证")
    if req.includeReviews:
        warnings.append("review bodies are not collected (overlay batchexecute not forged)")

    ids = _ids_from_request(req.packageIds, req.detailUrls)[: req.maxResults]
    if not ids:
        return _envelope(
            status="failed",
            items=[],
            diagnostics={
                "reason": "listings require live packageIds or detailUrls (do not invent ids)",
                **proxy_diagnostics(),
            },
            provider="curl",
            warnings=warnings,
        )

    items: list[dict[str, Any]] = []
    provider = "curl"
    last_diag: dict[str, Any] = {}
    for pkg in ids:
        if channel == "datasafety":
            url = f"{PLAY_ORIGIN}/store/apps/datasafety?id={pkg}&hl={hl}&gl={gl}"
            fetched = fetch_html(url)
            provider = "curl" if fetched.provider.startswith("curl") else fetched.provider.split(":")[0]
            last_diag = {
                "url": fetched.url,
                "httpStatus": fetched.status_code,
                "nbytes": fetched.nbytes,
            }
            if is_negative_page(fetched.text, status_code=fetched.status_code):
                warnings.append(f"datasafety negative for {pkg}")
                continue
            items.append(parse_datasafety(fetched.text, package_id=pkg, hl=hl, gl=gl))
            continue

        url = details_url(pkg, hl, gl)
        fetched = fetch_html(url)
        provider = "curl" if fetched.provider.startswith("curl") else fetched.provider.split(":")[0]
        last_diag = {
            "url": fetched.url,
            "httpStatus": fetched.status_code,
            "nbytes": fetched.nbytes,
            "jsonLd": "SoftwareApplication" in fetched.text,
        }
        if is_negative_page(fetched.text, status_code=fetched.status_code) or not is_ready_detail(fetched.text):
            warnings.append(f"detail not ready for {pkg}")
            continue
        row = parse_detail(fetched.text, package_id=pkg, hl=hl, gl=gl)
        row["channel"] = channel
        if req.includeDataSafety:
            safety = fetch_html(f"{PLAY_ORIGIN}/store/apps/datasafety?id={pkg}&hl={hl}&gl={gl}")
            row["dataSafety"] = parse_datasafety(safety.text, package_id=pkg, hl=hl, gl=gl)
        items.append(row)

    diagnostics = {
        "market": market,
        "channel": channel,
        "requested": ids,
        **last_diag,
        **proxy_diagnostics(),
    }
    status = "ok" if items else "failed"
    if items and len(items) < len(ids):
        status = "partial"
    return _envelope(
        status=status,
        items=_project(items, req.fields),
        diagnostics=diagnostics,
        provider=provider,
        warnings=warnings,
    )
