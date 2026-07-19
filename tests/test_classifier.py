from pathlib import Path

from rea_unblocker.classifier.html import classify_html

FIXTURES = Path(__file__).parent / "fixtures"


def test_live_kpsdk_shell_classified():
    html = (FIXTURES / "kpsdk_shell_live.html").read_text(encoding="utf-8")
    c = classify_html(html)
    assert c["bytes"] < 5000
    assert c["hasKpsdk"] is True
    assert c["tinyKasadaShell"] is True
    assert c["hasArgonaut"] is False
    assert c["blocked"] is True


def test_argonaut_sale_srp_classified():
    html = (FIXTURES / "argonaut_sale_srp.html").read_text(encoding="utf-8")
    c = classify_html(html)
    assert c["bytes"] > 100_000
    assert c["hasArgonaut"] is True
    assert c["hasBuySearch"] is True
    assert c["tinyKasadaShell"] is False
    assert c["blocked"] is False


def test_empty_html():
    c = classify_html("")
    assert c["empty"] is True
    assert c["bytes"] == 0
