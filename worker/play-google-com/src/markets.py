"""Play markets, catalogs, and category codes from the recon contract.

Opened cells are session-measured (report 2026-08-17 + Cloud Agent HTTP 2026-08-18).
Unlisted gl/hl values are accepted as ISO/BCP-47 but stay 未验证.
"""

from __future__ import annotations

from typing import Any

# Site geography for Cloud Run: Play is global on play.google.com; US is the
# primary opened market and Google HQ. Region = us-central1.

# (preset, hl, gl) — home + search c=apps + GAME first-pack opened 2026-08-18.
# UZ uses hl=en (hl=uz home was an empty ESF shell).
_OPENED_MARKETS: tuple[tuple[str, str, str], ...] = (
    ("us", "en", "US"),
    ("ph", "zh-CN", "PH"),
    ("gb", "en", "GB"),
    ("au", "en", "AU"),
    ("jp", "ja", "JP"),
    ("tw", "zh-TW", "TW"),
    ("de", "de", "DE"),
    ("fr", "fr", "FR"),
    ("in", "en", "IN"),
    ("br", "pt", "BR"),
    ("ca", "en", "CA"),
    ("sg", "en", "SG"),
    ("ae", "ar", "AE"),
    ("ag", "en", "AG"),
    ("ai", "en", "AI"),
    ("al", "en", "AL"),
    ("am", "en", "AM"),
    ("ao", "en", "AO"),
    ("ar", "es", "AR"),
    ("at", "de", "AT"),
    ("az", "az", "AZ"),
    ("ba", "en", "BA"),
    ("bb", "en", "BB"),
    ("bd", "en", "BD"),
    ("be", "fr", "BE"),
    ("bf", "en", "BF"),
    ("bg", "bg", "BG"),
    ("bh", "ar", "BH"),
    ("bj", "en", "BJ"),
    ("bm", "en", "BM"),
    ("bn", "en", "BN"),
    ("bo", "es", "BO"),
    ("bs", "en", "BS"),
    ("bt", "en", "BT"),
    ("bw", "en", "BW"),
    ("by", "en", "BY"),
    ("bz", "en", "BZ"),
    ("cd", "en", "CD"),
    ("cf", "en", "CF"),
    ("cg", "en", "CG"),
    ("ch", "de", "CH"),
    ("ci", "en", "CI"),
    ("cl", "es", "CL"),
    ("cm", "en", "CM"),
    ("co", "es", "CO"),
    ("cr", "es", "CR"),
    ("cv", "en", "CV"),
    ("cy", "en", "CY"),
    ("cz", "cs", "CZ"),
    ("dk", "da", "DK"),
    ("dm", "en", "DM"),
    ("do", "es", "DO"),
    ("dz", "ar", "DZ"),
    ("ec", "es", "EC"),
    ("ee", "et", "EE"),
    ("eg", "ar", "EG"),
    ("es", "es", "ES"),
    ("et", "en", "ET"),
    ("fi", "fi", "FI"),
    ("fj", "en", "FJ"),
    ("fm", "en", "FM"),
    ("ga", "en", "GA"),
    ("gd", "en", "GD"),
    ("ge", "ka", "GE"),
    ("gh", "en", "GH"),
    ("gm", "en", "GM"),
    ("gn", "en", "GN"),
    ("gq", "en", "GQ"),
    ("gr", "el", "GR"),
    ("gt", "es", "GT"),
    ("gw", "en", "GW"),
    ("gy", "en", "GY"),
    ("hk", "zh-HK", "HK"),
    ("hn", "es", "HN"),
    ("hr", "hr", "HR"),
    ("ht", "en", "HT"),
    ("hu", "hu", "HU"),
    ("id", "id", "ID"),
    ("ie", "en", "IE"),
    ("il", "he", "IL"),
    ("iq", "ar", "IQ"),
    ("is", "is", "IS"),
    ("it", "it", "IT"),
    ("jm", "en", "JM"),
    ("jo", "en", "JO"),
    ("ke", "en", "KE"),
    ("kg", "en", "KG"),
    ("kh", "km", "KH"),
    ("km", "en", "KM"),
    ("kn", "en", "KN"),
    ("kr", "ko", "KR"),
    ("kw", "ar", "KW"),
    ("ky", "en", "KY"),
    ("kz", "kk", "KZ"),
    ("la", "lo", "LA"),
    ("lb", "ar", "LB"),
    ("lc", "en", "LC"),
    ("li", "en", "LI"),
    ("lk", "si", "LK"),
    ("lr", "en", "LR"),
    ("ls", "en", "LS"),
    ("lt", "lt", "LT"),
    ("lu", "fr", "LU"),
    ("lv", "lv", "LV"),
    ("ly", "en", "LY"),
    ("ma", "ar", "MA"),
    ("md", "en", "MD"),
    ("me", "en", "ME"),
    ("mg", "en", "MG"),
    ("mk", "en", "MK"),
    ("ml", "en", "ML"),
    ("mm", "en", "MM"),
    ("mn", "en", "MN"),
    ("mo", "en", "MO"),
    ("mr", "en", "MR"),
    ("mt", "en", "MT"),
    ("mu", "en", "MU"),
    ("mv", "en", "MV"),
    ("mw", "en", "MW"),
    ("mx", "es", "MX"),
    ("my", "ms", "MY"),
    ("mz", "en", "MZ"),
    ("na", "en", "NA"),
    ("ne", "en", "NE"),
    ("ng", "en", "NG"),
    ("ni", "en", "NI"),
    ("nl", "nl", "NL"),
    ("no", "no", "NO"),
    ("np", "ne", "NP"),
    ("nz", "en", "NZ"),
    ("om", "ar", "OM"),
    ("pa", "es", "PA"),
    ("pe", "es", "PE"),
    ("pg", "en", "PG"),
    ("pk", "en", "PK"),
    ("pl", "pl", "PL"),
    ("pr", "es", "PR"),
    ("ps", "ar", "PS"),
    ("pt", "pt", "PT"),
    ("py", "es", "PY"),
    ("qa", "ar", "QA"),
    ("ro", "ro", "RO"),
    ("rs", "sr", "RS"),
    ("ru", "ru", "RU"),
    ("rw", "en", "RW"),
    ("sa", "ar", "SA"),
    ("sb", "en", "SB"),
    ("sc", "en", "SC"),
    ("se", "sv", "SE"),
    ("si", "sl", "SI"),
    ("sk", "sk", "SK"),
    ("sl", "en", "SL"),
    ("sn", "en", "SN"),
    ("so", "en", "SO"),
    ("sr", "en", "SR"),
    ("sv", "en", "SV"),
    ("sz", "en", "SZ"),
    ("tc", "en", "TC"),
    ("td", "en", "TD"),
    ("tg", "en", "TG"),
    ("th", "th", "TH"),
    ("tj", "en", "TJ"),
    ("tm", "en", "TM"),
    ("tn", "ar", "TN"),
    ("to", "en", "TO"),
    ("tr", "tr", "TR"),
    ("tt", "en", "TT"),
    ("tz", "en", "TZ"),
    ("ua", "uk", "UA"),
    ("ug", "en", "UG"),
    ("uy", "es", "UY"),
    ("uz", "en", "UZ"),
    ("vc", "en", "VC"),
    ("ve", "es", "VE"),
    ("vg", "en", "VG"),
    ("vi", "en", "VI"),
    ("vn", "vi", "VN"),
    ("vu", "en", "VU"),
    ("ws", "en", "WS"),
    ("ye", "en", "YE"),
    ("za", "en", "ZA"),
    ("zm", "en", "ZM"),
    ("zw", "en", "ZW"),
)

MARKET_PRESETS: dict[str, dict[str, str]] = {
    key: {"hl": hl, "gl": gl, "status": "opened"} for key, hl, gl in _OPENED_MARKETS
}

# US /store/apps/category/{CODE} first-pack measured 2026-08-18.
# empty = HTTP 200 but 0 live details?id= cards (age/region shelf).
CATEGORY_CODES: dict[str, str] = {
    "GAME": "opened",
    "SPORTS": "opened",
    "TRAVEL_AND_LOCAL": "opened",
    "FAMILY": "opened",
    "VIDEO_PLAYERS": "opened",
    "WEATHER": "opened",
    "FOOD_AND_DRINK": "opened",
    "EDUCATION": "opened",
    "COMICS": "opened",
    "BOOKS_AND_REFERENCE": "opened",
    "SOCIAL": "opened",
    "LIFESTYLE": "opened",
    "ENTERTAINMENT": "opened",
    "PHOTOGRAPHY": "opened",
    "PRODUCTIVITY": "opened",
    "SHOPPING": "opened",
    "ART_AND_DESIGN": "opened",
    "AUTO_AND_VEHICLES": "opened",
    "BEAUTY": "opened",
    "BUSINESS": "opened",
    "COMMUNICATION": "opened",
    "DATING": "empty",
    "EVENTS": "opened",
    "FINANCE": "opened",
    "HEALTH_AND_FITNESS": "opened",
    "HOUSE_AND_HOME": "opened",
    "LIBRARIES_AND_DEMO": "empty",
    "MAPS_AND_NAVIGATION": "opened",
    "MEDICAL": "empty",
    "MUSIC_AND_AUDIO": "opened",
    "NEWS_AND_MAGAZINES": "opened",
    "PARENTING": "opened",
    "PERSONALIZATION": "opened",
    "TOOLS": "opened",
    "ANDROID_WEAR": "opened",
    "APPLICATION": "opened",
    "WATCH_FACE": "opened",
    "FAMILY_ACTION": "empty",
    "FAMILY_CREATE": "empty",
    "FAMILY_EDUCATION": "empty",
    "GAME_ACTION": "opened",
    "GAME_ADVENTURE": "opened",
    "GAME_ARCADE": "opened",
    "GAME_BOARD": "opened",
    "GAME_CASUAL": "opened",
    "GAME_EDUCATIONAL": "opened",
    "GAME_SIMULATION": "opened",
    "GAME_STRATEGY": "opened",
    "GAME_RACING": "opened",
    "GAME_ROLE_PLAYING": "opened",
    "GAME_CASINO": "empty",
    "GAME_CARD": "opened",
    "GAME_MUSIC": "opened",
    "GAME_PUZZLE": "opened",
    "GAME_SPORTS": "opened",
    "GAME_TRIVIA": "opened",
    "GAME_WORD": "opened",
}

# FAMILY age chips: /store/apps/category/FAMILY?age=AGE_RANGE*
FAMILY_AGE_RANGES: dict[str, str] = {
    "AGE_RANGE1": "opened",
    "AGE_RANGE2": "opened",
    "AGE_RANGE3": "opened",
}

SEARCH_CATALOGS: dict[str, str] = {
    "apps": "opened",
    "games": "closed",  # HTTP 404 this session
}

OPENED_MODES = (
    "search",
    "category",
    "home",
    "detail",
    "developer",
    "datasafety",
)

SMOKE_QUERY_POOL = [
    "tide chart",
    "k-pop karaoke",
    "bus arrival",
    "sudoku daily",
    "blood pressure log",
]


def resolve_market(
    market: str | None,
    hl: str | None,
    gl: str | None,
) -> dict[str, Any]:
    preset_key = (market or "").strip().lower()
    preset = MARKET_PRESETS.get(preset_key, {})
    out_hl = (hl or "").strip() or preset.get("hl") or "en"
    out_gl = (gl or "").strip().upper() or preset.get("gl") or "US"
    status = preset.get("status") or "未验证"
    if not preset_key:
        for key, row in MARKET_PRESETS.items():
            if row["gl"] == out_gl and row["hl"] == out_hl:
                preset_key = key
                status = row["status"]
                break
        else:
            preset_key = out_gl.lower()
            status = MARKET_PRESETS.get(preset_key, {}).get("status") or "未验证"
            if status == "opened" and not hl:
                out_hl = MARKET_PRESETS[preset_key]["hl"]
    return {
        "market": preset_key,
        "hl": out_hl,
        "gl": out_gl,
        "status": status,
    }


def category_status(code: str) -> str:
    return CATEGORY_CODES.get((code or "").strip().upper(), "未验证")


def catalog_status(c: str) -> str:
    return SEARCH_CATALOGS.get((c or "apps").strip().lower(), "未验证")


def age_status(age: str | None) -> str:
    if not age:
        return "opened"
    return FAMILY_AGE_RANGES.get((age or "").strip().upper(), "未验证")


def categories_payload() -> list[dict[str, str]]:
    rows = []
    for code, status in CATEGORY_CODES.items():
        rows.append(
            {
                "listingId": code,
                "name": code.replace("_", " ").title(),
                "type": "category",
                "status": status,
                "country": "",
                "authority": "play.google.com",
                "categoryCode": code,
                "listingUrl": f"https://play.google.com/store/apps/category/{code}",
            }
        )
    return rows


def build_coverage_matrix() -> dict[str, Any]:
    """Opened cells only — random_smoke_input.py samples this document."""
    cells: list[dict[str, Any]] = []
    for market, row in MARKET_PRESETS.items():
        if row.get("status") != "opened":
            continue
        tmpl_market = {
            "market": market,
            "hl": row["hl"],
            "gl": row["gl"],
            "maxResults": 3,
        }
        cells.append(
            {
                "market": market,
                "mode": "search",
                "status": "opened",
                "template": {
                    "q": "{{query}}",
                    "mode": "search",
                    "c": "apps",
                    **tmpl_market,
                },
            }
        )
        cells.append(
            {
                "market": market,
                "mode": "home",
                "status": "opened",
                "template": {"mode": "home", **tmpl_market},
            }
        )
        cells.append(
            {
                "market": market,
                "mode": "category",
                "status": "opened",
                "template": {"mode": "category", "category": "GAME", **tmpl_market},
            }
        )
    for code, status in CATEGORY_CODES.items():
        if status != "opened" or code == "GAME":
            continue
        cells.append(
            {
                "market": "us",
                "mode": f"category-{code.lower()}",
                "status": "opened",
                "template": {
                    "mode": "category",
                    "category": code,
                    "market": "us",
                    "hl": "en",
                    "gl": "US",
                    "maxResults": 3,
                },
            }
        )
    for age, status in FAMILY_AGE_RANGES.items():
        if status != "opened":
            continue
        cells.append(
            {
                "market": "us",
                "mode": f"family-{age.lower()}",
                "status": "opened",
                "template": {
                    "mode": "category",
                    "category": "FAMILY",
                    "age": age,
                    "market": "us",
                    "hl": "en",
                    "gl": "US",
                    "maxResults": 3,
                },
            }
        )
    cells.append(
        {
            "market": "us",
            "mode": "search-enrich",
            "status": "opened",
            "template": {
                "q": "{{query}}",
                "mode": "search",
                "c": "apps",
                "market": "us",
                "hl": "en",
                "gl": "US",
                "enrichDetails": True,
                "maxResults": 2,
            },
        }
    )
    return {
        "primaryMarket": "us",
        "queryPool": list(SMOKE_QUERY_POOL),
        "queryKey": "q",
        "maxResults": 3,
        "cells": cells,
    }
