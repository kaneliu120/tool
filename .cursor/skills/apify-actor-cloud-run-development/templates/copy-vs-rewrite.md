# Copy vs rewrite (factory vs site delta)

Scaffold with `scripts/scaffold_worker.sh` / `scripts/scaffold_actor.sh`, then **only open delta files**.  
Peer is chosen by **engine class**, not by vertical (mercadolibre infra ← walmart; parse is rewritten).

## Worker

| File / area | Copy from peer | Rewrite for this site |
| --- | --- | --- |
| `Dockerfile`, `requirements.txt` (engine deps) | Yes | Only if engine class changes |
| `src/auth.py`, OpenAPI `securitySchemes`, `/docs` | Yes | No |
| `src/main.py` envelope, `/health`, CORS, PORT bind | Yes | Paths (`/v1/search` vs `/v1/listings`) if the contract differs |
| `egress_control_client.py`, `proxy_provider.py`, telemetry | **`_shared/sync_shared.sh`** — never hand-edit copies | No |
| `apply_runtime_env(WORKER_NAME)` call sites | Yes | Worker name string |
| `src/collector.py` / parse / wait / hydration | **No** | **Yes** — from Phase 0 contract |
| Markets / hosts / category enums | **No** | **Yes** — from coverage matrix |
| Ready / negative signals | **No** | **Yes** |
| Ladder order / `provider` pins | Start from peer | Adjust from measured gates |
| README coverage + engine decision block | Structure | Contents |

`sync_shared` lives at `~/Projects/google run worker/_shared/sync_shared.sh`, **not** inside a single worker.

## Thin Actor

| File / area | Copy | Change |
| --- | --- | --- |
| `src/worker_client.py` (HTTPS, allowlist, Bearer + X-Api-Key) | Yes | OpenAPI paths if worker differs |
| `src/free_tier.py`, Standby, `INPUT_ECHO` / `RUN_SUMMARY` | Yes | Caps/copy only if Store-facing differs |
| `defaultRunOptions.memoryMbytes` 1024, `WORKER_PROVIDES_PROXY=1` | Yes | No |
| `src/input_model.py`, `input_schema.json` | Structure | Field names = site (Costco `keyword` ≠ generic `searchQuery`) |
| `.actor/actor.json` name / title / SEO | | This product |
| README / dataset_schema preview fields | Structure | Site fields |
| Browser, unlock, egress-control client | **Must not exist** | — |

If you find yourself editing `worker_client` auth or `egress_control_client`, the factory layer was not copied cleanly — stop and re-scaffold.

## Peers (engine class)

| Engine | Worker peer | Actor peer (typical) |
| --- | --- | --- |
| curl_cffi / HTTP | `zillow-com` / `glassdoor-com` | `zillow-scraper` |
| Camoufox + Xvfb | `apartments-com` (gen2) | matching thin Actor |
| Patchright + Chrome | `bayt-com` / `linkedin-com` / `walmart-com` | matching thin Actor |
