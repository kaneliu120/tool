#!/usr/bin/env python3
"""Download Kane's thin Actors from Apify and worker source zips from Cloud Run.

Writes to:
  $HOME/Projects/Apify Actors/<actor-name>/
  $HOME/Projects/google run worker/<service>/

Does not write env var values, .env, or credentials. Not a GitHub clone.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HOME = Path.home()
ACTORS_ROOT = HOME / "Projects" / "Apify Actors"
WORKERS_ROOT = HOME / "Projects" / "google run worker"
SKIP_NAMES = {".env", ".env.local", ".env.production", "credentials.json", "service-account.json"}
SKIP_SUFFIXES = {".pem", ".p12"}


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=False, text=True, capture_output=True, **kwargs)


def pull_actors() -> dict:
    token = os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN")
    if not token:
        return {"ok": False, "error": "no APIFY_TOKEN", "pulled": []}
    import httpx

    r = httpx.get(
        "https://api.apify.com/v2/acts",
        params={"limit": 300},
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    r.raise_for_status()
    items = r.json()["data"]["items"]
    ACTORS_ROOT.mkdir(parents=True, exist_ok=True)
    pulled: list[str] = []
    failed: list[str] = []
    with tempfile.TemporaryDirectory(prefix="apify-pull-") as tmp:
        tmp_path = Path(tmp)
        for item in items:
            name = item["name"]
            aid = item["id"]
            dest = ACTORS_ROOT / name
            # apify CLI treats --dir as cwd-relative even when given an absolute path.
            print(f"apify {name}", file=sys.stderr, flush=True)
            proc = run(["apify", "pull", aid, "--dir", name], cwd=str(tmp_path))
            work = tmp_path / name
            if proc.returncode != 0 or not (work / ".actor" / "actor.json").is_file():
                failed.append(f"{name}: {(proc.stderr or proc.stdout or '')[:200]}")
                continue
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(work, dest, dirs_exist_ok=True)
            for junk in dest.rglob("*"):
                if junk.is_file() and (junk.name in SKIP_NAMES or junk.suffix in SKIP_SUFFIXES):
                    junk.unlink(missing_ok=True)
            pulled.append(name)
    return {"ok": not failed, "pulled": pulled, "failed": failed, "listed": len(items)}


def pull_workers() -> dict:
    WORKERS_ROOT.mkdir(parents=True, exist_ok=True)
    proc = run(
        [
            "gcloud",
            "run",
            "services",
            "list",
            "--project=woker-260722",
            "--format=json",
        ]
    )
    if proc.returncode != 0:
        return {"ok": False, "error": (proc.stderr or "")[-400:], "pulled": []}
    services = json.loads(proc.stdout or "[]")
    pulled: list[str] = []
    failed: list[str] = []
    skipped: list[str] = []
    with tempfile.TemporaryDirectory(prefix="run-src-") as tmp:
        tmp_path = Path(tmp)
        for svc in services:
            meta = svc.get("metadata") or {}
            name = meta.get("name") or ""
            ann = meta.get("annotations") or {}
            loc = (ann.get("run.googleapis.com/build-source-location") or "").strip()
            zip_uri = loc.split("#", 1)[0] if loc.startswith("gs://") else ""
            if not name or not zip_uri:
                skipped.append(f"{name or '?'}: no build-source-location")
                continue
            print(f"gcs {name}", file=sys.stderr, flush=True)
            local_zip = tmp_path / f"{name}.zip"
            cp = run(["gcloud", "storage", "cp", zip_uri, str(local_zip)])
            if cp.returncode != 0 or not local_zip.is_file():
                failed.append(f"{name}: gcloud storage cp {(cp.stderr or '')[:160]}")
                continue
            dest = WORKERS_ROOT / name
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True)
            try:
                with zipfile.ZipFile(local_zip) as zf:
                    for info in zf.infolist():
                        base = Path(info.filename).name
                        if base in SKIP_NAMES or Path(info.filename).suffix in SKIP_SUFFIXES:
                            continue
                        zf.extract(info, dest)
            except zipfile.BadZipFile as exc:
                failed.append(f"{name}: bad zip {exc}")
                continue
            pulled.append(name)
    return {
        "ok": not failed,
        "pulled": pulled,
        "failed": failed,
        "skipped": skipped,
        "listed": len(services),
    }


def main() -> int:
    report = {"actors": pull_actors(), "workers": pull_workers()}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    actors_ok = report["actors"].get("ok")
    workers_ok = report["workers"].get("ok")
    # Partial success is still useful.
    return 0 if (report["actors"].get("pulled") or report["workers"].get("pulled")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
