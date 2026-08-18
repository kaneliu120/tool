"""Parse Play Store first-pack HTML. Do not forge batchexecute or invent package ids."""

from __future__ import annotations

import json
import re
from html import unescape
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from src import PLAY_ORIGIN

FREE_PRICES = {"0", "0.0", "0.00"}

PACKAGE_RE = re.compile(
    r"/store/apps/details(?:/[^\"'?#]*)?\?id=([a-zA-Z0-9_.]+)",
    re.I,
)
DEV_RE = re.compile(r"/store/apps/dev\?id=(\d+)")
CATEGORY_RE = re.compile(r"/store/apps/category/([A-Z0-9_]+)")
CARD_RE = re.compile(
    r'<a class="Si6A0c[^"]*" href="(/store/apps/details\?id=[^"]+)"[^>]*>(.*?)</a>',
    re.S | re.I,
)
JSON_LD_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.S | re.I,
)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S | re.I)
RATED_RE = re.compile(r"Rated\s+([0-9]+(?:\.[0-9]+)?)\s+stars", re.I)
REVIEW_COUNT_RE = re.compile(
    r"([0-9]+(?:\.[0-9]+)?[KMB]?)\s+reviews",
    re.I,
)
DOWNLOADS_RE = re.compile(
    r'<div class="ClM7O">([^<]+)</div>\s*<div class="g1rdde">Downloads</div>',
    re.I | re.S,
)
UPDATED_RE = re.compile(
    r"Updated on</div>\s*<div class=\"xg1aie\">([^<]+)</div>",
    re.I,
)
THUMB_RE = re.compile(
    r'<img[^>]+class="[^"]*stzEZd[^"]*"[^>]+src="([^"]+)"',
    re.I,
)
ICON_RE = re.compile(
    r'<img[^>]+itemprop="image"[^>]+src="([^"]+)"',
    re.I,
)
NAME_SPAN_RE = re.compile(r'<span[^>]*class="[^"]*DdYX5[^"]*"[^>]*>([^<]+)</span>', re.I)
NAME_DIV_RE = re.compile(r'<div class="Epkrse[^"]*">([^<]+)</div>', re.I)
DEV_SPAN_RE = re.compile(r'<span[^>]*class="[^"]*wMUdtb[^"]*"[^>]*>([^<]+)</span>', re.I)
ICON_ALT_RE = re.compile(r'alt="Icon image ([^"]+)"', re.I)
CONTAINS_ADS_RE = re.compile(r"Contains ads", re.I)
IN_APP_RE = re.compile(r"In-app purchases|In-app products", re.I)
H2_RE = re.compile(r"<h2[^>]*class=\"q1rIdc\"[^>]*>([^<]+)</h2>", re.I)

NEGATIVE_TITLE_RE = re.compile(r"not found|unusual traffic|sorry", re.I)
DATA_TYPE_LABELS = (
    "Location",
    "Personal info",
    "Financial info",
    "Health and fitness",
    "Messages",
    "Photos and videos",
    "Audio files",
    "Files and docs",
    "Calendar",
    "Contacts",
    "App activity",
    "Web browsing",
    "App info and performance",
    "Device or other IDs",
)
SECURITY_LABELS = (
    "Data is encrypted in transit",
    "Data can’t be deleted",
    "Data can be deleted",
    "You can request that data be deleted",
    "Committed to follow the Play Families Policy",
    "Independent security review",
)


def _strip_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    return unescape(re.sub(r"\s+", " ", text)).strip()


def page_title(html: str) -> str:
    m = TITLE_RE.search(html or "")
    return _strip_tags(m.group(1)) if m else ""


def extract_package_ids(html: str) -> list[str]:
    seen: list[str] = []
    for pkg in PACKAGE_RE.findall(html or ""):
        if pkg not in seen:
            seen.append(pkg)
    return seen


def package_from_url(url: str) -> str | None:
    if not url:
        return None
    raw = url.strip()
    if re.fullmatch(r"[a-zA-Z0-9_.]+", raw) and "." in raw:
        return raw
    parsed = urlparse(raw)
    qs = parse_qs(parsed.query)
    if qs.get("id"):
        return qs["id"][0]
    m = PACKAGE_RE.search(raw)
    return m.group(1) if m else None


def details_url(package_id: str, hl: str, gl: str) -> str:
    return f"{PLAY_ORIGIN}/store/apps/details?id={package_id}&hl={hl}&gl={gl}"


def is_negative_page(html: str, *, status_code: int | None = None) -> bool:
    if status_code and status_code >= 400:
        return True
    body = html or ""
    title = page_title(body)
    if NEGATIVE_TITLE_RE.search(title):
        return True
    if "AF_initDataCallback" in body and not extract_package_ids(body):
        return False
    if len(body) < 4000 and not extract_package_ids(body) and "SoftwareApplication" not in body:
        if NEGATIVE_TITLE_RE.search(body) or len(body) < 800:
            return True
    return False


def is_ready_list(html: str) -> bool:
    return bool(extract_package_ids(html or "")) and "AF_initDataCallback" in (html or "")


def is_empty_list_page(html: str, *, status_code: int | None = None) -> bool:
    """HTTP 200 ESF shelf with no live details?id= cards (DATING / age-gated / locale shell)."""
    if status_code not in (None, 200):
        return False
    body = html or ""
    return "AF_initDataCallback" in body and not extract_package_ids(body)


def is_ready_detail(html: str) -> bool:
    body = html or ""
    if "SoftwareApplication" in body:
        return True
    if 'itemprop="name"' in body and extract_package_ids(body):
        return True
    return False


def _first_image(card_html: str) -> str | None:
    m = THUMB_RE.search(card_html)
    if m:
        return m.group(1)
    imgs = re.findall(r'<img[^>]+src="(https://play-lh\.googleusercontent\.com/[^"]+)"', card_html)
    for src in imgs:
        if "=s64" in src or "stzEZd" in card_html:
            return src
    return imgs[-1] if imgs else None


def parse_search_cards(html: str, *, channel: str, hl: str, gl: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for href, inner in CARD_RE.findall(html or ""):
        pkg = package_from_url(href)
        if not pkg or pkg in seen:
            continue
        seen.add(pkg)
        name_m = NAME_SPAN_RE.search(inner) or NAME_DIV_RE.search(inner)
        name = unescape(name_m.group(1)).strip() if name_m else ""
        if not name:
            alt_m = ICON_ALT_RE.search(inner)
            if alt_m:
                name = unescape(alt_m.group(1)).strip()
        if not name:
            texts = [unescape(t).strip() for t in re.findall(r">([^<]{2,80})<", inner)]
            skip = {"star", "•"}
            name = next((t for t in texts if t.lower() not in skip and not re.fullmatch(r"[0-9.]+", t)), pkg)
        dev_m = DEV_SPAN_RE.search(inner)
        rated = RATED_RE.search(inner)
        item: dict[str, Any] = {
            "listingId": pkg,
            "packageId": pkg,
            "name": name or pkg,
            "type": "app",
            "status": "listed",
            "country": gl,
            "authority": "play.google.com",
            "listingType": channel,
            "channel": channel,
            "listingUrl": details_url(pkg, hl, gl),
            "imageUrl": _first_image(inner),
            "developer": unescape(dev_m.group(1)).strip() if dev_m else None,
            "ratingValue": float(rated.group(1)) if rated else None,
        }
        items.append(item)
    if items:
        return items
    # Fallback: live anchors only (no invented ids)
    for pkg in extract_package_ids(html or ""):
        items.append(
            {
                "listingId": pkg,
                "packageId": pkg,
                "name": pkg,
                "type": "app",
                "status": "listed",
                "country": gl,
                "authority": "play.google.com",
                "listingType": channel,
                "channel": channel,
                "listingUrl": details_url(pkg, hl, gl),
                "imageUrl": None,
                "developer": None,
                "ratingValue": None,
            }
        )
    return items


def _json_ld_blocks(html: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in JSON_LD_RE.findall(html or ""):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            out.append(data)
        elif isinstance(data, list):
            out.extend(x for x in data if isinstance(x, dict))
    return out


def parse_json_ld(html: str) -> dict[str, Any] | None:
    for block in _json_ld_blocks(html):
        types = block.get("@type")
        type_l = types if isinstance(types, list) else [types]
        if any(str(t) == "SoftwareApplication" for t in type_l):
            return block
    return None


def screenshot_urls(ld: dict[str, Any] | None) -> list[str]:
    raw = (ld or {}).get("screenshot") or (ld or {}).get("screenshots")
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()][:8]
    return []


def offer_price_fields(offer: dict[str, Any] | None) -> dict[str, Any]:
    offer = offer or {}
    raw = offer.get("price")
    price = str(raw) if raw is not None else None
    currency = offer.get("priceCurrency")
    is_paid = bool(price) and price not in FREE_PRICES
    if price is None:
        display = None
    elif not is_paid:
        display = "Free"
    elif currency:
        display = f"{currency} {price}"
    else:
        display = price
    return {
        "price": price,
        "priceCurrency": currency,
        "priceDisplay": display,
        "isPaid": is_paid,
        "availability": offer.get("availability"),
    }


def parse_detail(html: str, *, package_id: str, hl: str, gl: str) -> dict[str, Any]:
    ld = parse_json_ld(html) or {}
    author = ld.get("author") if isinstance(ld.get("author"), dict) else {}
    agg = ld.get("aggregateRating") if isinstance(ld.get("aggregateRating"), dict) else {}
    offers = ld.get("offers")
    offer = offers[0] if isinstance(offers, list) and offers else (offers if isinstance(offers, dict) else {})
    h1 = H1_RE.search(html or "")
    name = (ld.get("name") or (_strip_tags(h1.group(1)) if h1 else "") or package_id).strip()
    dev_m = DEV_RE.search(html or "")
    dev_id = dev_m.group(1) if dev_m else None
    dev_name = None
    if dev_m:
        around = (html or "")[max(0, dev_m.start()) : dev_m.end() + 80]
        span = re.search(r"<span>([^<]+)</span>", around)
        if span:
            dev_name = unescape(span.group(1)).strip()
    if not dev_name:
        dev_name = author.get("name")
    downloads_m = DOWNLOADS_RE.search(html or "")
    updated_m = UPDATED_RE.search(html or "")
    rated = RATED_RE.search(html or "")
    reviews_m = REVIEW_COUNT_RE.search(html or "")
    icon = None
    icon_m = ICON_RE.search(html or "")
    if icon_m:
        icon = icon_m.group(1)
    elif isinstance(ld.get("image"), str):
        icon = ld.get("image")
    price_fields = offer_price_fields(offer if isinstance(offer, dict) else {})
    rating_value = None
    if agg.get("ratingValue") is not None:
        try:
            rating_value = float(agg["ratingValue"])
        except (TypeError, ValueError):
            rating_value = None
    elif rated:
        rating_value = float(rated.group(1))
    rating_count = None
    if agg.get("ratingCount") is not None:
        try:
            rating_count = int(float(str(agg["ratingCount"])))
        except (TypeError, ValueError):
            rating_count = None
    cats = CATEGORY_RE.findall(html or "")
    app_cat = ld.get("applicationCategory") or (cats[-1] if cats else None)
    item: dict[str, Any] = {
        "listingId": package_id,
        "packageId": package_id,
        "name": name,
        "type": "app",
        "status": "listed",
        "country": gl,
        "authority": "play.google.com",
        "listingType": "detail",
        "channel": "detail",
        "listingUrl": details_url(package_id, hl, gl),
        "imageUrl": icon,
        "developer": dev_name,
        "developerId": dev_id,
        "developerUrl": f"{PLAY_ORIGIN}/store/apps/dev?id={dev_id}" if dev_id else author.get("url"),
        "ratingValue": rating_value,
        "ratingCount": rating_count,
        "ratingCountDisplay": reviews_m.group(0) if reviews_m else None,
        **price_fields,
        "contentRating": ld.get("contentRating") or None,
        "applicationCategory": app_cat,
        "operatingSystem": ld.get("operatingSystem"),
        "installs": unescape(downloads_m.group(1)).strip() if downloads_m else None,
        "updatedOn": unescape(updated_m.group(1)).strip() if updated_m else None,
        "containsAds": bool(CONTAINS_ADS_RE.search(html or "")),
        "inAppPurchases": bool(IN_APP_RE.search(html or "")),
        "screenshots": screenshot_urls(ld) or None,
        "description": ld.get("description"),
        "dataSafetyUrl": f"{PLAY_ORIGIN}/store/apps/datasafety?id={package_id}&hl={hl}&gl={gl}",
        "jsonLd": True if ld else False,
    }
    cr_span = re.search(r'itemprop="contentRating"[^>]*>\s*<span>([^<]+)</span>', html or "", re.I)
    if cr_span and not item["contentRating"]:
        item["contentRating"] = unescape(cr_span.group(1)).strip()
    return item


def parse_datasafety(html: str, *, package_id: str, hl: str, gl: str) -> dict[str, Any]:
    headings = [unescape(x).strip() for x in H2_RE.findall(html or "")]
    sharing = None
    collected_declared = False
    for h in headings:
        low = h.lower()
        if "no data shared" in low or "doesn't share" in low or "doesn’t share" in low:
            sharing = "none"
        elif "data shared" in low:
            sharing = "shared"
        if "data collected" in low:
            collected_declared = True
    types = [label for label in DATA_TYPE_LABELS if label in (html or "")]
    security = [label for label in SECURITY_LABELS if label in (html or "")]
    h1 = H1_RE.search(html or "")
    ready = bool(h1 and "data safety" in _strip_tags(h1.group(1)).lower())
    return {
        "listingId": f"{package_id}#datasafety",
        "packageId": package_id,
        "name": _strip_tags(h1.group(1)) if h1 else "Data safety",
        "type": "datasafety",
        "status": "listed" if ready else "partial",
        "country": gl,
        "authority": "play.google.com",
        "listingType": "datasafety",
        "channel": "datasafety",
        "listingUrl": f"{PLAY_ORIGIN}/store/apps/datasafety?id={package_id}&hl={hl}&gl={gl}",
        "dataSharedWithThirdParties": sharing,
        "dataCollectedDeclared": collected_declared,
        "dataTypes": types,
        "securityPractices": security,
        "headings": headings[:12],
    }


def absolute_play_url(path: str) -> str:
    return urljoin(PLAY_ORIGIN + "/", path.lstrip("/"))
