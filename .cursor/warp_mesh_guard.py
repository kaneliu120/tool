#!/usr/bin/env python3
"""Refuse warp-cli connect unless Zero Trust Mesh Include policy is active.

Kane's opendata-best profile must be tunnel_only + Include 100.96.0.0/12.
Naked connect with default Exclude 100.64.0.0/10 swallows Mesh and can
steal the default route. This VM must not connect until settings match.
"""

from __future__ import annotations

import sys

MESH_INCLUDE = "100.96.0.0/12"
MESH_SWALLOW = "100.64.0.0/10"


def evaluate(settings_text: str) -> list[str]:
    text = settings_text or ""
    low = text.lower()
    errors: list[str] = []
    if "tunnelonly" not in low and "tunnel_only" not in low and "tunnel only" not in low:
        errors.append("mode is not tunnel_only (opendata-best profile not applied)")
    if MESH_INCLUDE not in text:
        errors.append(f"missing Include {MESH_INCLUDE}")
    if "exclude mode" in low and MESH_SWALLOW in text:
        errors.append(f"Exclude {MESH_SWALLOW} would swallow Mesh {MESH_INCLUDE}")
    return errors


def main() -> int:
    blob = sys.stdin.read() if not sys.argv[1:] else Path_read(sys.argv[1])
    errors = evaluate(blob)
    if errors:
        print("warp-mesh-guard: REFUSE connect")
        for e in errors:
            print(f"- {e}")
        return 1
    print("warp-mesh-guard: OK to connect (tunnel_only + Include 100.96.0.0/12)")
    return 0


def Path_read(path: str) -> str:
    from pathlib import Path

    return Path(path).read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
