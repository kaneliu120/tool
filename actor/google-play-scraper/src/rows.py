"""Dataset row helpers."""

from __future__ import annotations


def omit_nulls(row: dict) -> dict:
    """Apify dataset schema rejects JSON null on string/number fields."""
    return {k: v for k, v in row.items() if v is not None}
