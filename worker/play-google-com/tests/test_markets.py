from src.markets import catalog_status, category_status, resolve_market


def test_resolve_us_preset():
    row = resolve_market("us", None, None)
    assert row["hl"] == "en" and row["gl"] == "US"
    assert row["status"] == "opened"


def test_resolve_explicit_unverified_gl():
    row = resolve_market(None, "sv", "SE")
    assert row["gl"] == "SE"
    assert row["status"] == "未验证"


def test_game_opened_games_catalog_closed():
    assert category_status("GAME") == "opened"
    assert catalog_status("apps") == "opened"
    assert catalog_status("games") == "closed"
