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
    search.add_argument(
        "--meta",
        default=None,
        help='JSON metadata filter, e.g. {"kind":"handoff"}',
    )

    add = sub.add_parser("add", help="Write a memory")
    add.add_argument("text")
    add.add_argument(
        "--raw",
        action="store_true",
        help="infer=false: store text as-is without LLM extraction",
    )

    listed = sub.add_parser("list", help="List memories for the user")
    listed.add_argument("--top-k", type=int, default=50)

    fetched = sub.add_parser("get", help="Fetch one memory by id")
    fetched.add_argument("memory_id")

    handoff = sub.add_parser("handoff", help="Store a brain-style handoff document")
    handoff.add_argument("--project", required=True)
    handoff.add_argument("--verdict", required=True)
    handoff.add_argument("--done", required=True)
    handoff.add_argument("--status", required=True)
    handoff.add_argument("--next", required=True, dest="next_steps")
    handoff.add_argument("--gotchas", default="无")
    handoff.add_argument("--evidence", default="")

    decision = sub.add_parser("decision", help="Store a durable decision")
    decision.add_argument("text")
    decision.add_argument("--project", default=None)

    gotcha = sub.add_parser("gotcha", help="Store a reusable gotcha")
    gotcha.add_argument("text")
    gotcha.add_argument("--project", default=None)

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
                        meta_json=args.meta,
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
            if args.cmd == "get":
                _print(client.get(args.memory_id))
                return 0
            if args.cmd == "handoff":
                _print(
                    client.handoff(
                        project=args.project,
                        verdict=args.verdict,
                        done=args.done,
                        status=args.status,
                        next_steps=args.next_steps,
                        gotchas=args.gotchas,
                        evidence=args.evidence,
                        user_id=user_id,
                    )
                )
                return 0
            if args.cmd == "decision":
                _print(
                    client.decision(
                        args.text,
                        project=args.project,
                        user_id=user_id,
                    )
                )
                return 0
            if args.cmd == "gotcha":
                _print(
                    client.gotcha(
                        args.text,
                        project=args.project,
                        user_id=user_id,
                    )
                )
                return 0
    except Mem0Error as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 2
    return 1


def _print(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
