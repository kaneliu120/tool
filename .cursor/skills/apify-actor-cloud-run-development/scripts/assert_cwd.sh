#!/usr/bin/env bash
# Fail if cwd (or DIR) is the wrong kind of project for the next command.
# Usage:
#   bash assert_cwd.sh worker [DIR]
#   bash assert_cwd.sh actor [DIR]
set -euo pipefail

KIND="${1:-}"
DIR="$(cd "${2:-.}" && pwd)"

usage() {
  echo "usage: $0 worker|actor [DIR]" >&2
  exit 2
}

[[ "$KIND" == "worker" || "$KIND" == "actor" ]] || usage

has_actor_json=0
[[ -f "$DIR/.actor/actor.json" ]] && has_actor_json=1
has_dockerfile=0
[[ -f "$DIR/Dockerfile" ]] && has_dockerfile=1

echo "assert_cwd kind=$KIND dir=$DIR dockerfile=$has_dockerfile actor_json=$has_actor_json"

if [[ "$KIND" == "worker" ]]; then
  if [[ "$has_actor_json" -eq 1 ]]; then
    echo "FAIL: $DIR looks like an Apify Actor (.actor/actor.json). Do not gcloud run deploy --source=. from here (Costco: ActorInput / exit 91 / PORT fail)." >&2
    exit 1
  fi
  if [[ "$has_dockerfile" -eq 0 ]]; then
    echo "FAIL: $DIR has no Dockerfile — not a Cloud Run worker root." >&2
    exit 1
  fi
  if [[ ! -d "$DIR/src" ]]; then
    echo "FAIL: $DIR has no src/ — not a worker root." >&2
    exit 1
  fi
  echo "OK worker cwd=$DIR service_guess=$(basename "$DIR")"
  exit 0
fi

if [[ "$has_actor_json" -eq 0 ]]; then
  echo "FAIL: $DIR has no .actor/actor.json — not an Apify Actor root. apify push from here is wrong." >&2
  exit 1
fi
echo "OK actor cwd=$DIR"
echo "NOTE: never gcloud run deploy --source=. from an Actor directory."
exit 0
