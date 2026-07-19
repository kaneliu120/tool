"""Frozen ArgonautExchange parser — acquisition layer must feed this, not rewrite it."""

from __future__ import annotations

import json
import re
from typing import Any


# Greedy match mirrors ScrapFly's proven REA extractor.
ARGONAUT_RE = re.compile(r"window\.ArgonautExchange\s*=\s*(\{.+\})\s*;", re.DOTALL)


class ArgonautParseError(ValueError):
    pass


def extract_argonaut(html: str) -> dict[str, Any]:
    if "window.ArgonautExchange" not in html:
        raise ArgonautParseError("ArgonautExchange not found")
    match = ARGONAUT_RE.search(html)
    if not match:
        raise ArgonautParseError("ArgonautExchange regex failed")
    root = json.loads(match.group(1))
    app = root.get("resi-property_listing-experience-web")
    if not app or "urqlClientCache" not in app:
        raise ArgonautParseError("urqlClientCache missing")
    cache = json.loads(app["urqlClientCache"])
    if not cache:
        raise ArgonautParseError("empty urqlClientCache")
    first = next(iter(cache.values()))
    data = first.get("data")
    if isinstance(data, str):
        data = json.loads(data)
    if not isinstance(data, dict):
        raise ArgonautParseError("cache data is not an object")
    return data


def _iter_listing_nodes(data: dict[str, Any]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for key in ("buySearch", "rentSearch"):
        search = data.get(key) or {}
        results = search.get("results") or search.get("exact") or {}
        items = results.get("items") or results.get("listings") or []
        for item in items:
            listing = item.get("listing") if isinstance(item, dict) else None
            if isinstance(listing, dict):
                nodes.append(listing)
            elif isinstance(item, dict) and item.get("id"):
                nodes.append(item)
    details = data.get("details") or {}
    listing = details.get("listing") if isinstance(details, dict) else None
    if isinstance(listing, dict):
        nodes.append(listing)
    return nodes


def normalize_listing(listing: dict[str, Any], *, listing_type: str | None = None) -> dict[str, Any]:
    address = listing.get("address") or {}
    price = listing.get("price") or {}
    return {
        "listingId": listing.get("id") or listing.get("listingId"),
        "url": listing.get("url")
        or listing.get("listingUrl")
        or listing.get("_links", {}).get("canonical", {}).get("href"),
        "address": address.get("display", {}).get("shortAddress")
        or address.get("display", {}).get("fullAddress")
        or address.get("suburb"),
        "price": price.get("display") or price.get("value") or listing.get("priceText"),
        "listingType": listing_type
        or listing.get("listingType")
        or listing.get("channel")
        or "unknown",
        "raw": {
            "id": listing.get("id"),
            "status": listing.get("status"),
        },
    }


def parse_listings_from_html(html: str, *, kind: str | None = None) -> list[dict[str, Any]]:
    data = extract_argonaut(html)
    listing_type = None
    if kind and "rent" in kind:
        listing_type = "rent"
    elif kind and "sale" in kind:
        listing_type = "sale"
    rows = [normalize_listing(n, listing_type=listing_type) for n in _iter_listing_nodes(data)]
    return [r for r in rows if r.get("listingId")]
