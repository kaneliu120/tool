from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cursor_agent_config_checker_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_cursor_agent_config.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = json.loads(proc.stdout)
    assert report["ok"] is True
    assert report["errors"] == []


def test_system_python3_mem0ctl_health_and_handoff_help() -> None:
    """Cloud hooks/AGENTS.md invoke system python3, not .venv/bin/python."""
    health = subprocess.run(
        ["/usr/bin/python3", str(ROOT / "scripts" / "mem0ctl.py"), "health"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert health.returncode == 0, health.stdout + health.stderr
    payload = json.loads(health.stdout)
    assert payload.get("status") == "ok"
    help_proc = subprocess.run(
        ["/usr/bin/python3", str(ROOT / "scripts" / "mem0ctl.py"), "handoff", "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert help_proc.returncode == 0, help_proc.stdout + help_proc.stderr
    assert "--project" in help_proc.stdout
    assert "--next" in help_proc.stdout
