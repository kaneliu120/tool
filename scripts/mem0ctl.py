#!/usr/bin/env python3
"""Wrapper so Cloud Agents can run ``python3 scripts/mem0ctl.py`` from the repo root.

System ``python3`` on the Cloud image does not include ``httpx``. After
``.cursor/install.sh``, dependencies live in ``.venv``. Re-exec into that
interpreter when needed so AGENTS.md / stop-hook commands keep working.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV_PY = ROOT / ".venv" / "bin" / "python"


def _in_project_venv() -> bool:
    return Path(sys.prefix).resolve() == (ROOT / ".venv").resolve()


def _reexec_venv_if_needed() -> None:
    try:
        import httpx  # noqa: F401
        return
    except ImportError:
        pass
    if _in_project_venv():
        sys.stderr.write(
            "mem0ctl: .venv python is missing httpx. Re-run ./.cursor/install.sh\n"
        )
        raise SystemExit(1)
    if not VENV_PY.is_file():
        sys.stderr.write(
            "mem0ctl: httpx is missing and .venv does not exist. "
            "Run ./.cursor/install.sh first.\n"
        )
        raise SystemExit(1)
    os.execv(
        str(VENV_PY),
        [str(VENV_PY), str(Path(__file__).resolve()), *sys.argv[1:]],
    )


_reexec_venv_if_needed()

sys.path.insert(0, str(ROOT / "src"))

from mem0_client.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
