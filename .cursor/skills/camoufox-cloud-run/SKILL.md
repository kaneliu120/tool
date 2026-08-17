---
name: camoufox-cloud-run
description: >-
  Run Camoufox (Firefox anti-detect) stably on Google Cloud Run without Bright
  Data. Use when a Camoufox Actor/worker fails on Cloud Run with TargetClosedError,
  Uncaught signal 11 / SIGSEGV, headless=virtual hangs, missing camoufox-bin,
  or when migrating a Camoufox Apify Actor into google run worker/* and peers
  previously abandoned Camoufox for Patchright.
---

# Camoufox on Cloud Run (proven recipe)

**Proven pair:** `google run worker/apartments-com` (revision with
`--execution-environment=gen2`) + Apify Actor Camoufox inheritance.
**Do not** default to Bright Data for this failure class — cost up, often still blocked.

## Symptom → root cause

| Symptom | Likely cause |
| --- | --- |
| `TargetClosedError: Browser.new_page` + `Uncaught signal: 11` | Cloud Run **gen1 / gVisor** killing Firefox; fix with **gen2** |
| Hang / silent fail / Fontconfig / profile errors | Unwritable `HOME` / missing `~/.camoufox` |
| `headless="virtual"` hang in Docker | Camoufox-managed Xvfb unreliable; use **external Xvfb + `headless=True`** |
| `hasBin=False` / seed empty | Camoufox **≥0.5** nests binary under `~/.cache/camoufox/browsers/official/<ver>/` |
| Whole container never binds `PORT` | Do **not** wrap CMD in `xvfb-run` (health check timeout) |
| Patchright works elsewhere but site Access Denied | Chrome ≠ Camoufox; keep Camoufox if Actor proved it |

Upstream refs: [daijro/camoufox#572](https://github.com/daijro/camoufox/issues/572), [#372](https://github.com/daijro/camoufox/issues/372), [#44](https://github.com/daijro/camoufox/issues/44), [openlegion#156](https://github.com/openlegion-ai/openlegion/pull/156).

## Mandatory checklist (in order)

```
- [ ] 1. Deploy Cloud Run with --execution-environment=gen2
- [ ] 2. HOME=/tmp + pre-create ~/.camoufox + fontconfig caches
- [ ] 3. Build-time camoufox fetch → seed /opt/camoufox (full tree)
- [ ] 4. Entrypoint copies seed → $HOME/.cache/camoufox (nested OK)
- [ ] 5. External Xvfb :99 1920x1080x24 in-process; headless=True first
- [ ] 6. LIBGL_ALWAYS_SOFTWARE=1; optional MOZ_DISABLE_*_SANDBOX=1
- [ ] 7. Bind PORT with plain python -m src (lazy-import browser)
- [ ] 8. Smoke: /health 200, search 401 without key, authenticated items≥1
```

## 1. Cloud Run deploy flags

```bash
gcloud run deploy <service> \
  --project=woker-260722 \
  --region=<geo> \
  --source=. \
  --allow-unauthenticated \
  --execution-environment=gen2 \
  --memory=4Gi \
  --cpu=2 \
  --timeout=900 \
  --concurrency=1 \
  --cpu-boost \
  --env-vars-file=/tmp/<service>-env.yaml
```

Env (no Bright Data required):

```yaml
SCRAPE_PROVIDER: "camoufox"
ALLOW_CAMOUFOX: "1"
HOME: "/tmp"
LIBGL_ALWAYS_SOFTWARE: "1"
WORKER_API_KEY: "..."
PROXY_URL: "http://groups-RESIDENTIAL,country-<CC>:...@proxy.apify.com:8000"
```

**gen1 → signal 11** was the apartments-com blocker even after HOME/Xvfb hardening.
**gen2** made Camoufox smoke succeed (`items≥1`, `provider=camoufox`).

## 2. Writable HOME + seed (Camoufox 0.5.x layout)

Build with `HOME=/root`, fetch, copy entire cache tree to `/opt/camoufox`:

```dockerfile
ENV HOME=/root
RUN pip install -r requirements.txt \
    && (python -m playwright install-deps || true) \
    && python -m camoufox fetch \
    && mkdir -p /opt/camoufox /root/.camoufox \
    && cp -a /root/.cache/camoufox/. /opt/camoufox/ \
    && BIN="$(find /opt/camoufox -type f -name camoufox-bin | head -n 1)" \
    && test -n "$BIN"

ENV HOME=/tmp
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV MOZ_DISABLE_RDD_SANDBOX=1
ENV MOZ_DISABLE_CONTENT_SANDBOX=1
CMD ["/app/entrypoint.sh"]
```

Entrypoint (do **not** use `xvfb-run` around the HTTP server):

```bash
#!/usr/bin/env bash
set -euo pipefail
export HOME="${HOME:-/tmp}"
mkdir -p "${HOME}/.camoufox" "${HOME}/.cache/camoufox" \
  "${HOME}/.cache/fontconfig" "${HOME}/.fontconfig"
if [[ -d /opt/camoufox && ! -e "${HOME}/.cache/camoufox/camoufox-bin" ]]; then
  # 0.5.x: binary may only exist under browsers/official/...
  if ! find "${HOME}/.cache/camoufox" -name camoufox-bin | grep -q .; then
    cp -a /opt/camoufox/. "${HOME}/.cache/camoufox/"
  fi
fi
exec python -m src
```

Runtime prep must **rglob** `camoufox-bin` (not only top-level).

## 3. Display: external Xvfb + headless=True

```text
prepare HOME/caches
→ start Xvfb :99 -screen 0 1920x1080x24 (keep process; set DISPLAY)
→ AsyncCamoufox(headless=True, geoip=True, proxy=...)
→ fallback headless="virtual" only if True fails
```

- Start Xvfb **inside** the scrape path (or once per process), never as the sole CMD wrapper.
- Clear stale `DISPLAY` if `/tmp/.X11-unix/X99` is missing.
- Clean `/tmp/.X99-lock` when orphaned.

## 4. System packages

Debian slim minimum (expand as needed):

`libgtk-3-0 libx11-xcb1 libasound2 libdbus-glib-1-2 libxt6` + fonts + `xvfb xauth`
(+ other Playwright/Firefox shared libs already used in apartments-com Dockerfile).

Prefer build-time `playwright install-deps` so runtime does not re-download.

## 5. Proxy

Keep Actor Apify **RESIDENTIAL** → `proxyUrl` (site geography country).
Worker: prefer body `proxyUrl`; if URL contains `apify_actor_run`, fall back to `PROXY_URL`.

## 6. Anti-patterns

| Don't | Do instead |
| --- | --- |
| Default Bright Data because Camoufox "doesn't work on GCP" | Fix gen2 + HOME + Xvfb first |
| `CMD ["xvfb-run", ..., "python", "-m", "src"]` | In-process Xvfb; plain `python -m src` for PORT |
| Assume binary at `~/.cache/camoufox/camoufox-bin` only | `find … -name camoufox-bin` / rglob |
| Abandon Camoufox for Patchright when Actor was Camoufox-only | Measure; Chrome often Akamai Access Denied |
| Set stale `DISPLAY=:99` in Dockerfile without Xvfb | Set DISPLAY only after Xvfb is up |

## Smoke gates

1. `GET /health` → 200  
2. `POST /v1/search` without key → **401**  
3. Authenticated small search → 200 + `items.length >= 1` + `provider=camoufox`  
4. Logs show `hasBin=True`, `Xvfb started`, **no** `Uncaught signal: 11`

## Reference implementation

- Worker: `/Users/kane/Projects/google run worker/apartments-com/`
  - `Dockerfile`, `entrypoint.sh`, `src/runtime_env.py`, `src/camoufox_engine.py`
- Parent skill: [`apify-actor-cloud-run-development`](../apify-actor-cloud-run-development/SKILL.md) (engines + migrate branches). Legacy redirects: `cloud-run-apify-actor`, `migrate-apify-actor-worker`.
- Longer notes: [reference.md](reference.md)
