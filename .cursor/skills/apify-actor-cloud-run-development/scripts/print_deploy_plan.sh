#!/usr/bin/env bash
# Print a deploy plan (no secret values). Does not deploy.
# Usage: bash print_deploy_plan.sh [--region REGION] [--env-file PATH] [DIR]
set -euo pipefail

REGION=""
ENV_FILE=""
DIR="."
while [[ $# -gt 0 ]]; do
  case "$1" in
    --region) REGION="${2:-}"; shift 2 ;;
    --env-file) ENV_FILE="${2:-}"; shift 2 ;;
    --help|-h) echo "usage: $0 [--region REGION] [--env-file PATH] [DIR]" >&2; exit 2 ;;
    *) DIR="$1"; shift ;;
  esac
done

DIR="$(cd "$DIR" && pwd)"
SERVICE="$(basename "$DIR")"
HAS_ACTOR=0
[[ -f "$DIR/.actor/actor.json" ]] && HAS_ACTOR=1

echo "dir=$DIR"
echo "basename=$SERVICE"
if [[ "$HAS_ACTOR" -eq 1 ]]; then
  echo "detected=actor"
  echo "FORBIDDEN: gcloud run deploy --source=. from this directory"
  echo "next: bash $(dirname "$0")/assert_cwd.sh actor \"$DIR\" && apify push"
  exit 0
fi

echo "detected=worker"
echo "service=$SERVICE"
echo "region=${REGION:-<set --region from site geography; immutable once deployed>}"
echo "project=woker-260722"
echo "flags: --source=. --allow-unauthenticated --memory=2Gi --cpu=2 --timeout=900 --concurrency=1 --min-instances=0 --max-instances=2"
echo "env: first deploy = --env-vars-file (complete). later = --update-env-vars additive."
echo "FORBIDDEN: --set-env-vars (wipes EGRESS_CONTROL_* / PROXY_URL / WORKER_API_KEY)"
echo "comma-in-value (Apify proxy user): --env-vars-file only, never --update-env-vars"

if [[ -n "$ENV_FILE" ]]; then
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "FAIL: env file missing: $ENV_FILE" >&2
    exit 1
  fi
  echo "env_file=$ENV_FILE keys:"
  # Print keys only (YAML KEY: or KEY=). Never values.
  python3 - "$ENV_FILE" <<'PY'
import re, sys
path = sys.argv[1]
keys = []
for line in open(path, encoding="utf-8"):
    s = line.strip()
    if not s or s.startswith("#"):
        continue
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*[:=]", s)
    if m:
        keys.append(m.group(1))
print("  " + " ".join(keys) if keys else "  (no keys parsed)")
need = ["WORKER_API_KEY", "EGRESS_CONTROL_BASE_URL", "EGRESS_CONTROL_API_KEY", "EGRESS_CONTROL_WORKER_ID"]
missing = [k for k in need if k not in keys]
if missing:
    print("WARN missing recommended keys: " + " ".join(missing))
PY
fi

echo "preflight: bash $(dirname "$0")/assert_cwd.sh worker \"$DIR\""
echo "register:  bash $(dirname "$0")/register_egress_worker.sh $SERVICE --from-peer <peer>"
echo "smoke:     bash $(dirname "$0")/worker_triple_smoke.sh"
