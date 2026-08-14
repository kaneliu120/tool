from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
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


def test_cloud_auth_is_noop_without_secrets() -> None:
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in {
            "GCP_SA_JSON",
            "GCP_PROJECT",
            "VPS_SSH_KEY",
            "VPS_SSH_HOST",
            "VPS_SSH_USER",
            "APIFY_TOKEN",
            "CLOUDFLARE_API_TOKEN",
        }
    }
    proc = subprocess.run(
        ["bash", "-c", "set -euo pipefail; . .cursor/cloud-auth.sh; echo ok"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.strip() == "ok"


def test_cloud_auth_writes_escaped_ssh_key_and_config() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"GCP_SA_JSON", "GCP_PROJECT", "APIFY_TOKEN", "CLOUDFLARE_API_TOKEN"}
        }
        env.update(
            {
                "HOME": tmp,
                "VPS_SSH_KEY": "-----BEGIN OPENSSH PRIVATE KEY-----\\ntestkey\\n-----END OPENSSH PRIVATE KEY-----",
                "VPS_SSH_HOST": "203.0.113.10",
                "VPS_SSH_USER": "ubuntu",
            }
        )
        proc = subprocess.run(
            ["bash", "-c", "set -euo pipefail; . .cursor/cloud-auth.sh"],
            cwd=ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        key = Path(tmp) / ".ssh" / "ovhcloud_ca_ed25519"
        cfg = Path(tmp) / ".ssh" / "config"
        text = key.read_text()
        assert "BEGIN OPENSSH PRIVATE KEY" in text
        assert "\\n" not in text
        assert text.count("\n") >= 2
        config = cfg.read_text()
        assert "Host vps-b85e86d3" in config
        assert "HostName 203.0.113.10" in config
        assert "IdentityFile" in config
        assert oct(key.stat().st_mode)[-3:] == "600"
