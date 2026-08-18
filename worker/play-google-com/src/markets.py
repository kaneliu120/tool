"""Play markets, catalogs, and category codes from the recon contract.

Opened cells are session-measured (report 2026-08-17 + Cloud Agent HTTP 2026-08-18).
Unlisted gl/hl values are accepted as ISO/BCP-47 but stay 未验证.
"""

from __future__ import annotations

from typing import Any

# Site geography for Cloud Run: Play is global on play.google.com; US is the
# primary opened market and Google HQ. Region = us-central1.

MARKET_PRESETS: dict[str, dict[str, str]] = {
    "us": {"hl": "en", "gl": "US", "status": "opened"},
    "ph": {"hl": "zh-CN", "gl": "PH", "status": "opened"},
    "gb": {"hl": "en", "gl": "GB", "status": "opened"},
    "au": {"hl": "en", "gl": "AU", "status": "opened"},
    "jp": {"hl": "ja", "gl": "JP", "status": "opened"},
    "tw": {"hl": "zh-TW", "gl": "TW", "status": "opened"},
    "de": {"hl": "de", "gl": "DE", "status": "opened"},
    "fr": {"hl": "fr", "gl": "FR", "status": "opened"},
    "in": {"hl": "en", "gl": "IN", "status": "opened"},
    "br": {"hl": "pt", "gl": "BR", "status": "opened"},
    "ca": {"hl": "en", "gl": "CA", "status": "opened"},
    "sg": {"hl": "en", "gl": "SG", "status": "opened"},
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
            status = "未验证"
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
