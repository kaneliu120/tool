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
ACTORS_ROOT = Path(os.environ.get("ACTORS_ROOT") or (HOME / "Projects" / "Apify Actors"))
WORKERS_ROOT = Path(os.environ.get("WORKERS_ROOT") or (HOME / "Projects" / "google run worker"))
SKIP_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "service-account.json",
    "=",
}
SKIP_SUFFIXES = {".pem", ".p12"}
SHARED_FILES = (
    "egress_control_client.py",
    "proxy_provider.py",
    "run_telemetry.py",
    "zyte_api.py",
)
SYNC_SHARED_SH = """#!/usr/bin/env bash
# Recovered from Cloud Run per-service source copies. Not the Mac git original.
set -euo pipefail
SHARED="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SHARED/.." && pwd)"
DEST="${1:-}"
[[ -n "$DEST" ]] || { echo "usage: $0 <worker-name-or-path>" >&2; exit 2; }
if [[ -d "$DEST/src" ]]; then
  OUT="$DEST"
elif [[ -d "$ROOT/$DEST/src" ]]; then
  OUT="$ROOT/$DEST"
else
  echo "FAIL: no worker src at $DEST" >&2
  exit 1
fi
mkdir -p "$OUT/src"
for f in egress_control_client.py proxy_provider.py run_telemetry.py zyte_api.py; do
  if [[ -f "$SHARED/$f" ]]; then
    cp "$SHARED/$f" "$OUT/src/$f"
  fi
done
echo "OK synced shared modules into $OUT/src"
"""


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
                        if not base or base in SKIP_NAMES or Path(info.filename).suffix in SKIP_SUFFIXES:
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


def recover_shared(workers_root: Path | None = None) -> dict:
    """Rebuild _shared/ from copies already inside worker src/ (GCS zips omit it)."""
    root = workers_root or WORKERS_ROOT
    shared = root / "_shared"
    donors: list[str] = []
    for peer in root.iterdir():
        if not peer.is_dir() or peer.name.startswith("_"):
            continue
        if all((peer / "src" / name).is_file() for name in SHARED_FILES):
            donors.append(peer.name)
    preferred = "airbnb-com" if "airbnb-com" in donors else (donors[0] if donors else "")
    if not preferred:
        return {"ok": False, "error": "no worker has all shared src copies", "donor": None}
    donor = root / preferred
    shared.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in SHARED_FILES:
        src = donor / "src" / name
        dest = shared / name
        shutil.copy2(src, dest)
        copied.append(name)
    script = shared / "sync_shared.sh"
    script.write_text(SYNC_SHARED_SH, encoding="utf-8")
    script.chmod(0o755)
    note = shared / "RECOVERED.md"
    note.write_text(
        "Recovered from Cloud Run per-service zip copies "
        f"(donor `{preferred}`).\n"
        "Not Kane's Mac `google run worker/_shared` git tree. "
        "If the Mac original differs, replace this directory.\n",
        encoding="utf-8",
    )
    return {"ok": True, "donor": preferred, "copied": copied, "donors": len(donors)}


def main() -> int:
    report = {
        "actors": pull_actors(),
        "workers": pull_workers(),
        "shared": recover_shared(),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    # Partial success is still useful.
    return 0 if (report["actors"].get("pulled") or report["workers"].get("pulled")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
