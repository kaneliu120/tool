#!/usr/bin/env python3
"""Inventory Cloud Agent tools for website-page-research + Actor/worker work.

Prints JSON. Exit 0 when binaries needed for Phase 0 HTTP + VM Playwright exist.
gcloud auth, worker/actor repos, and vendor OAuth are reported as notes — they
are not installed by this checker (Kane parks CLI login until asked).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV_PY = ROOT / ".venv" / "bin" / "python"
SKILL_RECON = ROOT / ".cursor" / "skills" / "website-page-research"
SKILL_ACTOR = ROOT / ".cursor" / "skills" / "apify-actor-cloud-run-development"


def _which(name: str) -> str | None:
    return shutil.which(name)


def _run(cmd: list[str], timeout: int = 20) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def _venv_import(mod: str) -> bool:
    if not VENV_PY.is_file():
        return False
    code, _ = _run([str(VENV_PY), "-c", f"import {mod}"])
    return code == 0


def main() -> int:
    errors: list[str] = []
    notes: list[str] = []
    bins = {
        "curl": _which("curl"),
        "jq": _which("jq"),
        "rsync": _which("rsync"),
        "node": _which("node"),
        "npm": _which("npm"),
        "apify": _which("apify"),
        "gcloud": _which("gcloud"),
        "docker": _which("docker"),
        "google-chrome": _which("google-chrome") or _which("google-chrome-stable"),
        "xvfb-run": _which("xvfb-run"),
    }
    for required in ("curl", "jq", "rsync", "node"):
        if not bins[required]:
            errors.append(f"missing binary: {required}")

    files = {
        "http_contrast": SKILL_RECON / "scripts" / "http_contrast.sh",
        "generic_probe_js": SKILL_RECON / "scripts" / "generic_page_probe.js",
        "rsc_grep_js": SKILL_RECON / "scripts" / "rsc_keyword_grep.js",
        "playwright_probe": SKILL_RECON / "scripts" / "playwright_page_probe.py",
        "assert_cwd": SKILL_ACTOR / "scripts" / "assert_cwd.sh",
        "worker_triple_smoke": SKILL_ACTOR / "scripts" / "worker_triple_smoke.sh",
        "random_smoke_input": SKILL_ACTOR / "scripts" / "random_smoke_input.py",
        "scaffold_worker": SKILL_ACTOR / "scripts" / "scaffold_worker.sh",
        "scaffold_actor": SKILL_ACTOR / "scripts" / "scaffold_actor.sh",
        "worker_contract": SKILL_ACTOR / "templates" / "worker-contract.md",
    }
    for label, path in files.items():
        if not path.is_file():
            errors.append(f"missing {label}: {path.relative_to(ROOT)}")

    pkgs = {
        "playwright": _venv_import("playwright"),
        "curl_cffi": _venv_import("curl_cffi"),
        "httpx": _venv_import("httpx"),
    }
    for name, ok in pkgs.items():
        if not ok:
            errors.append(f".venv missing import {name} (run ./.cursor/install.sh)")

    if not bins["apify"]:
        notes.append("apify CLI not on PATH")
    if not bins["gcloud"]:
        notes.append("gcloud CLI not on PATH")
    else:
        code, out = _run(["gcloud", "auth", "list", "--format=value(account)"])
        if code != 0 or not out.strip():
            notes.append(
                "gcloud has no credentialed account — parked until Kane runs "
                "gcloud auth login --no-launch-browser (do not start OAuth unattended)"
            )
        project = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            check=False,
            capture_output=True,
            text=True,
        )
        proj = (project.stdout or "").strip()
        if not proj or proj == "(unset)":
            notes.append("gcloud project unset (expected woker-260722 after login)")

    workers = Path.home() / "Projects" / "google run worker"
    actors = Path.home() / "Projects" / "Apify Actors"
    if not workers.is_dir():
        notes.append(
            "WORKERS_ROOT missing on this VM "
            f"({workers}) — scaffold_worker.sh cannot copy peers here"
        )
    if not actors.is_dir():
        notes.append(
            "ACTORS_ROOT missing on this VM "
            f"({actors}) — scaffold_actor.sh cannot copy peers here"
        )

    if os.environ.get("APIFY_TOKEN") or bins["apify"]:
        if bins["apify"]:
            code, out = _run(["apify", "info"])
            if code != 0:
                notes.append("apify info failed (CLI present, session unknown)")
            elif "username:" in out or "userId:" in out:
                notes.append("apify CLI responds to info (token/session present)")

    report = {
        "ok": not errors,
        "errors": errors,
        "notes": notes,
        "bins": bins,
        "venv_packages": pkgs,
        "mac_chrome_bridge": False,
        "cloud_playwright_probe": files["playwright_probe"].is_file() and pkgs["playwright"],
        "mem0_api_key": bool(os.environ.get("MEM0_API_KEY")),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
