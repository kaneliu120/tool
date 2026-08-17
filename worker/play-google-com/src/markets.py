"""Play markets, catalogs, and category codes from the recon contract.

Opened cells are session-measured (report 2026-08-17 + this Cloud Agent HTTP).
Unlisted gl/hl values are accepted as ISO/BCP-47 but stay 未验证.
"""

from __future__ import annotations

from typing import Any

# Site geography for Cloud Run: Play is global on play.google.com; US is the
# opened secondary market and Google HQ. Region = us-central1.

MARKET_PRESETS: dict[str, dict[str, str]] = {
    "us": {"hl": "en", "gl": "US", "status": "opened"},
    "ph": {"hl": "zh-CN", "gl": "PH", "status": "opened"},
    "gb": {"hl": "en", "gl": "GB", "status": "未验证"},
    "au": {"hl": "en", "gl": "AU", "status": "未验证"},
    "jp": {"hl": "ja", "gl": "JP", "status": "未验证"},
    "tw": {"hl": "zh-TW", "gl": "TW", "status": "未验证"},
    "de": {"hl": "de", "gl": "DE", "status": "未验证"},
    "fr": {"hl": "fr", "gl": "FR", "status": "未验证"},
    "in": {"hl": "en", "gl": "IN", "status": "未验证"},
    "br": {"hl": "pt", "gl": "BR", "status": "未验证"},
    "ca": {"hl": "en", "gl": "CA", "status": "未验证"},
    "sg": {"hl": "en", "gl": "SG", "status": "未验证"},
}

# App taxonomy seen on Home HTML (shape) plus GAME_* from GAME page.
# GAME and SPORTS pages were opened this session; others 未验证 until fetched.
CATEGORY_CODES: dict[str, str] = {
    "GAME": "opened",
    "SPORTS": "opened",
    "TRAVEL_AND_LOCAL": "partial",  # seen on Maps LDP, page itself 未逐个打开
    "FAMILY": "shape",
    "VIDEO_PLAYERS": "shape",
    "WEATHER": "shape",
    "FOOD_AND_DRINK": "shape",
    "EDUCATION": "shape",
    "COMICS": "shape",
    "BOOKS_AND_REFERENCE": "shape",
    "SOCIAL": "shape",
    "LIFESTYLE": "shape",
    "ENTERTAINMENT": "shape",
    "PHOTOGRAPHY": "shape",
    "PRODUCTIVITY": "shape",
    "SHOPPING": "shape",
    "ART_AND_DESIGN": "未验证",
    "AUTO_AND_VEHICLES": "未验证",
    "BEAUTY": "未验证",
    "BUSINESS": "未验证",
    "COMMUNICATION": "未验证",
    "DATING": "未验证",
    "EVENTS": "未验证",
    "FINANCE": "未验证",
    "HEALTH_AND_FITNESS": "未验证",
    "HOUSE_AND_HOME": "未验证",
    "LIBRARIES_AND_DEMO": "未验证",
    "MAPS_AND_NAVIGATION": "未验证",
    "MEDICAL": "未验证",
    "MUSIC_AND_AUDIO": "未验证",
    "NEWS_AND_MAGAZINES": "未验证",
    "PARENTING": "未验证",
    "PERSONALIZATION": "未验证",
    "TOOLS": "未验证",
    "ANDROID_WEAR": "未验证",
    "GAME_ACTION": "partial",
    "GAME_ADVENTURE": "partial",
    "GAME_ARCADE": "partial",
    "GAME_BOARD": "partial",
    "GAME_CASUAL": "partial",
    "GAME_EDUCATIONAL": "partial",
    "GAME_SIMULATION": "partial",
    "GAME_STRATEGY": "未验证",
    "GAME_RACING": "未验证",
    "GAME_ROLE_PLAYING": "未验证",
    "GAME_CASINO": "未验证",
    "GAME_CARD": "未验证",
    "GAME_MUSIC": "未验证",
    "GAME_PUZZLE": "未验证",
    "GAME_SPORTS": "未验证",
    "GAME_TRIVIA": "未验证",
    "GAME_WORD": "未验证",
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
