"""HTML response classifier for REA / Kasada failure modes."""

from __future__ import annotations

from typing import Any


def classify_html(html: str | None) -> dict[str, Any]:
    """Classify acquisition HTML into Argonaut / KPSDK / empty states.

    This is the contract-test backbone: every provider result must be
    classified before it can be treated as a successful fetch.
    """
    text = html or ""
    nbytes = len(text.encode("utf-8")) if text else 0
    has_argonaut = "window.ArgonautExchange" in text
    has_kpsdk = (
        "window.KPSDK" in text
        or "KP_UIDz" in text
        or "ips.js" in text
        or "x-kpsdk" in text.lower()
    )
    tiny_shell = nbytes < 5000 and has_kpsdk and not has_argonaut
    return {
        "bytes": nbytes,
        "hasArgonaut": has_argonaut,
        "hasKpsdk": has_kpsdk,
        "tinyKasadaShell": tiny_shell,
        "hasBuySearch": "buySearch" in text,
        "hasRentSearch": "rentSearch" in text,
        "hasDetails": '"details"' in text or "property_listing" in text,
        "blocked": tiny_shell or (has_kpsdk and not has_argonaut and nbytes < 20000),
        "empty": nbytes == 0,
    }
