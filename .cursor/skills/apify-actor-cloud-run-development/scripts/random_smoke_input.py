#!/usr/bin/env python3
"""Sample a fresh random-valid Actor/worker input from opened coverage-matrix cells.

Never uses README prefills, schema defaults, or fixed canaries (Austin, TX).

  python3 random_smoke_input.py --matrix ./coverage-matrix.json --out /tmp/accept.json
  python3 random_smoke_input.py --markets us,uk --modes search --query-pool "a,b,c" \\
      --query-key q --out /tmp/accept.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

FORBIDDEN_SUBSTRINGS = (
    "austin, tx",
    "austin tx",
)
PLACEHOLDER_SUBSTRINGS = (
    "replace-me",
    "replace-with-fresh",
    "example-query",
    "your-query-here",
)


def die(msg: str, code: int = 2) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_matrix(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        die(f"matrix not found: {path}")
    except json.JSONDecodeError as exc:
        die(f"matrix is not JSON: {exc}")
    return {}


def opened_cells(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    cells = matrix.get("cells") or []
    out = []
    for c in cells:
        status = str(c.get("status") or "").strip().lower()
        if status in {"opened", "open", "partial", "部分", "已验证"}:
            out.append(c)
    return out


def fill_template(obj: Any, query: str, max_results: int) -> Any:
    if isinstance(obj, dict):
        return {k: fill_template(v, query, max_results) for k, v in obj.items()}
    if isinstance(obj, list):
        return [fill_template(v, query, max_results) for v in obj]
    if isinstance(obj, str):
        return obj.replace("{{query}}", query).replace("{{maxResults}}", str(max_results))
    return obj


def pick_cell(
    cells: list[dict[str, Any]],
    *,
    primary_market: str,
    spot_check: bool,
) -> dict[str, Any]:
    if not cells:
        die("no opened/partial cells to sample — fill coverage-matrix.json")
    if not spot_check:
        return random.choice(cells)
    secondary = [c for c in cells if str(c.get("market") or "") != primary_market]
    non_search = [c for c in cells if str(c.get("mode") or "search").lower() != "search"]
    pool = secondary or non_search or cells
    # Prefer a cell that is both secondary-market and non-search when possible
    both = [c for c in secondary if c in non_search]
    return random.choice(both or pool)


def from_cli_pools(args: argparse.Namespace) -> dict[str, Any]:
    markets = [m.strip() for m in (args.markets or "").split(",") if m.strip()]
    modes = [m.strip() for m in (args.modes or "search").split(",") if m.strip()]
    queries = [q.strip() for q in (args.query_pool or "").split(",") if q.strip()]
    if not markets:
        die("provide --matrix or --markets")
    if not queries:
        die("provide --query-pool (fresh queries; not README cities)")
    cells = []
    for market in markets:
        for mode in modes:
            tmpl: dict[str, Any] = {args.query_key: "{{query}}", "maxResults": args.max_results}
            if args.market_key:
                tmpl[args.market_key] = market
            cells.append(
                {
                    "market": market,
                    "mode": mode,
                    "status": "opened",
                    "template": tmpl,
                }
            )
    return {
        "primaryMarket": markets[0],
        "queryPool": queries,
        "queryKey": args.query_key,
        "maxResults": args.max_results,
        "cells": cells,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--matrix", type=Path, help="coverage-matrix.json")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--markets", help="comma markets if no --matrix")
    p.add_argument("--modes", default="search")
    p.add_argument("--query-pool", help="comma queries (required without matrix.queryPool)")
    p.add_argument("--query-key", default="q")
    p.add_argument("--market-key", default="market")
    p.add_argument("--max-results", type=int, default=3)
    p.add_argument("--spot-check", action="store_true", default=True)
    p.add_argument("--no-spot-check", action="store_false", dest="spot_check")
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    max_results = args.max_results
    if max_results < 2 or max_results > 5:
        die("maxResults must be 2–5 for cost")

    if args.matrix:
        matrix = load_matrix(args.matrix)
        if args.query_pool:
            extra = [q.strip() for q in args.query_pool.split(",") if q.strip()]
            matrix["queryPool"] = list(matrix.get("queryPool") or []) + extra
        if args.markets:
            allow = {m.strip() for m in args.markets.split(",") if m.strip()}
            matrix["cells"] = [
                c for c in (matrix.get("cells") or []) if str(c.get("market") or "") in allow
            ]
    else:
        matrix = from_cli_pools(args)

    if matrix.get("maxResults"):
        try:
            mr = int(matrix["maxResults"])
            if 2 <= mr <= 5:
                max_results = mr
        except (TypeError, ValueError):
            pass

    queries = [str(q).strip() for q in (matrix.get("queryPool") or []) if str(q).strip()]
    if args.query_pool and args.matrix:
        queries = [q.strip() for q in args.query_pool.split(",") if q.strip()] or queries
    if not queries:
        die("queryPool empty — pass --query-pool with fresh values (not README/prefill)")

    for q in queries:
        ql = q.lower()
        if any(bad in ql for bad in FORBIDDEN_SUBSTRINGS):
            die(f"forbidden canary in queryPool: {q!r}")
        if any(bad in ql for bad in PLACEHOLDER_SUBSTRINGS):
            die(f"placeholder queryPool value {q!r} — pass --query-pool with fresh queries")

    cells = opened_cells(matrix)
    primary = str(matrix.get("primaryMarket") or (cells[0].get("market") if cells else "") or "")
    cell = pick_cell(cells, primary_market=primary, spot_check=args.spot_check)
    query = random.choice(queries)
    template = cell.get("template") or {matrix.get("queryKey") or args.query_key: "{{query}}"}
    payload = fill_template(template, query, max_results)
    if isinstance(payload, dict):
        payload.setdefault("maxResults", max_results)
        # Never let a copied template ship a huge cap
        try:
            if int(payload.get("maxResults") or 0) > 5:
                payload["maxResults"] = max_results
        except (TypeError, ValueError):
            payload["maxResults"] = max_results
    else:
        die("cell.template must be an object")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    meta = {
        "out": str(args.out),
        "market": cell.get("market"),
        "mode": cell.get("mode"),
        "query": query,
        "spotCheck": args.spot_check,
    }
    print(json.dumps(meta, ensure_ascii=False), file=sys.stderr)
    print(str(args.out))


if __name__ == "__main__":
    main()
