# AGENTS.md

## Cursor Cloud specific instructions

This VM cannot use macOS Keychain or `ssh -N mem0` to `localhost:8888`. Kane's Mem0 REST/Dashboard stay private; **public ingress is MCP only**.

### Call the memory system

1. Public health (no key): `python3 scripts/mem0ctl.py health`
2. Authenticated search/add needs **`MEM0_API_KEY`** (user REST/MCP key, not the admin `/configure` key).
3. Default scope: `user_id=kane`. Do **not** use stdlib `urllib` against the public host (Cloudflare 1010). Use `mem0ctl` / `httpx` / `curl`.
4. Do **not** use the official `mem0ai` Python client against this self-hosted stack.
5. Never commit API keys, Atlas URIs, or NVIDIA/Voyage tokens.

```bash
# no auth — system python3 re-execs into .venv when httpx is missing
python3 scripts/mem0ctl.py health

# requires MEM0_API_KEY in the Cloud Agent secret store
python3 scripts/mem0ctl.py search "hiking Taipei"
python3 scripts/mem0ctl.py add --raw "handoff note"
python3 scripts/mem0ctl.py list
python3 scripts/mem0ctl.py handoff \
  --project 'tool' \
  --verdict '一句话结论' \
  --done '做了什么' \
  --status '当前真实状态' \
  --gotchas '无' \
  --next '下一步' \
  --evidence '路径/命令'
```

Python:

```python
from mem0_client import Mem0Client
with Mem0Client() as mem0:
    mem0.health()
    mem0.search("Kane 怎么部署", top_k=5)
```

### Secrets and MCP this agent cannot set itself

- **Runtime Secret** `MEM0_API_KEY` at [cursor.com/dashboard/cloud-agents](https://cursor.com/dashboard/cloud-agents) — injected as a VM env var so `mem0ctl` works. Restart the agent after adding it.
- **HTTP MCP** named `mem0-selfhost` at [cursor.com/agents](https://cursor.com/agents) (Cloud Agents do not load `.cursor/mcp.json`):
  - URL: `https://mem0-mcp.opendata.best/mcp`
  - Headers: `Authorization: Bearer <MEM0_API_KEY>` and `X-API-Key: <MEM0_API_KEY>`
  - Transport must be HTTP (not SSE).

Optional env: `MEM0_MCP_URL` (default `https://mem0-mcp.opendata.best`), `MEM0_USER_ID` (default `kane`), `MEM0_REST_URL` (only if an SSH tunnel to REST `:8888` exists).

Local Cursor IDE can use `.cursor/mcp.json` with `${env:MEM0_API_KEY}`.

## Skills / hooks / rules copied from Kane's Mac

Cloud Agents **do not** load `~/.cursor/` from the laptop. This repo checkout is the source.

### Skills (`.cursor/skills/`)

Cloud Agents **often do not inject** project skills into the available-skills list
(plugin / Cursor built-ins still appear). Treat the table as the catalog and
**Read** the `SKILL.md` when the task matches. Always-apply rule:
`.cursor/rules/project-skills.mdc`.

| Skill | Cloud |
|---|---|
| `mem0-selfhost` | Yes — use `scripts/mem0ctl.py` + HTTP MCP |
| `apify-actor-cloud-run-development` (+ redirects) | Yes as methodology; Kane's `~/Projects/google run worker` paths are **not** on this VM |
| `apify-publish-tasks` | Yes; Console publish needs a browser (VM desktop, not Mac Chrome) |
| `bright-data-riskbypass` / `camoufox-cloud-run` | Yes as docs |
| `website-page-research` | Phase 0 `http_contrast.sh`; Phase 1 `playwright_page_probe.py` + system Chrome. No AppleScript |
| `reverse-skill` | Router only — full pack not in this clone |
| `use-my-browser` | **Stub only** — do not `osascript` |

Skipped: `harvest-transcripts` (Mac agent-transcripts). Built-in `~/.cursor/skills-cursor/` is provided by Cursor, not copied.

### Hooks (`.cursor/hooks.json`)

Command hooks only, after the VM is writable:

- `beforeSubmitPrompt` → `.cursor/hooks/mem0_before_prompt.py`
- `stop` → `.cursor/hooks/mem0_stop_handoff.py` (follow-up uses `python3 scripts/mem0ctl.py`)
- `preCompact` → `.cursor/hooks/mem0_precompact.py`

**Not on Cloud:** `sessionStart`, `sessionEnd`, prompt-based hooks, Tab hooks, MCP execution hooks. Mem0 recall at start comes from always-apply rule `mem0-mandatory.mdc` + this file. The **first** Cloud prompt can be submitted while the VM is still read-only, so `beforeSubmitPrompt` may not run for that message — later turns do.

Command hooks are invoked as `python3 .cursor/hooks/…` from the **repo root**. They only need the stdlib. `mem0ctl` (used by the stop follow-up) re-execs `.venv` so system `python3` works after `install`.

### Rules (`.cursor/rules/*.mdc`, alwaysApply)

- `mem0-mandatory.mdc`
- `project-skills.mdc`
- `apify-actor-cloud-run-development.mdc`
- `apify-cloud-smoke-random.mdc`
- `apify-publish-tasks.mdc`

User Rules in Cursor Settings still apply to Cloud sessions (account-level). Team dashboard rules apply if configured.

### What you still configure in the Dashboard (not git)

1. Runtime Secret `MEM0_API_KEY` (MCP/REST; not a vendor CLI login)
2. HTTP MCP `mem0-selfhost` on [cursor.com/agents](https://cursor.com/agents)
3. Re-open a **new** Cloud Agent on this branch after push — existing runs will not pick up new git files until they clone this revision.

**Vendor CLI login is parked until Kane asks.** Do not start `gcloud` / `apify` / `cf` / `wrangler` OAuth on this VM, and do not install or log those CLIs in on the bastion unattended. Overlay (Mac + Cloud Agent + OVH `vps-b85e86d3`) plus Mesh SSH is enough for operator reachability. `MEM0_API_KEY` stays a Dashboard secret because public MCP has no overlay yet.

Validate this checkout:

```bash
python3 scripts/check_cursor_agent_config.py
```

## Cloud Agent runtime (this Ubuntu VM)

Repo-managed config: `.cursor/environment.json`.

| Phase | Script | Role |
|---|---|---|
| `install` | `./.cursor/install.sh` | `python3-venv` if missing; Docker CLI; `gcloud` / `apify` / `cf` / `wrangler` if missing; `rsync`/`jq`; `.venv`; `pip install -e ".[dev,recon]"` (Playwright + `curl_cffi`) |
| `start` | `./.cursor/start.sh` | Optional secret activation via `cloud-auth.sh`; idempotent mock gateway on `:8080`, then **returns**; sets `DOCKER_HOST` when Engine is on `:2375` |
| `terminals` | `./.cursor/start.sh --attach` | Same gateway; tails `/tmp/rea-gateway.log` |

This Cloud image often **does not** auto-start `terminals`. Rely on `start`, or run `./.cursor/start.sh` yourself.

The VM exposes Docker Engine on `tcp://127.0.0.1:2375` **without** `/var/run/docker.sock`. After `install.sh`, use:

```bash
export DOCKER_HOST="${DOCKER_HOST:-tcp://127.0.0.1:2375}"
docker version
docker compose version
docker buildx version
```

Do **not** start a second nested `dockerd` when `:2375` already answers.

### Operator private network (Cloudflare Mesh)

Mac + two OVH boxes are already Mesh peers (Mac `100.96.0.2`, camoufox-worker-01 `.1`, bastion `vps-b85e86d3` `.3`). Data-plane `cloudflared` tunnels stay public. **Do not `warp-cli connect` on a Cloud Agent until settings are TunnelOnly + Include `100.96.0.0/12`.** Default client settings are Mode Warp + Exclude `100.64.0.0/10` (swallows Mesh and can steal the default route). Guard: `python3 .cursor/warp_mesh_guard.py`.

This image often has `/dev/net/tun` but unprivileged `TUNSETIFF` is EPERM; `sudo` works. `warp-svc` is not systemd PID 1 — start it in tmux (`sudo warp-svc`). Enroll org `opendata-best` at `https://opendata-best.cloudflareaccess.com/warp` **on this VM’s Computer** (Mac browser enrolls the Mac, not the agent). After registration: `warp-cli --accept-tos settings | python3 .cursor/warp_mesh_guard.py`, then `warp-cli --accept-tos connect`. Default route must stay on `eth0`.

Overlay SSH to the bastion is verified: `ssh vps-b85e86d3-mesh` (Host alias, `IdentitiesOnly` + `IdentityFile ~/.ssh/ovhcloud_ca_ed25519`, key comment `cursor-cloud-bc-6b19916e`). Naked `ssh ubuntu@100.96.0.3` without `-i` fails because it never offers that key. Access SSH is not published; public `:22` remains a fallback. This VM’s pubkey is **not** on camoufox-worker-01.

Vendor CLI login on the bastion is **parked**. The bastion currently has Docker + `cloudflared` on PATH, but **not** `gcloud` / `apify` / `cf` / `wrangler`. Next Cloud Agent work on this VM should use the repo (gateway, pytest, Docker `:2375`, Mesh SSH), not vendor consoles.

`.cursor/cloud-auth.sh` remains a no-op fallback if env vars happen to exist; it is **not** the intended Cloud login path.

### Ready for the next task (this run)

Leave `rea-gateway` and `warp-svc` running. Do not `warp-cli disconnect`. Do not close bastion `:22`.

| Check | Expected |
|---|---|
| `curl -sS http://127.0.0.1:8080/healthz` | `{"ok":true,"providers":["mock_fixture"]}` |
| `DOCKER_HOST=tcp://127.0.0.1:2375 docker version` | client + server |
| `ssh vps-b85e86d3-mesh hostname` | `vps-b85e86d3` |
| `python3 scripts/check_cursor_agent_config.py` | `"ok": true` |

```bash
./.cursor/start.sh
curl -sS http://127.0.0.1:8080/healthz
.venv/bin/python scripts/test_html_provider.py --provider mock_fixture
.venv/bin/python scripts/run_canary_local.py
.venv/bin/pytest -q
```

`GET /healthz` with `REA_INCLUDE_MOCK=1` includes `mock_fixture`. Live REA HTML still needs the Mac Chrome runner (`REA_MAC_RUNNER_URL`); do not default to Apify Xvfb. Google Chrome on this image is the **page-recon** browser (`playwright_page_probe.py` `channel=chrome`), not the REA Kasada HTML provider.

### Page recon + Actor/worker toolchain (this VM)

| Need | Cloud Agent |
|---|---|
| Phase 0 HTTP contrast | `bash .cursor/skills/website-page-research/scripts/http_contrast.sh URL` |
| Phase 1 page probe | `.venv/bin/python .cursor/skills/website-page-research/scripts/playwright_page_probe.py --url URL --js generic` |
| Inventory | `python3 scripts/check_recon_actor_env.py` |
| Thin Actor / worker factory | Skill scripts under `.cursor/skills/apify-actor-cloud-run-development/scripts/` |
| `~/Projects/google run worker` and `~/Projects/Apify Actors` | **Present on this VM** (2026-08-17): Apify `apify pull` 109 Actors + Cloud Run `build-source-location` zips 103 workers. **Not** a GitHub clone. Refresh: `python3 scripts/pull_actor_worker_peers.py` |
| `gcloud` deploy (`woker-260722`) | User login **done** as `kaneliu10@gmail.com`; project `woker-260722`. Not ADC. Do not start another OAuth unless Kane asks |
| Camoufox / Patchright worker runtimes | Not installed on the Agent snapshot (worker image / Mac worker repo) |

Do **not** claim Mac Chrome recon works here. Do **not** install Camoufox into this Cloud snapshot. Random Apify smoke still uses `random_smoke_input.py` — never README prefills.

### Worker / Actor peer trees

`scaffold_worker.sh` / `scaffold_actor.sh` default roots:

- `$HOME/Projects/google run worker/<peer>/`
- `$HOME/Projects/Apify Actors/<peer>/`

**This VM (2026-08-17):** downloaded from Apify + GCP, not GitHub.

```bash
python3 scripts/pull_actor_worker_peers.py
# 109 Actors (105 have src/worker_client.py), 103 Cloud Run source zips
# assert_cwd worker zillow-com / apartments-com / bayt-com — OK
# assert_cwd actor zillow-group-scraper / walmart-scraper — OK
```

GitHub `kaneliu120/actor.git` is still **404** to this Agent’s GitHub App (installation only has `tool`). Do not call the HOME trees a git clone. Per-service Cloud Run zips omit `_shared/`; `scripts/pull_actor_worker_peers.py` **recovers** `_shared/` from copies already in worker `src/` (donor `airbnb-com`) and writes `sync_shared.sh`. That recovery is **not** Kane’s Mac git original — replace it if the laptop tree differs.

Verified peers: `zillow-com` (http), `apartments-com` (camoufox), `bayt-com` (patchright), `zillow-group-scraper` (thin Actor). There is no live Apify actor named `zillow-scraper`; the factory peer on this account is `zillow-group-scraper`. Not-thin Apify pulls (no `src/worker_client.py`): `booking-airbnb-scraper`, `craigslist-housing-scraper`, `phone-number-intelligence`, `us-real-estate-scraper`.
