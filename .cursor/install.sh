#!/usr/bin/env bash
# Idempotent dependency refresh for the REA Kasada HTML Unblocker Toolkit.
# Safe to run repeatedly and against a warm cache.
set -euo pipefail

cd "$(dirname "$0")/.."

# The default image ships python3 but may lack the stdlib `venv`/`ensurepip`
# support needed to create a virtualenv. Install it only when missing.
if ! python3 -c "import venv, ensurepip" >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y python3-venv
fi

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e ".[dev]"
