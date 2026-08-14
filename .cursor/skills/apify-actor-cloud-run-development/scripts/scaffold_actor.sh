#!/usr/bin/env bash
# Copy thin-Actor *factory* from a peer. Change input fields / SEO; do not add scrape.
# Usage:
#   bash scaffold_actor.sh <peer-actor-dir-name> <dest-actor-dir-name> [--force]
# Example:
#   bash scaffold_actor.sh zillow-scraper example-scraper
set -euo pipefail

ROOT="${ACTORS_ROOT:-$HOME/Projects/Apify Actors}"
PEER="${1:-}"
DEST="${2:-}"
FORCE=0
[[ "${3:-}" == "--force" ]] && FORCE=1

usage() {
  echo "usage: $0 <peer-actor> <dest-actor> [--force]" >&2
  exit 2
}

[[ -n "$PEER" && -n "$DEST" ]] || usage
[[ "$PEER" != "$DEST" ]] || { echo "FAIL: peer and dest are the same" >&2; exit 1; }

SRC="$ROOT/$PEER"
OUT="$ROOT/$DEST"
[[ -f "$SRC/.actor/actor.json" ]] || { echo "FAIL: peer is not an Actor: $SRC" >&2; exit 1; }
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
  --exclude 'storage/' \
  --exclude '.apify/' \
  --exclude '*.pyc' \
  --exclude '.DS_Store' \
  "$SRC/" "$OUT/"

echo "OK scaffolded $OUT from $PEER"
echo "CHANGE: .actor/actor.json name/title, input_schema field names, README SEO, coverage enums"
echo "KEEP: worker_client auth, 1024 MB, Standby, free_tier, WORKER_PROVIDES_PROXY=1"
echo "MUST NOT exist: browser, unlock, egress-control client"
echo "Schema: every REQUIRED field needs default (= prefill) or be optional; empty {} SUCCEEDED"
echo "Next: bash $(dirname "$0")/assert_cwd.sh actor \"$OUT\""
echo "See templates/copy-vs-rewrite.md"
