#!/usr/bin/env bash
# Worker triple smoke: /health 200, scrape 401/403 without key, auth rows >= 1.
# Usage:
#   WORKER_URL=https://….run.app WORKER_API_KEY=… SEARCH_JSON=/tmp/accept.json \
#     bash worker_triple_smoke.sh
# Optional: SEARCH_PATH=/v1/search (default)
set -euo pipefail

WORKER_URL="${WORKER_URL:-}"
WORKER_API_KEY="${WORKER_API_KEY:-}"
SEARCH_JSON="${SEARCH_JSON:-}"
SEARCH_PATH="${SEARCH_PATH:-/v1/search}"

fail() { echo "FAIL: $*" >&2; exit 1; }

[[ -n "$WORKER_URL" ]] || fail "set WORKER_URL"
[[ -n "$WORKER_API_KEY" ]] || fail "set WORKER_API_KEY"
[[ -n "$SEARCH_JSON" && -f "$SEARCH_JSON" ]] || fail "set SEARCH_JSON to an existing file (random_smoke_input.py --out)"
[[ "$WORKER_URL" == https://* ]] || fail "WORKER_URL must be https://"

WORKER_URL="${WORKER_URL%/}"
BODY="$(cat "$SEARCH_JSON")"

echo "triple_smoke url=$WORKER_URL path=$SEARCH_PATH input=$SEARCH_JSON"

code_health="$(curl -sS -o /tmp/worker-health.body -w '%{http_code}' --max-time 30 "$WORKER_URL/health" || true)"
[[ "$code_health" == "200" ]] || fail "/health expected 200 got $code_health"
echo "OK /health 200"

code_unauth="$(curl -sS -o /tmp/worker-unauth.body -w '%{http_code}' --max-time 60 \
  -X POST "$WORKER_URL$SEARCH_PATH" \
  -H 'content-type: application/json' \
  -d "$BODY" || true)"
if [[ "$code_unauth" != "401" && "$code_unauth" != "403" ]]; then
  fail "unauth $SEARCH_PATH expected 401 or 403 got $code_unauth (body $(head -c 200 /tmp/worker-unauth.body))"
fi
echo "OK unauth $code_unauth"

code_auth="$(curl -sS -o /tmp/worker-auth.body -w '%{http_code}' --max-time 180 \
  -X POST "$WORKER_URL$SEARCH_PATH" \
  -H 'content-type: application/json' \
  -H "Authorization: Bearer $WORKER_API_KEY" \
  -H "X-Api-Key: $WORKER_API_KEY" \
  -d "$BODY" || true)"
[[ "$code_auth" == "200" ]] || fail "auth $SEARCH_PATH expected 200 got $code_auth (body $(head -c 400 /tmp/worker-auth.body))"

python3 - <<'PY'
import json, sys
raw = open("/tmp/worker-auth.body", encoding="utf-8").read()
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    print("FAIL: auth body is not JSON", file=sys.stderr)
    sys.exit(1)
items = data.get("items")
if items is None:
    items = data.get("results") or []
n = len(items) if isinstance(items, list) else 0
status = data.get("status")
print(f"auth status={status!r} items={n} provider={data.get('provider')!r} worker={data.get('worker')!r}")
if n < 1:
    print("FAIL: items.length < 1 — do not claim ready (unregistered workerId, bad params, or no rows). Re-roll input; do not fall back to README.", file=sys.stderr)
    sys.exit(1)
PY

echo "OK triple smoke (health + unauth + auth rows>=1)"
echo "evidence: /tmp/worker-health.body /tmp/worker-unauth.body /tmp/worker-auth.body"
