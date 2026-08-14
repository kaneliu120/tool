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

# nvm Node (apify / cf / wrangler). Cloud image ships nvm at ~/.nvm.
if [[ -d "${HOME}/.nvm/versions/node" ]]; then
  NODE_BIN="$(ls -d "${HOME}/.nvm/versions/node"/v*/bin 2>/dev/null | sort -V | tail -1 || true)"
  if [[ -n "${NODE_BIN}" ]]; then
    export PATH="${NODE_BIN}:${PATH}"
    if [[ -f "${HOME}/.bashrc" ]] && ! grep -q 'CURSOR_NVM_NODE_PATH' "${HOME}/.bashrc"; then
      cat >> "${HOME}/.bashrc" << 'EOF'
# CURSOR_NVM_NODE_PATH
if [ -d "$HOME/.nvm/versions/node" ]; then
  _cursor_nvm_bin="$(ls -d "$HOME/.nvm/versions/node"/v*/bin 2>/dev/null | sort -V | tail -1 || true)"
  if [ -n "$_cursor_nvm_bin" ]; then
    case ":$PATH:" in *":$_cursor_nvm_bin:"*) ;; *) export PATH="$_cursor_nvm_bin:$PATH" ;; esac
  fi
  unset _cursor_nvm_bin
fi
EOF
    fi
  fi
fi

if ! command -v gcloud >/dev/null 2>&1; then
  curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
    | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list >/dev/null
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y google-cloud-cli
fi

if command -v npm >/dev/null 2>&1; then
  command -v apify >/dev/null 2>&1 || npm install -g apify-cli
  command -v cf >/dev/null 2>&1 || npm install -g cf
  command -v wrangler >/dev/null 2>&1 || npm install -g wrangler
fi

# Cloudflare Access client. Do not apt-install cloudflare-warp here: this
# image is not systemd PID 1, and naked warp-cli connect can steal the
# default route. Mesh join is manual (see AGENTS.md).
if ! command -v cloudflared >/dev/null 2>&1; then
  curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -o /tmp/cloudflared
  sudo install -m 755 /tmp/cloudflared /usr/local/bin/cloudflared
fi

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e ".[dev]"
