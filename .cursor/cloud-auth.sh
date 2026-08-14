#!/usr/bin/env bash
# Optional Cloud Agent auth from Runtime Secrets. Never prints secret values.
# Sourced by start.sh. Missing secrets are a no-op (gateway still starts).
# Expected secret names (cursor.com/dashboard/cloud-agents):
#   APIFY_TOKEN, GCP_SA_JSON, GCP_PROJECT, CLOUDFLARE_API_TOKEN,
#   VPS_SSH_KEY, VPS_SSH_HOST, VPS_SSH_USER

_cloud_auth_nvm_path() {
  local bin
  bin="$(ls -d "${HOME}/.nvm/versions/node"/v*/bin 2>/dev/null | sort -V | tail -1 || true)"
  if [[ -n "${bin}" ]]; then
    case ":$PATH:" in
      *":${bin}:"*) ;;
      *) export PATH="${bin}:$PATH" ;;
    esac
  fi
}

_cloud_auth_write_file() {
  local dest="$1"
  local value="$2"
  # Dashboard secrets often store PEM as a single line with \n escapes.
  if [[ "${value}" == *$'\n'* ]]; then
    printf '%s\n' "${value}" > "${dest}"
  else
    printf '%b\n' "${value}" > "${dest}"
  fi
  chmod 600 "${dest}"
}

_cloud_auth_gcp() {
  command -v gcloud >/dev/null 2>&1 || return 0
  [[ -n "${GCP_SA_JSON:-}" ]] || return 0
  mkdir -p "${HOME}/.config/gcloud"
  umask 077
  _cloud_auth_write_file "${HOME}/.config/gcloud/sa.json" "${GCP_SA_JSON}"
  gcloud auth activate-service-account --key-file="${HOME}/.config/gcloud/sa.json" --quiet \
    >/dev/null 2>&1 || return 0
  local project="${GCP_PROJECT:-}"
  if [[ -z "${project}" ]] && command -v python3 >/dev/null 2>&1; then
    project="$(python3 -c 'import json,pathlib; p=pathlib.Path.home()/".config/gcloud/sa.json"; print(json.loads(p.read_text()).get("project_id",""))' 2>/dev/null || true)"
  fi
  project="${project:-woker-260722}"
  gcloud config set project "${project}" --quiet >/dev/null 2>&1 || true
}

_cloud_auth_ssh() {
  [[ -n "${VPS_SSH_KEY:-}" ]] || return 0
  mkdir -p "${HOME}/.ssh"
  chmod 700 "${HOME}/.ssh"
  local key="${HOME}/.ssh/ovhcloud_ca_ed25519"
  _cloud_auth_write_file "${key}" "${VPS_SSH_KEY}"
  local host="${VPS_SSH_HOST:-}"
  local user="${VPS_SSH_USER:-ubuntu}"
  local cfg="${HOME}/.ssh/config"
  if [[ ! -f "${cfg}" ]] || ! grep -q '^Host vps-b85e86d3$' "${cfg}" 2>/dev/null; then
    {
      echo "Host vps-b85e86d3"
      if [[ -n "${host}" ]]; then
        echo "  HostName ${host}"
      fi
      echo "  User ${user}"
      echo "  IdentityFile ${key}"
      echo "  IdentitiesOnly yes"
      echo "  StrictHostKeyChecking accept-new"
    } >> "${cfg}"
    chmod 600 "${cfg}"
  fi
}

_cloud_auth_nvm_path || true
_cloud_auth_gcp || true
_cloud_auth_ssh || true
# APIFY_TOKEN and CLOUDFLARE_API_TOKEN are read from the environment by the CLIs.
true
