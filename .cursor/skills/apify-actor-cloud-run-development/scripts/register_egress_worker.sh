#!/usr/bin/env bash
# Register (or fetch) an egress-control workerId. Admin key stays on this machine.
# Never prints the admin key. Runtime key is printed once for Cloud Run env.
#
# Usage:
#   bash register_egress_worker.sh <workerId> [--from-peer PEER] [--print-key]
#
# Admin key resolution (first hit):
#   $EGRESS_ADMIN_API_KEY
#   $EGRESS_CONTROL_REPO/deploy/.env.generated.local  (default ~/Projects/egress-control)
set -euo pipefail

BASE="${EGRESS_CONTROL_BASE_URL:-https://worker.opendata.best}"
REPO="${EGRESS_CONTROL_REPO:-$HOME/Projects/egress-control}"
WORKER_ID=""
FROM_PEER=""
PRINT_KEY=0

usage() {
  echo "usage: $0 <workerId> [--from-peer PEER] [--print-key]" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from-peer) FROM_PEER="${2:-}"; shift 2 ;;
    --print-key) PRINT_KEY=1; shift ;;
    --help|-h) usage ;;
    *)
      if [[ -z "$WORKER_ID" ]]; then WORKER_ID="$1"; shift; else usage; fi
      ;;
  esac
done
[[ -n "$WORKER_ID" ]] || usage

load_admin() {
  if [[ -n "${EGRESS_ADMIN_API_KEY:-}" ]]; then
    printf '%s' "$EGRESS_ADMIN_API_KEY"
    return
  fi
  local envf="$REPO/deploy/.env.generated.local"
  if [[ -f "$envf" ]]; then
    python3 - "$envf" <<'PY'
import sys
path = sys.argv[1]
for line in open(path, encoding="utf-8"):
    if line.startswith("EGRESS_ADMIN_API_KEY="):
        print(line.split("=", 1)[1].strip(), end="")
        break
PY
    return
  fi
  printf ''
}

ADMIN="$(load_admin)"
if [[ -z "$ADMIN" ]]; then
  echo "FAIL: set EGRESS_ADMIN_API_KEY (local only) or provide $REPO/deploy/.env.generated.local" >&2
  echo "Do not put the admin key on Cloud Run." >&2
  exit 1
fi

# Probe: GET worker (admin). 404 → need --from-peer PUT.
HTTP_PROBE="$(curl -sS -o /tmp/egress-get-worker.json -w '%{http_code}' \
  -A 'egress-register-skill/1.0' \
  -H "X-Api-Key: $ADMIN" \
  "$BASE/v1/workers/$WORKER_ID" || true)"
cp /tmp/egress-get-worker.json /tmp/egress-get-worker.$WORKER_ID.json 2>/dev/null || true

if [[ "$HTTP_PROBE" == "404" ]]; then
  if [[ -z "$FROM_PEER" ]]; then
    echo "FAIL: workerId=$WORKER_ID not registered. Re-run with --from-peer <existing-workerId> or register in the UI." >&2
    echo "Do not claim egress ready (Eventbrite: worker_not_found → 405/422 empty)." >&2
    exit 1
  fi
  PEER_HTTP="$(curl -sS -o /tmp/egress-peer.json -w '%{http_code}' \
    -A 'egress-register-skill/1.0' \
    -H "X-Api-Key: $ADMIN" \
    "$BASE/v1/workers/$FROM_PEER" || true)"
  [[ "$PEER_HTTP" == "200" ]] || { echo "FAIL: peer $FROM_PEER GET $PEER_HTTP" >&2; exit 1; }
  PUT_BODY="$(python3 - <<'PY'
import json
peer = json.load(open("/tmp/egress-peer.json", encoding="utf-8"))
policy = peer.get("policy") or {}
tags = list(peer.get("tags") or [])
if "scaffold" not in tags:
    tags.append("scaffold")
print(json.dumps({"policy": policy, "tags": tags}))
PY
)"
  PUT_HTTP="$(curl -sS -o /tmp/egress-put.json -w '%{http_code}' \
    -A 'egress-register-skill/1.0' \
    -X PUT \
    -H "X-Api-Key: $ADMIN" \
    -H 'content-type: application/json' \
    -d "$PUT_BODY" \
    "$BASE/v1/workers/$WORKER_ID" || true)"
  if [[ "$PUT_HTTP" != "200" && "$PUT_HTTP" != "201" ]]; then
    echo "FAIL: PUT /v1/workers/$WORKER_ID → $PUT_HTTP $(head -c 300 /tmp/egress-put.json)" >&2
    exit 1
  fi
  echo "OK registered workerId=$WORKER_ID from peer=$FROM_PEER"
elif [[ "$HTTP_PROBE" == "200" ]]; then
  echo "OK workerId=$WORKER_ID already registered"
else
  echo "FAIL: GET /v1/workers/$WORKER_ID → $HTTP_PROBE $(head -c 200 /tmp/egress-get-worker.json)" >&2
  exit 1
fi

KEY_HTTP="$(curl -sS -o /tmp/egress-runtime-key.json -w '%{http_code}' \
  -A 'egress-register-skill/1.0' \
  -H "X-Api-Key: $ADMIN" \
  "$BASE/v1/workers/$WORKER_ID/runtime-key" || true)"
[[ "$KEY_HTTP" == "200" ]] || { echo "FAIL: runtime-key $KEY_HTTP $(head -c 200 /tmp/egress-runtime-key.json)" >&2; exit 1; }

python3 - "$WORKER_ID" "$PRINT_KEY" <<'PY'
import json, sys
wid = sys.argv[1]
print_key = sys.argv[2] == "1"
data = json.load(open("/tmp/egress-runtime-key.json", encoding="utf-8"))
key = data.get("apiKey") or data.get("key") or data.get("runtimeKey") or ""
if not key:
    # common wrapper { "workerId", "apiKey" } — dump keys for debugging names only
    print("FAIL: runtime-key JSON missing apiKey; top-level keys: " + ",".join(data.keys()), file=sys.stderr)
    sys.exit(1)
print("Cloud Run env (runtime key, NOT admin, NOT fleet master):")
print(f"  EGRESS_CONTROL_BASE_URL=https://worker.opendata.best")
print(f"  EGRESS_CONTROL_WORKER_ID={wid}")
print("  EGRESS_CONTROL_CACHE_TTL=120")
if print_key:
    print(f"  EGRESS_CONTROL_API_KEY={key}")
else:
    print("  EGRESS_CONTROL_API_KEY=<pass --print-key to echo once; do not commit>")
print("Apply with --update-env-vars or --env-vars-file. NEVER --set-env-vars wipe.")
print("Actor must NOT call worker.opendata.best.")
PY
