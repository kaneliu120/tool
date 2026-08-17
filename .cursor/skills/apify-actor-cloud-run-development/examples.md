# Migration examples (Actor → worker)

## LinkedIn Jobs (patchright)

| | |
| --- | --- |
| Actor ID | `vbjPXhgJ9u8XhMcCW` (`lentic_clockss/linkedin-jobs-scraper`) |
| Worker | `google run worker/linkedin-com` |
| Region | `us-central1` |
| Engine | Inherit Patchright CloakBrowser + Guest Jobs |
| Shell | bayt-com Dockerfile (Chrome/Xvfb) |
| Actor thin | `worker_client` + PPE `result` / dataset item + Standby→worker |
| Store | Inherit PPE; `isPPEPlatformUsagePaidByUser: true` |

## Facebook Ad Library (curl_cffi GraphQL)

| | |
| --- | --- |
| Actor ID | `ktGss02P7vYV4uGOS` (`lentic_clockss/facebook-ad-library-scraper`) |
| Worker | `google run worker/facebook-com` |
| Region | `us-central1` |
| Engine | Inherit curl_cffi + Ad Library GraphQL |
| Shell | glassdoor-com / zillow-com (slim Python) |
| Actor thin | Keep `checkpoint` + optional CDN `assets`; remove GraphQL from Actor |
| Pitfall | First push may need rebuild with `applyEnvVarsToBuild=true` so `WORKER_AUTH` is present |
| Store | Prices unchanged ($0.005 start / $0.002 item); platform usage yes |

## TikTok (patchright + CapSolver)

| | |
| --- | --- |
| Actor ID | `wsdAqpLn1ykYGHqAU` (`lentic_clockss/tiktok-scraper`) |
| Worker | `google run worker/tiktok-com` |
| Region | `us-central1` |
| Engine | Inherit Patchright CloakBrowser + XHR + CapSolver |
| Shell | bayt/linkedin Dockerfile (Chrome/Xvfb) |
| Actor thin | Keep optional video download via httpx; remove browser engine |
| Pitfall | `WorkerCollectionResult` must include fields main.py expects (`timings`); CapSolver secret may not be readable via API — set `CAPSOLVER_API_KEY` on Cloud Run env separately |
| Store | Inherit PPE; platform usage yes; prices unchanged |

## Booking.com Hotels (patchright)

| | |
| --- | --- |
| Actor ID | `vXrlagWWqZiiL48YR` (`lentic_clockss/booking-hotels-scraper`) |
| Worker | `google run worker/booking-com` |
| Region | `europe-west4` (Booking.com NL/EU HQ) |
| Engine | Inherit Patchright headed Chrome + Xvfb + CF wait (no CapSolver) |
| Shell | linkedin-com / bayt-com Dockerfile (Chrome/Xvfb) |
| Actor thin | `worker_client` + PPE dataset item + Standby façade; no browser in Actor |
| Pitfall | Slim `engine/__init__.py` after stripping Apify proxy helpers (`resolve_sticky_proxy`); cold-start: lazy-import scrape stack so PORT binds quickly; first Cloud Run deploy may need `--cpu-boost` |
| Store | Prices unchanged ($0.005 start / $0.003 item); `isPPEPlatformUsagePaidByUser: true` |


## Jobicy Remote Jobs (curl_cffi API)

| | |
| --- | --- |
| Actor ID | `WLN1jUzN2xm9fa4RN` (`lentic_clockss/jobicy-remote-jobs-scraper`) |
| Worker | `google run worker/jobicy-com` |
| Region | `us-central1` |
| Engine | Inherit curl_cffi → public Jobicy JSON API (no browser, no proxy required) |
| Shell | facebook-com / glassdoor-com (slim Python) |
| Actor thin | `worker_client` + Standby façade; remove `jobicy_client`/`collector` |
| Store | Prices unchanged ($0.005 start / $0.002 item); platform usage already yes |

## Lazada Product Search (Playwright AJAX)

| | |
| --- | --- |
| Actor ID | `Q6NsHrUhBzxboRav8` (`lentic_clockss/lazada-ph-search-results-collector`) |
| Worker | `google run worker/lazada-com` |
| Region | `australia-southeast1` (fallback — `asia-southeast1/2` new-region quota exceeded) |
| Engine | Inherit Store Playwright Chromium + in-page catalog AJAX; curl_cffi punished on smoke → escalated |
| Shell | Playwright Python base image (`mcr.microsoft.com/playwright/python:v1.60.0-jammy`) |
| Actor thin | `worker_client` + mint Apify RESIDENTIAL (country=market); remove browser stack |
| Pitfall | Pin `pydantic<2.12` (2.13 breaks apify/crawlee import); SEA region quota may force AU deploy |
| Store | Prices unchanged (`result-item` $0.0019); platform usage already yes |

## Himalayas Remote Jobs (curl_cffi API)

| | |
| --- | --- |
| Actor ID | `QOAYoqT7eaNUUceXb` (`lentic_clockss/himalayas-jobs-scraper`) |
| Worker | `google run worker/himalayas-com` |
| Region | `us-central1` |
| Engine | Inherit curl_cffi → public Himalayas paginated JSON API (`/jobs/api`, offset/limit 20) |
| Shell | jobicy-com (slim Python) |
| Actor thin | `worker_client` + Standby façade; remove `himalayas_client`/`collector` |
| Store | Prices unchanged ($0.005 start / $0.002 item); platform usage already yes |

## Daft.ie Property (curl_cffi + __NEXT_DATA__)

| | |
| --- | --- |
| Actor ID | `NWVnO9Yt3UsKQijLc` (`lentic_clockss/daft-property-scraper`) |
| Worker | `google run worker/daft-ie` |
| Region | `europe-west1` (Ireland / EU) |
| Engine | Inherit curl_cffi → HTML `__NEXT_DATA__` SRP+LDP; worker-owned residential (prefer egress-control) |
| Shell | otodom-pl (curl Next.js EU twin) |
| Actor thin | `worker_client` + `WORKER_PROVIDES_PROXY=1` (omit `proxyUrl`); remove scrape stack |
| Store | Prices unchanged ($0.005 start / $0.0025 item); platform usage already yes |

## Walmart (thin Actor compute tune, no rebuild)

| | |
| --- | --- |
| Actor ID | `5NZ6LCnfRWley6Zcx` (`lentic_clockss/walmart-scraper`) |
| Worker | `google run worker/walmart-com` |
| Change | Remote `defaultRunOptions.memoryMbytes` **2048 → 1024** via API PUT only |
| Build | Stayed on **0.1.13** (no `apify push`) |
| Smoke | `N61Xgc9T1Q65Jvgmg` SUCCEEDED @ 1024 MB, CU ≈ 0.023 |
| Lesson | Thin HTTP Actors: half memory ≈ half CU; PPE start drops from 2× to 1× at ≤1 GB |
| Detail | [actor-compute-cost.md](actor-compute-cost.md) |

## Egress-control (fleet proxy / unlock)

| | |
| --- | --- |
| Control plane | `https://worker.opendata.best` (OVH + CF Tunnel) |
| Client | `google run worker/_shared/egress_control_client.py` → sync into each worker `src/` |
| Wire | `apply_runtime_env(WORKER_NAME)` in `main()` + scrape entry; Cloud Run `EGRESS_CONTROL_*` |
| Actor default | `WORKER_PROVIDES_PROXY=1` — no Apify mint / no `proxyUrl` |
| Golden samples | `ealestate-com-au`, `zillow-com`, `shopee-com`, `upwork-com` |
| Detail | [egress-control.md](egress-control.md) · repo `~/Projects/egress-control` |

## Common pitfalls

Full table: [pitfalls.md](pitfalls.md). Do not tick past a failing script.

1. **Wrong console ID** — always API-resolve `username/name` before push.
2. **Actor-run proxy on Cloud Run** — new Actors use `WORKER_PROVIDES_PROXY=1`; worker falls back to `PROXY_URL` / egress-applied env (not Actor-minted `apify_actor_run` URLs).
3. **Env after push** — secrets on version may need rebuild to apply to `latest` runtime.
4. **Store PUT** — never mutate event unit prices; only inherit / ensure platform-usage flag.
5. **Worker `engine/__init__.py`** — after thinning proxy helpers, drop Apify-only exports or imports crash on first `/v1/search`.
6. **Thin Actor RAM** — do not default 2048/4096; do not validate 1024 defaults with `-m 2048`.
7. **Egress wipe** — never `--set-env-vars`; comma-in-value → `--env-vars-file` only.
8. **Admin vs runtime key** — Cloud Run gets egress **runtime** key only; never put admin key or vendor secrets on the Actor.
9. **Wrong cwd deploy** — `gcloud run deploy --source=.` from an Actor dir ships the Apify image (Costco PORT fail). Use `scripts/assert_cwd.sh worker`.
10. **Unregistered workerId** — `worker_not_found` then 405/422 empty. `scripts/register_egress_worker.sh` first.
11. **prefill ≠ default** — Store auto-test uses `default`; empty `{}` must SUCCEEDED.
12. **README smoke** — use `scripts/random_smoke_input.py`, never Austin TX / schema prefill.
13. **Copy peer parse** — infra only; rewrite collector/markets ([templates/copy-vs-rewrite.md](templates/copy-vs-rewrite.md)).
14. **orch `/v1/unlock`** — may still be Bright Data; Unlocker stays last auto rung unless Kane says otherwise.
