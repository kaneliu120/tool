from src.markets import catalog_status, category_status, resolve_market


def test_resolve_us_preset():
    row = resolve_market("us", None, None)
    assert row["hl"] == "en" and row["gl"] == "US"
    assert row["status"] == "opened"


def test_resolve_explicit_unverified_gl():
    row = resolve_market(None, "zh-CN", "CN")
    assert row["gl"] == "CN"
    assert row["status"] == "未验证"


def test_game_opened_games_catalog_closed():
    assert category_status("GAME") == "opened"
    assert category_status("GAME_WORD") == "opened"
    assert category_status("APPLICATION") == "opened"
    assert category_status("WATCH_FACE") == "opened"
    assert category_status("DATING") == "empty"
    assert catalog_status("apps") == "opened"
    assert catalog_status("games") == "closed"


def test_all_presets_opened():
    from src.markets import FAMILY_AGE_RANGES, MARKET_PRESETS, build_coverage_matrix

    assert len(MARKET_PRESETS) == 183
    assert all(row["status"] == "opened" for row in MARKET_PRESETS.values())
    matrix = build_coverage_matrix()
    markets = {c["market"] for c in matrix["cells"]}
    assert markets == set(MARKET_PRESETS)
    assert {"kr", "mx", "es", "ng", "uz"} <= markets
    assert any(c["mode"] == "search-enrich" for c in matrix["cells"])
    assert any(c["template"].get("category") == "SPORTS" for c in matrix["cells"])
    assert any(c["template"].get("category") == "WATCH_FACE" for c in matrix["cells"])
    assert any(c["template"].get("age") == "AGE_RANGE1" for c in matrix["cells"])
    assert all(v == "opened" for v in FAMILY_AGE_RANGES.values())


def test_checked_in_matrix_matches_builder():
    import json
    from pathlib import Path

    from src.markets import build_coverage_matrix

    on_disk = json.loads(Path("coverage-matrix.json").read_text(encoding="utf-8"))
    assert on_disk == build_coverage_matrix()
