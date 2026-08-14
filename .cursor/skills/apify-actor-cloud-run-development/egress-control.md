# Egress control (worker outBound / unlock)

> Parent: [SKILL.md](SKILL.md)  
> Control plane repo: `~/Projects/egress-control`  
> Spec: `~/Projects/egress-control/deploy/WIRE_EGRESS_CONTROL.md`  
> Shared client: `~/Projects/google run worker/_shared/egress_control_client.py`

## 1. Role in the stack

```
Apify Actor (thin)
    --HTTPS + WORKER_AUTH-->
Cloud Run worker (heavy)
    --runtime-config (runtime key)-->
egress-control @ https://worker.opendata.best
    --> PROXY_URL / Bright Data / RiskByPass / CapSolver / scrape defaults
Cloud Run worker --> target site
```

| Layer | Owns egress | Must not |
| --- | --- | --- |
| **egress-control** | Fleet proxy provider, unlock credentials, per-`workerId` strategy; admin UI | Scrape business logic; Apify Dataset / PPE |
| **Worker** | `apply_runtime_env` → use injected env; engine + parse + OpenAPI | Call admin API; hard-code vendor secrets as sole truth |
| **Actor** | `WORKER_PROVIDES_PROXY=1`; omit `proxyUrl` | Mint Apify RESIDENTIAL by default; call `worker.opendata.best`; hold BD/RiskByPass/CapSolver keys |

**Decision (2026-07-27):** control plane is **OVH + Cloudflare Tunnel**, decoupled from Cloud Run. Source of truth is the OVH DB/UI — not per-service Secret sprawl alone.

## 2. New worker checklist (mandatory)

1. Run `_shared/sync_shared.sh` so `src/egress_control_client.py` exists (also syncs `proxy_provider.py` / telemetry).
2. Wire `apply_runtime_env(WORKER_NAME)` in `main()` **before** binding `PORT`, and at the start of the scrape entrypoint (`run_search` / equivalent).
3. Register / update the worker in the control plane (`workerId` = Cloud Run service name, e.g. `walmart-com`) **before** claiming egress ready:

```bash
# Admin key stays on this machine. Never put it on Cloud Run.
bash "$SKILL/scripts/register_egress_worker.sh" <service-name> --from-peer <peer> --print-key
```

Or UI + manual mint:

```bash
curl -sS -H "X-Api-Key: $EGRESS_ADMIN_API_KEY" \
  https://worker.opendata.best/v1/workers/<service-name>/runtime-key
```

Unregistered id → `worker_not_found` → naked egress (Eventbrite 405) → auth search 422 empty. See [pitfalls.md](pitfalls.md).

4. Deploy Cloud Run with a **per-worker HMAC runtime key** (not admin, not the fleet `EGRESS_RUNTIME_API_KEY` master):

```text
EGRESS_CONTROL_BASE_URL=https://worker.opendata.best
EGRESS_CONTROL_API_KEY=<apiKey from runtime-key>
EGRESS_CONTROL_WORKER_ID=<service-name>
EGRESS_CONTROL_CACHE_TTL=120
```

After the fleet is rotated off the shared master, OVH must set
`EGRESS_ALLOW_SHARED_RUNTIME_KEY=0`. Workers that still hold the master can
HMAC any id locally — rotation must drop the master from Cloud Run.

5. Keep optional **fallback** env (`PROXY_URL`, vendor keys) for local smoke and control-plane outages. Unset `EGRESS_CONTROL_BASE_URL` / key → client no-ops; fetch failure → env fallback.
6. Prefer `--update-env-vars` (or env-vars-file merge) for `EGRESS_CONTROL_*`. Do **not** wipe other vars with a bare `--set-env-vars` that drops `PROXY_URL` / `WORKER_API_KEY`. Comma-in-value → `--env-vars-file` only. Orchestrator CDP (`/v1/sessions/lease`) is a hosted-browser rung; **`/v1/unlock` is not first-party unlock**.

Golden samples: `ealestate-com-au`, `zillow-com`, `shopee-com`, `upwork-com`.

## 3. Wiring snippet

```python
from src import egress_control_client

# main() before bind:
status = egress_control_client.apply_runtime_env(WORKER_NAME)
if status.get("source") == "control_plane":
    logger.info(
        "egress-control ready worker=%s version=%s keys=%s",
        status.get("workerId"),
        status.get("version"),
        ",".join(status.get("applied") or []),
    )

# scrape entrypoint:
egress_control_client.apply_runtime_env(WORKER_NAME)
```

## 4. Acceptance

| Check | Expect |
| --- | --- |
| `curl https://worker.opendata.best/healthz` | 200 |
| Worker `/openapi.json` (or public openapi path) | 200 |
| Cold-start logs | `egress-control ready worker=<id>` when control plane reachable |
| Scrape smoke | Still succeeds if control plane down **and** fallback `PROXY_URL` / keys present |

Do not claim “fleet closed” from healthz alone — claim scrape contract only after authenticated `/v1/*` smoke.

## 5. Actor side (new builds)

Default for every new thin Actor paired with a Cloud Run worker:

```json
"environmentVariables": {
  "WORKER_BASE_URL": "https://<worker>.run.app",
  "WORKER_AUTH": "@<ActorSecretName>",
  "WORKER_PROVIDES_PROXY": "1"
}
```

- Do **not** mint Apify RESIDENTIAL → `proxyUrl` unless Kane explicitly asks (debug / legacy exception).
- `RUN_SUMMARY.proxySource`: prefer `worker-env` (egress-applied or static `PROXY_URL`). Do not invent an Actor→egress hop.

## 6. Vendor skills vs control plane

| Concern | Where |
| --- | --- |
| Unlocker vs Scraping Browser vs Kasada vs CapSolver **fit** | Satellite [`bright-data-riskbypass`](../bright-data-riskbypass/SKILL.md) |
| Env names / CDP call shapes / measured gotchas | Same satellite |
| **Where credentials + per-worker policy live** | egress-control UI / runtime-config |
| Copying a new `brightdata.py` as the only truth | Avoid — prefer shared client + control plane |

**Never conflate:** Unlocker ≠ Scraping Browser ≠ RiskByPass Kasada ≠ CapSolver. Do not smash them into one `SCRAPE_PROVIDER` string without documenting the chain.

## 7. Secrets

- Runtime key ≠ admin key. Workers get **runtime** only.
- Keys live in control plane storage / `/opt/egress-control/.env` (gitignored) and optional Cloud Run fallback — **never** git, README, OpenAPI examples, or Mem0.
- Actor must not receive Bright Data / RiskByPass / CapSolver / egress admin credentials.

## 7b. Gotcha — Scraping Browser country ≠ proxy.country

`egress_control_client` must **not** map `proxy.country` → `BRIGHTDATA_BROWSER_COUNTRY`.
Residential Apify geo (often `au`) pinned Shopee VN/PH Scraping Browser exits and caused
`/verify/traffic` type=4 (batch smoke `0bcEYHondsl0vfNRs`). Only set browser country when
`tools.brightdata_browser.country` is explicit (`auto` / `off` / market code).

## 8. Proxy ↔ engine compatibility (worker-side mandatory)

> Source of truth for fleet gotchas: Mem0 (`cf374345`, `e625aebb`, `fbe8438d`,
> `2b371621`, `ead476b3`, `d84fce72`, `df8f4cd5`, `3722f335`, …).  
> Shared code: `_shared/proxy_provider.py` + `_shared/egress_control_client.py`  
> (always `sync_shared.sh` after edits).

Proxy switching and scrape engines are **orthogonal layers**. Control-plane
`proxy/switch` only changes mint/`PROXY_*`. Worker engines must already implement
the vendor-aware helpers below — otherwise a “valid” egress policy still fails
at `Page.goto` / CONNECT.

### 8.1 Compatibility matrix (integrated providers × engines)

Legend: ✅ OK when shared helpers wired · ⚠️ OK with constraints · ❌ do not pair ·
🔧 needs engine/factory change (not env-only)

| Provider / product | curl_cffi / HTTP | Playwright | Patchright | Camoufox | CloakBrowser | Bright Data Scraping Browser |
| --- | --- | --- | --- | --- | --- | --- |
| **Apify RESIDENTIAL** | ✅ | ✅ | ✅ | ⚠️ must keep `,` literal in username (`groups-…,country-XX`); `%2C` → `NS_ERROR_PROXY_CONNECTION_REFUSED` | ⚠️ verify CONNECT; prefer DI if flaky | N/A (use BD tool, not Apify URL) |
| **Apify GOOGLE_SERP** | ⚠️ Search/Shopping HTTP `www.google.*` only | ❌ Maps / Ads Transparency | ❌ | ❌ | ❌ | N/A |
| **DataImpulse residential** | ✅ fleet default | ✅ | ✅ | ✅ preferred for Camoufox when Apify fails | ✅ (DoorDash DI override OK when dedicated fails) | N/A |
| **Decodo residential** | ✅ | ✅ | ✅ | ⚠️ site ACL (e.g. Shopee 403 ≠ auth) | ⚠️ | N/A |
| **Oxylabs residential** (`customer-…-cc-XX` @ `pr.oxylabs.io`) | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | N/A |
| **Oxylabs dedicated ISP** (`user-…` @ `disp.*:800x`) | ✅ | ✅ (gmaps) | ✅ (ebay) | ❌ `NS_ERROR_UNKNOWN_HOST` (fleet) | ❌ `ERR_TUNNEL` on Cloud Run Cloak path | N/A |
| **Bright Data Unlocker / Scraping Browser** | via tools, not `PROXY_URL` | N/A | N/A | N/A | N/A | ✅; **never** inherit `proxy.country` |

**Hard product rules (enforced on control-plane PUT / `proxy/switch` via inferred
engine capabilities — Camoufox/Cloak `forbidDedicated`, SERP vs maps/playwright):**

- Never assign `GOOGLE_SERP` to Playwright/maps/ads workers.
- Never attach `country` to Oxylabs `dedicated_isp` policy (entry node rejects `-cc-`).
- Never treat egress `scrape.default_provider=browser` as universal — maps to different engines per worker (`3722f335`).
- Setting `SCRAPE_PROVIDER=brightdata_browser` does **nothing** if the worker hard-codes Patchright and never reads BD WS (`21a4037f`).

### 8.2 Worker-side features that MUST exist (shared + call sites)

These are the **compatibility / optimization** features already proven in fleet
incidents. New or refactored workers must include them via `sync_shared` + correct
call sites — do not re-implement one-off URL mangling in `main.py`.

#### A. `egress_control_client` (process env)

| Feature | Why | Status expectation |
| --- | --- | --- |
| **Wipe-then-set `PROXY_*`** on every successful apply | DI→dedicated left `PROXY_COUNTRY=us` → `user-xxx-cc-us` → tunnel fail | Required; `_PROXY_ENV_KEYS` wipe only (do **not** wipe `SCRAPE_*` / BD / RiskByPass) |
| **Scrape-refresh / version force fetch** | Switch lands without waiting full TTL / restart | Required |
| **No `proxy.country` → `BRIGHTDATA_BROWSER_COUNTRY`** | Shopee multi-market traffic verify | Required |
| **`resolve_proxy_for_request`** | Ignore `apify_actor_run` URLs when env `PROXY_URL` exists; apply geo via `proxy_provider` | Required for scrape entry |
| Optional **`GET /v1/egress-status`** + diagnostics `proxyHost` / `egressVersion` | Prove which mint is live after switch | Strongly recommended (VPS four already) |

#### B. `proxy_provider` (URL rewrite)

| Feature | Why | Status expectation |
| --- | --- | --- |
| **`detect_provider` + vendor-aware `with_country` / `with_session`** | Apify commas, DI `__cr.` / `;`, Oxylabs `-cc-`, Decodo `-country-` | Required |
| **Apify: `quote(..., safe` includes `,`)** + **`unquote` before edit** | Camoufox `%2C` → `NS_ERROR_PROXY_CONNECTION_REFUSED` (`fbe8438d` / `2b371621`) | Required in **both** `with_country` and `with_session` rebuild paths |
| **Oxylabs dedicated: skip `with_country` / `with_session`** when host `disp.*` or `user-*` (not `customer-*`) | `-cc-us` breaks CONNECT (`e625aebb`) | Required |
| **DataImpulse: keep `;` `.` `_` literal** in username quote safe | Chromium CONNECT breaks on `%3B` | Required |
| Prefer **`resolve_proxy_url` / `resolve_proxy_for_request`** over hand-rolled `PROXY_URL` + country | One code path for Actor override + egress mint | Required |

#### C. Engine / browser factory (per engine class)

| Engine | Proxy-related worker requirements |
| --- | --- |
| **curl_cffi / HTTP** | Pass resolved URL into session proxies; OK with Apify / DI / Decodo / Oxylabs residential **and** dedicated |
| **Playwright / Patchright** | Launch/context `proxy={"server","username","password"}` from **parsed** URL (after unquote); OK with dedicated ISP; do not re-apply country on dedicated |
| **Camoufox** | Prefer **DataImpulse** (or fixed Apify URL **without** mangled commas). **Do not** put Camoufox workers on Oxylabs dedicated or flaky Apify without smoke. Sync `proxy_provider` fix before any Apify+Camoufox switch |
| **CloakBrowser** | Not drop-in for Oxylabs dedicated on Cloud Run (`CLOAKBROWSER_BINARY_PATH` → no inline proxy auth → CDP 407/tunnel). Pair with **DI/Apify residential**, or migrate factory to Patchright (ebay pattern) before dedicated |
| **Bright Data Scraping Browser** | Wire `tools.brightdata_browser` only; explicit `country`; retries on traffic/timeout (Shopee pattern). Unlocker ≠ Browser |

### 8.3 Per-provider worker checklist (when policy uses that provider)

**Apify RESIDENTIAL**

- [ ] Mint via egress (`groups-RESIDENTIAL[,country-XX]`); Actor `WORKER_PROVIDES_PROXY=1`
- [ ] Shared `with_country` keeps comma-safe usernames (Camoufox-safe)
- [ ] Fall back: ignore Actor `apify_actor_run` proxy URLs on Cloud Run
- [ ] Camoufox workers: smoke CONNECT after any Apify switch; else stay on DI

**Apify GOOGLE_SERP**

- [ ] Only HTTP Search/Shopping workers; never maps/ads/playwright
- [ ] Control-plane profile + worker `forbiddenProducts: ["GOOGLE_SERP"]` when applicable

**DataImpulse**

- [ ] Country via `__cr.{cc}` / request `with_country`; sticky delimiters unescaped
- [ ] Default safe choice for Camoufox / CloakBrowser when dedicated fails

**Decodo**

- [ ] Username `user-…-country-{cc}` via shared helper
- [ ] Treat site HTTP 403 as ACL/content, not necessarily bad credentials

**Oxylabs residential**

- [ ] `customer-…-cc-{cc}` on `pr.oxylabs.io`; allow `with_country`

**Oxylabs dedicated ISP**

- [ ] Policy: `product=dedicated_isp`, host/port, **no country**
- [ ] Credentials: `oxylabs_dedicated_username` / `_password` (egress)
- [ ] Worker: wipe stale `PROXY_COUNTRY`; skip country/session rewrite on `disp.*`
- [ ] Engines: Playwright/Patchright/HTTP only unless measured OK; **not** Camoufox/CloakBrowser without waiver + smoke
- [ ] Optional multi-market: map country→`disp` **port** (not username `-cc-`)

**Geonode sticky (`geonode_sticky`, `:10000`)**

- [ ] **Each worker gets its own `-session-`**. Control plane defaults missing session to sanitized `workerId` (max 25 alnum). Do not mint sticky with empty session — that shares one exit across workers (traveloka SG + doordash “US” both hit the same IP).
- [ ] Explicit unique session (e.g. `doordashus` / `travelokasg`) is kept; rotating `:9000` must not get `-session-`.
- [ ] SEA Camoufox (Traveloka/Grab): prefer host `sg.premium-residential.geonode.com` — generic `proxy.geonode.io` sticky can land a blocked exit.
- [ ] After switch: re-probe ipinfo country, then scrape-smoke (ipinfo ≠ Camoufox/Cloak CONNECT)

**Bright Data (Unlocker / Scraping Browser)**

- [ ] Enabled only via egress `tools.*` + credential names
- [ ] Never copy `proxy.country` into browser country
- [ ] Confirm worker actually consumes BD WS/API (not Patchright-only hardcode)

### 8.4 Switch protocol vs engine pairing

When using `POST /v1/workers/{id}/proxy/switch` / profiles:

1. Validate **product ↔ worker capabilities** (SERP, dedicated+country) on control plane.
2. Worker apply: wipe `PROXY_*` → set mint → optional `/v1/egress-status`.
3. **Still** respect §8.1 — switch success ≠ Camoufox/CloakBrowser can use dedicated.
4. For CloakBrowser/Camoufox fleets, prefer profiles `dataimpulse_residential` /
   `apify_residential` (post-comma-fix) over `oxylabs_dedicated_isp`.

### 8.5 Do not (proxy×engine)

- Assume one residential provider works for every browser engine
- Fix tunnel failures by only changing egress provider without checking engine class
- Re-introduce `proxy.country` → Scraping Browser country inheritance
- Encode Apify username commas as `%2C` for Firefox/Camoufox
- Apply Oxylabs `-cc-` / session tags on dedicated `user-*` / `disp.*`
- Claim “dedicated fleet OK” after gmaps/ebay smoke while CloakBrowser food workers remain on dedicated

## 9. Do not

- Put egress-control or vendor unlock stacks into the thin Actor
- Treat Actor-minted `proxyUrl` as the default for new worker-backed Actors
- Use the admin API key on Cloud Run services
- Commit plaintext credentials or log full `proxyUrl` / API keys
- Drop `PROXY_URL` on redeploy “because egress exists” without verifying fallback smoke
