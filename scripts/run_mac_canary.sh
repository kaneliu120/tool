#!/usr/bin/env bash
# Run REA live canary on a real macOS host with Chrome.
# Usage:
#   ./scripts/run_mac_canary.sh
# Optional:
#   REA_PROXY_SERVER=http://user:pass@host:port ./scripts/run_mac_canary.sh
#   REA_MAC_RUNNER_TOKEN=secret ./scripts/run_mac_canary.sh --serve-only

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "ERROR: this script must run on macOS (found $(uname -s))" >&2
  exit 2
fi

SERVE_ONLY=0
if [[ "${1:-}" == "--serve-only" ]]; then
  SERVE_ONLY=1
fi

python3 -m venv .venv 2>/dev/null || true
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -U pip >/dev/null
pip install -e ".[dev]" >/dev/null
pip install playwright >/dev/null
python -m playwright install chrome >/dev/null || python -m playwright install chromium

export REA_RUNNER_PORT="${REA_RUNNER_PORT:-8090}"
export REA_RUNNER_TOKEN="${REA_RUNNER_TOKEN:-${REA_MAC_RUNNER_TOKEN:-dev-mac-token}}"
export REA_MAC_RUNNER_URL="${REA_MAC_RUNNER_URL:-http://127.0.0.1:${REA_RUNNER_PORT}}"
export REA_MAC_RUNNER_TOKEN="${REA_MAC_RUNNER_TOKEN:-$REA_RUNNER_TOKEN}"

echo "==> starting Mac runner on :${REA_RUNNER_PORT}"
python -m rea_unblocker.runner.server &
RUNNER_PID=$!
cleanup() {
  kill "$RUNNER_PID" 2>/dev/null || true
}
trap cleanup EXIT

for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${REA_RUNNER_PORT}/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done
curl -fsS "http://127.0.0.1:${REA_RUNNER_PORT}/healthz" | tee /tmp/rea-runner-health.json
echo

if [[ "$SERVE_ONLY" -eq 1 ]]; then
  echo "Runner ready: $REA_MAC_RUNNER_URL"
  echo "Token: $REA_MAC_RUNNER_TOKEN"
  echo "Expose this URL (Tailscale/ngrok/SSH tunnel) then set REA_MAC_RUNNER_URL for the cloud agent."
  wait "$RUNNER_PID"
  exit 0
fi

echo "==> unit tests"
pytest -q

echo "==> live 4-URL contract via internal_mac_runner"
PROXY_CTX='{}'
if [[ -n "${REA_PROXY_SERVER:-}" ]]; then
  PROXY_CTX=$(python - <<'PY'
import json, os
print(json.dumps({
  "proxy": {
    "server": os.environ["REA_PROXY_SERVER"],
    "username": os.environ.get("REA_PROXY_USERNAME"),
    "password": os.environ.get("REA_PROXY_PASSWORD"),
    "country": os.environ.get("REA_PROXY_COUNTRY", "AU"),
    "sessionId": os.environ.get("REA_PROXY_SESSION", "rea-mac-canary-001"),
  }
}))
PY
)
fi

python - <<PY
import asyncio, json, os, yaml
from pathlib import Path
from rea_unblocker.classifier.html import classify_html
from rea_unblocker.parser.argonaut import parse_listings_from_html
from rea_unblocker.providers.registry import build_default_registry

async def main():
    profile = yaml.safe_load(Path("config/rea-target-profile.yaml").read_text())
    registry = build_default_registry(include_mock=False)
    assert "internal_mac_runner" in registry.names(), registry.names()
    proxy = json.loads('''$PROXY_CTX''')
    cases = []
    ok_all = True
    for case in profile["contractTests"]:
        result = await registry.fetch(
            case["url"],
            kind=case["kind"],
            provider="internal_mac_runner",
            context={**proxy, "timeoutMs": 90000, "warmup": True},
            failover=False,
        )
        c = classify_html(result.html)
        rows = []
        err = result.error
        try:
            if c["hasArgonaut"] and not c["blocked"]:
                rows = parse_listings_from_html(result.html, kind=case["kind"])
        except Exception as exc:
            err = str(exc)
        listings_ok = True
        if case.get("minListings") is not None:
            listings_ok = len(rows) >= case["minListings"]
        if case.get("requireDetailId"):
            listings_ok = listings_ok and bool(rows and rows[0].get("listingId"))
        case_ok = (
            not result.blocked
            and c["bytes"] >= case["minBytes"]
            and c["hasArgonaut"] is case["requireArgonaut"]
            and listings_ok
            and not err
        )
        ok_all = ok_all and case_ok
        cases.append({
            "id": case["id"],
            "ok": case_ok,
            "bytes": c["bytes"],
            "hasArgonaut": c["hasArgonaut"],
            "tinyKasadaShell": c["tinyKasadaShell"],
            "listingCount": len(rows),
            "statusCode": result.status_code,
            "error": err,
        })
    out = {"ok": ok_all, "provider": "internal_mac_runner", "cases": cases}
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/mac_canary_result.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    raise SystemExit(0 if ok_all else 1)

asyncio.run(main())
PY

echo "==> wrote artifacts/mac_canary_result.json"
