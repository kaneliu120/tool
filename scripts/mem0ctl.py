#!/usr/bin/env python3
"""Wrapper so Cloud Agents can run ``python scripts/mem0ctl.py`` from the repo root."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mem0_client.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
