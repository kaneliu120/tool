from pathlib import Path

import pytest

from src.parse import (
    extract_package_ids,
    is_negative_page,
    is_ready_detail,
    is_ready_list,
    package_from_url,
    parse_datasafety,
    parse_detail,
    parse_json_ld,
    parse_search_cards,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_search_card_keep():
    html = _read("search_card.html")
    items = parse_search_cards(html, channel="search", hl="en", gl="US")
    assert len(items) == 1
    row = items[0]
    assert row["listingId"] == "com.google.android.keep"
    assert "Keep" in row["name"]
    assert row["developer"] == "Google LLC"
    assert row["ratingValue"] == 4.7
    assert row["country"] == "US"
    assert row["authority"] == "play.google.com"
    assert row["imageUrl"]


def test_category_card_clash():
    html = _read("category_card.html")
    items = parse_search_cards(html, channel="category", hl="en", gl="US")
    assert items[0]["listingId"] == "com.supercell.clashofclans"
    assert items[0]["name"] == "Clash of Clans"
    assert items[0]["ratingValue"] == 4.5


def test_json_ld_maps():
    html = '<script type="application/ld+json">' + _read("detail_jsonld.json") + "</script>"
    ld = parse_json_ld(html)
    assert ld and ld["@type"] == "SoftwareApplication"
    assert ld["name"] == "Google Maps"


def test_detail_header_chips():
    html = _read("detail_header.html") + _read("detail_updated.html")
    html = '<script type="application/ld+json">' + _read("detail_jsonld.json") + "</script>" + html
    row = parse_detail(html, package_id="com.google.android.apps.maps", hl="en", gl="US")
    assert row["name"] == "Google Maps"
    assert row["developer"] == "Google LLC"
    assert row["developerId"] == "5700313618786177705"
    assert row["containsAds"] is True
    assert row["installs"] == "10B+"
    assert row["contentRating"] == "Everyone"
    assert row["jsonLd"] is True
    assert row["priceDisplay"] == "Free"


def test_datasafety_headings():
    row = parse_datasafety(
        _read("datasafety_snippet.html"),
        package_id="com.google.android.apps.maps",
        hl="en",
        gl="US",
    )
    assert row["dataSharedWithThirdParties"] == "none"
    assert row["dataCollectedDeclared"] is True
    assert row["channel"] == "datasafety"


def test_negative_not_found():
    html = _read("not_found.html")
    assert is_negative_page(html, status_code=404)
    assert not is_ready_list(html)


def test_package_from_url_live_only():
    assert package_from_url("https://play.google.com/store/apps/details?id=com.foo.bar") == "com.foo.bar"
    assert package_from_url("com.foo.bar") == "com.foo.bar"
    assert extract_package_ids("no apps here") == []


def test_ready_detail_requires_software_or_name():
    html = '<script type="application/ld+json">' + _read("detail_jsonld.json") + "</script>"
    assert is_ready_detail(html)
