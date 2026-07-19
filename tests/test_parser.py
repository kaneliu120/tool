from pathlib import Path

import pytest

from rea_unblocker.parser.argonaut import (
    ArgonautParseError,
    extract_argonaut,
    parse_listings_from_html,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_sale_srp_rows():
    html = (FIXTURES / "argonaut_sale_srp.html").read_text(encoding="utf-8")
    rows = parse_listings_from_html(html, kind="sale_search")
    assert len(rows) >= 2
    assert rows[0]["listingId"] == "149100001"
    assert rows[0]["listingType"] == "sale"
    assert rows[0]["address"]
    assert rows[0]["price"]
    assert rows[0]["url"]


def test_parse_rent_detail():
    html = (FIXTURES / "argonaut_rent_ldp.html").read_text(encoding="utf-8")
    rows = parse_listings_from_html(html, kind="rent_detail")
    assert len(rows) == 1
    assert rows[0]["listingId"] == "149000001"
    assert rows[0]["listingType"] == "rent"


def test_shell_page_fails_closed():
    html = (FIXTURES / "kpsdk_shell_live.html").read_text(encoding="utf-8")
    with pytest.raises(ArgonautParseError):
        extract_argonaut(html)
