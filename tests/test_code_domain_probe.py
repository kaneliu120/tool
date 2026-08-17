from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "probes"))

from code_domain_probe import cite_gate, ptos_card, run  # noqa: E402


def test_rename_drops_old_symbol() -> None:
    report = run()
    assert "greet" not in report["v2_current_symbols"]
    assert "greet_user" in report["v2_current_symbols"]
    assert "handoff" in report["v2_current_symbols"]
    assert report["old_greet_still_current"] is False


def test_ptos_without_cite_rejected() -> None:
    report = run()
    assert report["ptos_gate"].startswith("reject")
    assert report["ptos_reject_rate"] == 1.0
    assert cite_gate(ptos_card("x")) != "ok"


def test_template_l2_passes_cite_gate() -> None:
    report = run()
    assert report["l2_gate"] == "ok"


def test_schemas_exist_and_parse() -> None:
    for name in ("code_l1_chunk.json", "wiki_derived_card.json"):
        data = json.loads((ROOT / "docs" / "schemas" / name).read_text(encoding="utf-8"))
        assert "required" in data
