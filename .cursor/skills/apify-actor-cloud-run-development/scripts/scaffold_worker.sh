#!/usr/bin/env bash
# Copy worker *infra* from a peer, then sync_shared. Does not rewrite parse for you.
# Usage:
#   bash scaffold_worker.sh <peer> <dest> [--force]
# Example:
#   bash scaffold_worker.sh zillow-com example-com
set -euo pipefail

ROOT="${WORKERS_ROOT:-$HOME/Projects/google run worker}"
PEER="${1:-}"
DEST="${2:-}"
FORCE=0
[[ "${3:-}" == "--force" ]] && FORCE=1

usage() {
  echo "usage: $0 <peer-worker> <dest-worker> [--force]" >&2
  echo "peers by engine: zillow-com/glassdoor-com (http) | apartments-com (camoufox) | bayt-com/linkedin-com/walmart-com (patchright)" >&2
  exit 2
}

[[ -n "$PEER" && -n "$DEST" ]] || usage
[[ "$PEER" != "$DEST" ]] || { echo "FAIL: peer and dest are the same" >&2; exit 1; }

SRC="$ROOT/$PEER"
OUT="$ROOT/$DEST"
[[ -d "$SRC/src" && -f "$SRC/Dockerfile" ]] || { echo "FAIL: peer is not a worker: $SRC" >&2; exit 1; }
if [[ -e "$OUT" && "$FORCE" -ne 1 ]]; then
  echo "FAIL: dest exists: $OUT (pass --force to rsync into it)" >&2
  exit 1
fi

mkdir -p "$OUT"
rsync -a --delete-excluded \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '.git/' \
  --exclude '.env' \
  --exclude '.env.*' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache/' \
  --exclude 'node_modules/' \
  --exclude '.DS_Store' \
  --exclude '*.log' \
  --exclude 'storage/' \
  "$SRC/" "$OUT/"

if [[ -x "$ROOT/_shared/sync_shared.sh" ]]; then
  "$ROOT/_shared/sync_shared.sh" "$DEST"
else
  echo "WARN: missing $ROOT/_shared/sync_shared.sh — copy egress client manually" >&2
fi

echo "OK scaffolded $OUT from $PEER"
echo "REWRITE (do not keep peer selectors): collector/parse/wait/markets/ready-signals"
echo "COPY as-is: auth.py, OpenAPI, envelope, apply_runtime_env call sites"
echo "Next:"
echo "  1. Paste templates/worker-contract.md → $OUT/docs/worker-contract.md"
echo "  2. Fill coverage matrix; empty = 未验证"
echo "  3. bash $(dirname "$0")/assert_cwd.sh worker \"$OUT\""
echo "  4. bash $(dirname "$0")/register_egress_worker.sh $DEST --from-peer $PEER"
echo "See templates/copy-vs-rewrite.md"
