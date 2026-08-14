#!/usr/bin/env bash
# Idempotent dependency refresh for the REA Kasada HTML Unblocker Toolkit.
# Safe to run repeatedly and against a warm cache.
set -euo pipefail

cd "$(dirname "$0")/.."

# The default image ships python3 but may lack the stdlib `venv`/`ensurepip`
# support needed to create a virtualenv. Install it only when missing.
if ! python3 -c "import venv, ensurepip" >/dev/null 2>&1; then
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv
fi

# Docker Engine is often already listening on TCP :2375 on Cloud VMs, but the
# image has no CLI and no docker.sock. Install CLI + compose + buildx only.
if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    docker.io docker-compose-v2 docker-buildx
fi

# Prefer the host Engine on :2375 over a nested dockerd (this image has no sock).
if [[ ! -S /var/run/docker.sock ]] \
  && curl -sf --max-time 2 http://127.0.0.1:2375/version >/dev/null 2>&1; then
  sudo systemctl disable --now docker.service docker.socket >/dev/null 2>&1 || true
  export DOCKER_HOST="${DOCKER_HOST:-tcp://127.0.0.1:2375}"
  sudo tee /etc/profile.d/cursor-docker-host.sh >/dev/null <<'EOF'
# Cursor Cloud: Engine listens on TCP 2375; this image has no docker.sock.
if [ ! -S /var/run/docker.sock ]; then
  export DOCKER_HOST="${DOCKER_HOST:-tcp://127.0.0.1:2375}"
fi
EOF
  if [[ -f "${HOME}/.bashrc" ]] && ! grep -q 'DOCKER_HOST=tcp://127.0.0.1:2375' "${HOME}/.bashrc"; then
    printf '\n# Cursor Cloud Docker Engine (no unix socket)\nexport DOCKER_HOST="${DOCKER_HOST:-tcp://127.0.0.1:2375}"\n' >> "${HOME}/.bashrc"
  fi
fi

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e ".[dev]"
