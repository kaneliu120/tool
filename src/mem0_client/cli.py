"""CLI for the self-hosted Mem0 gateway (Cloud Agent / local)."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from mem0_client.client import Mem0Client, Mem0Config, Mem0Error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mem0ctl",
        description="Call Kane's self-hosted Mem0 (public MCP or local REST).",
    )
    parser.add_argument(
        "--user-id",
        default=None,
        help="Mem0 user scope (default MEM0_USER_ID or kane)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health", help="GET /healthz on the public MCP host (no auth)")
    sub.add_parser("tools", help="List MCP tools (requires MEM0_API_KEY)")

    search = sub.add_parser("search", help="Semantic search")
    search.add_argument("query")
    search.add_argument("--top-k", type=int, default=5)
    search.add_argument("--threshold", type=float, default=None)

    add = sub.add_parser("add", help="Write a memory")
    add.add_argument("text")
    add.add_argument(
        "--raw",
        action="store_true",
        help="infer=false: store text as-is without LLM extraction",
    )

    listed = sub.add_parser("list", help="List memories for the user")
    listed.add_argument("--top-k", type=int, default=50)

    args = parser.parse_args(argv)
    try:
        with Mem0Client(Mem0Config.from_env()) as client:
            if args.cmd == "health":
                _print(client.health())
                return 0
            if args.cmd == "tools":
                _print({"tools": client.list_tools()})
                return 0
            user_id = args.user_id
            if args.cmd == "search":
                _print(
                    client.search(
                        args.query,
                        user_id=user_id,
                        top_k=args.top_k,
                        threshold=args.threshold,
                    )
                )
                return 0
            if args.cmd == "add":
                _print(
                    client.add(
                        args.text,
                        user_id=user_id,
                        infer=not args.raw,
                    )
                )
                return 0
            if args.cmd == "list":
                _print(client.list_memories(user_id=user_id, top_k=args.top_k))
                return 0
    except Mem0Error as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 2
    return 1


def _print(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
