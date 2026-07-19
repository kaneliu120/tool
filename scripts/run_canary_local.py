#!/usr/bin/env python3
"""Local Actor canary using mock provider (software closed loop)."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rea_unblocker.actor.client import ActorHtmlClient


async def main() -> int:
    client = ActorHtmlClient(provider_name="mock_fixture", use_mock_if_missing=True)
    urls = [
        (
            "https://www.realestate.com.au/buy/in-melbourne,+vic/list-1",
            "sale_search",
        ),
        (
            "https://www.realestate.com.au/rent/in-melbourne,+vic/list-1",
            "rent_search",
        ),
    ]
    all_rows = []
    for url, kind in urls:
        rows = await client.fetch_and_parse(url, kind=kind)
        all_rows.extend(rows)
    client.summary.datasetRows = len(all_rows)
    try:
        client.summary.assert_canary(min_rows=2)
        status = "SUCCEEDED"
        code = 0
    except AssertionError as exc:
        status = f"FAILED: {exc}"
        code = 1
    print(
        json.dumps(
            {
                "runStatus": status,
                "RUN_SUMMARY": client.summary.to_dict(),
                "sampleRows": all_rows[:4],
            },
            indent=2,
        )
    )
    return code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
