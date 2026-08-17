#!/usr/bin/env bash
# Three-UA HTTP contrast for website-page-research Phase 0.
# Usage: bash http_contrast.sh 'https://example.com/path'
# Prints status, server, cf-ray, bytes, and whether hydration/listing tokens appear.
# Does not dump bodies. Not a scraper.
set -euo pipefail

URL="${1:-}"
if [[ -z "$URL" ]]; then
  echo "usage: $0 URL" >&2
  exit 2
fi

UA_PY='python-requests/2.31.0'
UA_CURL='curl/8.7.1'
UA_CHROME='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

probe() {
  local label="$1"
  local ua="$2"
  local tmp
  tmp="$(mktemp)"
  local hdr
  hdr="$(mktemp)"
  local code
  code="$(curl -sS -L --max-time 25 -A "$ua" -D "$hdr" -o "$tmp" -w '%{http_code}' "$URL" || echo "000")"
  local bytes
  bytes="$(wc -c < "$tmp" | tr -d ' ')"
  local server
  server="$(grep -i '^server:' "$hdr" | tail -n1 | tr -d '\r' || true)"
  local cfray
  cfray="$(grep -i '^cf-ray:' "$hdr" | tail -n1 | tr -d '\r' || true)"
  local mitigated
  mitigated="$(grep -i '^cf-mitigated:' "$hdr" | tail -n1 | tr -d '\r' || true)"
  local tokens=""
  for tok in __NEXT_DATA__ __next_f itemid edpData application/ld+json challenge cf-browser-verification; do
    if grep -q -- "$tok" "$tmp" 2>/dev/null; then
      tokens="${tokens}${tok},"
    fi
  done
  printf '%s\t%s\t%s\t%s\t%s\t%s\ttokens=%s\n' \
    "$label" "$code" "$bytes" "${server:-server:}" "${cfray:-cf-ray:}" "${mitigated:-cf-mitigated:}" "${tokens:-none}"
  rm -f "$tmp" "$hdr"
}

echo "url	$URL"
probe "python-requests-like" "$UA_PY"
probe "curl" "$UA_CURL"
probe "chrome-ua" "$UA_CHROME"
