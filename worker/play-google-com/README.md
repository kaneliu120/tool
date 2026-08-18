# play-google-com (Cloud Run worker)

Thin scrape API for **Google Play** (`play.google.com`). Paired Actor: `actor/google-play-scraper`.

| | |
| --- | --- |
| Service / `workerId` | `play-google-com` |
| Region | `us-central1` (Play is global on one host) |
| Engine | `curl_cffi` Chrome impersonate → first-pack HTML (`AF_initDataCallback` + `details?id=`) + detail JSON-LD |
| Proxy | egress-control runtime config / `PROXY_URL` fallback. Actor `WORKER_PROVIDES_PROXY=1` |
| Schema | `2026-08-18.2` |

## Engine decision

Recon (2026-08-17) + HTTP expansion (2026-08-18):

| Source | Finding |
| --- | --- |
| Phase 0 channel | Same-origin HTML 200 ESF, no Cloudflare, no `__NEXT_DATA__` / RSC. JSON-LD on detail including `offers.price`. |
| A historical | No source Play worker. Kane HTTP floor = `curl_cffi` (zillow/daft class). |
| B GitHub | curl_cffi TLS impersonation; do not add Scrapling/Firecrawl/Crawlee. |
| C public | Impersonated HTTP first; browser only on measured blocks. |

**Default:** curl_cffi + first-pack parse. **Do not** forge `PlayStoreUi/data/batchexecute`. Escalate to a browser rung only if production HTTP starts returning empty shells / 403.

## Coverage matrix

Measured 2026-08-18 first-pack (`AF_initDataCallback` + live `details?id=`).

| Surface | Status |
| --- | --- |
| **183 `gl` presets** (home + search `c=apps` + GAME) | 打开. UZ uses `hl=en` (`hl=uz` was an empty ESF shell). |
| US category CODEs | 50 opened including `APPLICATION` and `WATCH_FACE` |
| Empty first-pack (HTTP 200, 0 live ids) | `DATING`, `MEDICAL`, `LIBRARIES_AND_DEMO`, `GAME_CASINO`, deprecated `FAMILY_ACTION` / `FAMILY_CREATE` / `FAMILY_EDUCATION` |
| FAMILY age chips `AGE_RANGE1/2/3` | 打开 (US) |
| `c=games` | HTTP 404 关闭 |
| Legacy `/store/apps/collection/topselling_*` | empty ESF, not a channel |
| Device chips / `gsr` / review bodies | 未采集 |

Unlisted ISO `gl` still accepted with a 未验证 warning. Empty shelves return envelope `status=empty` (0 items), not `failed`.

## API

Public: `GET /health`, `/openapi.json`, `/openapi.yaml`, `/docs`  
Auth scrape: `GET /v1/categories`, `POST /v1/search`, `POST /v1/listings`  
Headers: `Authorization: Bearer` and/or `X-Api-Key`

Envelope: `{ status, items, diagnostics, provider, warnings, worker, schemaVersion }`

Primary key: **package id**. Preview fields: `name`, `type`, `status`, `country`, `authority`. Detail enrich adds `price` / `priceCurrency` / `priceDisplay` / `isPaid` / `screenshots` / `inAppPurchases`.

## Ready / negative

- List ready: `/store/apps/details?id=` + `AF_initDataCallback`
- Empty shelf: `AF_initDataCallback` + 0 package ids (HTTP 200)
- Detail ready: JSON-LD `@type=SoftwareApplication` or `itemprop=name`
- Negative: `Not Found`, tiny body, no package ids. Substring `challenge` is **not** a Cloudflare page.

## Deploy

```bash
SKILL=.cursor/skills/apify-actor-cloud-run-development
bash "$SKILL/scripts/assert_cwd.sh" worker worker/play-google-com
bash "$SKILL/scripts/print_deploy_plan.sh" --region us-central1 --env-file /tmp/play-google-com-env.yaml worker/play-google-com
bash "$SKILL/scripts/register_egress_worker.sh" play-google-com --from-peer zillow-com --print-key
# later deploys: gcloud run deploy --source=. from this directory; never --set-env-vars wipe
```
