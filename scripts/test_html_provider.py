#!/usr/bin/env python3
"""Contract harness for HTML providers (fixture or remote)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rea_unblocker.classifier.html import classify_html
from rea_unblocker.parser.argonaut import parse_listings_from_html
from rea_unblocker.providers.mock import MockHtmlProvider
from rea_unblocker.providers.registry import build_default_registry


async def run(provider_name: str, profile_path: Path) -> int:
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    if provider_name == "mock_fixture":
        registry = build_default_registry(include_mock=True)
        provider_name = "mock_fixture"
    else:
        registry = build_default_registry(include_mock=False)
        if provider_name not in registry.names():
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": f"provider {provider_name} not configured",
                        "hint": "Set REA_MAC_RUNNER_URL or use --provider mock_fixture",
                    },
                    indent=2,
                )
            )
            return 2

    results = []
    ok_all = True
    for case in profile["contractTests"]:
        result = await registry.fetch(
            case["url"],
            kind=case["kind"],
            provider=provider_name,
            failover=False,
        )
        c = classify_html(result.html)
        rows = []
        detail_ok = True
        try:
            if c["hasArgonaut"] and not c["blocked"]:
                rows = parse_listings_from_html(result.html, kind=case["kind"])
        except Exception as exc:  # noqa: BLE001
            detail_ok = False
            rows = []
            parse_error = str(exc)
        else:
            parse_error = None

        listings_ok = True
        if case.get("minListings") is not None:
            listings_ok = len(rows) >= case["minListings"]
        if case.get("requireDetailId"):
            listings_ok = listings_ok and bool(rows and rows[0].get("listingId"))

        case_ok = (
            not result.blocked
            and c["bytes"] >= case["minBytes"]
            and c["hasArgonaut"] is case["requireArgonaut"]
            and listings_ok
            and detail_ok
        )
        ok_all = ok_all and case_ok
        results.append(
            {
                "id": case["id"],
                "ok": case_ok,
                "bytes": c["bytes"],
                "hasArgonaut": c["hasArgonaut"],
                "blocked": result.blocked or c["blocked"],
                "listingCount": len(rows),
                "provider": result.provider,
                "error": result.error or parse_error,
            }
        )

    print(json.dumps({"ok": ok_all, "provider": provider_name, "cases": results}, indent=2))
    return 0 if ok_all else 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="mock_fixture")
    parser.add_argument(
        "--profile",
        default=str(ROOT / "config" / "rea-target-profile.yaml"),
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.provider, Path(args.profile))))


if __name__ == "__main__":
    main()
