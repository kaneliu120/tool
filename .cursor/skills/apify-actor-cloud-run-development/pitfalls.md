# Pitfalls (measured — fail the run, do not tick past)

Parent: [SKILL.md](SKILL.md). Full table of session lessons. If a script exists, **run it**; do not re-litigate in prose.

## Identity / cwd

| Trigger | What you see | Rule |
| --- | --- | --- |
| `gcloud run deploy --source=.` from an **Actor** dir | Logs: `ActorInput`, exit 91, PORT probe fail (Costco) | `scripts/assert_cwd.sh worker` first. Worker = Dockerfile **and no** `.actor/actor.json` |
| Trust Console URL | Push/update the wrong Actor (LinkedIn link → Facebook) | API-resolve `username/name` before any push |
| Edit without `move_agent_to_root` | Changes land in the wrong workspace | Multi-root: worker path + Actor path |

## Deploy / egress

| Trigger | What you see | Rule |
| --- | --- | --- |
| Bare `--set-env-vars` with a few keys | Wipes `EGRESS_CONTROL_*` / `PROXY_URL` / `WORKER_API_KEY` | First deploy: full `--env-vars-file`. Later: `--update-env-vars` **additive**. Comma-in-value (Apify proxy user) → **only** `--env-vars-file` |
| New `workerId` never PUT on control plane | `worker_not_found` → naked egress → Eventbrite HTTP 405 → auth `/v1/search` 422 empty | `scripts/register_egress_worker.sh` **before** claiming egress ready |
| Cloud Run gets admin / fleet master key | HMAC any id; rotation nightmare | Runtime key only: `GET /v1/workers/{id}/runtime-key`. Actor never calls the plane |
| Drop `PROXY_URL` “because egress exists” | Control-plane blip → scrape dies | Keep fallback; smoke both paths |
| orch `/v1/unlock` as “first-party unlock” | Still Bright Data underneath | Unlocker last auto-ladder rung if already proven. Pin `provider=orchestrator` skips Patchright **and** Unlocker for that call — do **not** turn Unlocker off fleet-wide because a pin path worked |
| Geonode FR hostname vs NA site | Bad country / blocked | Match proxy country to site geography |
| orch VPS + extra Geonode `PROXY_URL` | `ERR_TUNNEL_CONNECTION_FAILED` (Ticketmaster) | Do not nest Geonode under orch CDP |

## Actor schema / smoke

| Trigger | What you see | Rule |
| --- | --- | --- |
| REQUIRED field has `prefill` but no `default` | Dev runs SUCCEEDED; Store auto-test `{}` → `Actor.fail()` → success rate collapse | Every REQUIRED has `default` = `prefill`, or make it optional. Empty `{}` must SUCCEEDED |
| Cloud accept uses README / schema default / Austin TX | False green | `scripts/random_smoke_input.py` from **opened** matrix cells → `--input-file` |
| New env (`WORKER_PROVIDES_PROXY`) on version, no rebuild | Still mints Apify proxy (Craigslist) | Rebuild `latest`; assert `proxySource=worker-env` |
| Shop coverage table missing `authKey` | Worker key ≠ Store `WORKER_AUTH` | Coverage rows carry `authKey`. Generic `searchQuery` may be wrong (Costco needs `keyword`) |
| Smoke with `-m 2048` | “Proves” 1024 defaults that never ran | `apify call -m 1024` |
| Manual `charged_event_name="apify-default-dataset-item"` | Synthetic PPE | Do not |

## Worker implementation

| Trigger | What you see | Rule |
| --- | --- | --- |
| Copy peer parse/wait/markets | Wrong selectors; mercadolibre copied walmart HTML | Copy infra only. Table: [templates/copy-vs-rewrite.md](templates/copy-vs-rewrite.md) |
| `sync_shared` looked for inside the worker | Missing `egress_control_client.py` | `~/Projects/google run worker/_shared/sync_shared.sh <worker>` |
| BFF 400 (bad param) falls through to HTML | Garbage / pause page | Do not HTML-fallback on structured 4xx |
| Pause ~160KB brand string | Thought hydration succeeded | Ready = `__NEXT_DATA__` + fat `edpData` (or pack equivalent), not a brand token |
| List 200 ≠ detail fetchable | Search green, event `full` empty | Per-surface gates. Matrix cells independent |
| `bool("virtual")` | Headed/Xvfb coerced to headless | `normalize_headless()` — never `bool(str)` |
| `headless=false` via Cloudflare | 502 | Default headless true unless measured otherwise |
| Ignore `apify_actor_run` proxy on Cloud Run | Broken proxy URL | Worker-owned egress |
| Local `.venv` green | Cloud Run Python/system mismatch | Triple smoke against **deployed** URL |

## Coverage / product

| Trigger | What you see | Rule |
| --- | --- | --- |
| Inherit source Actor as a **ceiling** | Dropped markets (TM geo hosts, Shopee category pages) | Source is a **floor**. Empty matrix cell = 未验证, not “N/A because source skipped it” |
| Prose “all services” | No Search/Category/Detail/Overlay/Market ticks | Ontology from `website-page-research`. Template: [templates/coverage-matrix.md](templates/coverage-matrix.md) |
| Firecrawl Map as coverage | Fake-complete URL list on 403/CSR | Map = 仅侧证 |

## Do not put in this skill

Bypass recipes, signature forge, Scrapling/Firecrawl/Crawlee as worker runtimes, driving the user’s Chrome from the Actor.
