#!/usr/bin/env python3
"""Thin shim: run the canonical mem0ctl so ``python scripts/mem0ctl.py`` from this
repo behaves exactly like the skill CLI (same flags, ``--raw``, MCP-first search).

Falls back to the in-repo ``mem0_client`` only when the canonical skill is absent
(Cloud Agents without the skill checkout)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

CANONICAL = Path.home() / "Projects/devin-skills/skills/mem0-selfhost/scripts/mem0ctl.py"
if CANONICAL.is_file():
    os.execv(sys.executable, [sys.executable, str(CANONICAL), *sys.argv[1:]])

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mem0_client.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
