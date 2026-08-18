# play-google-com (Cloud Run worker)

Thin scrape API for **Google Play** (`play.google.com`). Paired Actor: `actor/google-play-scraper`.

| | |
| --- | --- |
| Service / `workerId` | `play-google-com` |
| Region | `us-central1` (Play is global on one host) |
| Engine | `curl_cffi` Chrome impersonate → first-pack HTML (`AF_initDataCallback` + `details?id=`) + detail JSON-LD |
| Proxy | egress-control runtime config / `PROXY_URL` fallback. Actor `WORKER_PROVIDES_PROXY=1` |
| Schema | `2026-08-18.1` |

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

| 市场 `hl`/`gl` | Search `c=apps` | Home | Category GAME | Detail JSON-LD | 闸门 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| us en/US | 已验证 | 已验证 | 已验证 | 已验证（含付费 `offers.price`） | guest | 打开 |
| ph zh-CN/PH | 已验证 | 已验证 | 已验证 | 已验证 | guest | 打开 |
| gb en/GB | 已验证 | 已验证 | 已验证 | 同引擎 | guest | 打开 |
| au en/AU | 已验证 | 已验证 | 已验证 | 同引擎 | guest | 打开 |
| jp ja/JP | 已验证 | 已验证 | 已验证 | 同引擎 | guest | 打开 |
| tw zh-TW/TW | 已验证 | 已验证 | 已验证 | 同引擎 | guest | 打开 |
| de de/DE | 已验证 | 已验证 | 已验证 | 同引擎 | guest | 打开 |
| fr fr/FR | 已验证 | 已验证 | 已验证 | 同引擎 | guest | 打开 |
| in en/IN | 已验证 | 已验证 | 已验证 | 同引擎 | guest | 打开 |
| br pt/BR | 已验证 | 已验证 | 已验证 | 同引擎 | guest | 打开 |
| ca en/CA | 已验证 | 已验证 | 已验证 | 同引擎 | guest | 打开 |
| sg en/SG | 已验证 | 已验证 | 已验证 | 同引擎 | guest | 打开 |
| `c=games` | HTTP 404 | — | — | — | | 关闭 |

US `/store/apps/category/{CODE}`: **48 opened**. Empty first-pack (HTTP 200, 0 live ids): `DATING`, `MEDICAL`, `LIBRARIES_AND_DEMO`, `GAME_CASINO`. Device chips, cluster `gsr`, review bodies **未采集**. Other ISO `gl` still 未验证 (accepted with warning).

## API

Public: `GET /health`, `/openapi.json`, `/openapi.yaml`, `/docs`  
Auth scrape: `GET /v1/categories`, `POST /v1/search`, `POST /v1/listings`  
Headers: `Authorization: Bearer` and/or `X-Api-Key`

Envelope: `{ status, items, diagnostics, provider, warnings, worker, schemaVersion }`

Primary key: **package id**. Preview fields: `name`, `type`, `status`, `country`, `authority`. Detail enrich adds `price` / `priceCurrency` / `priceDisplay` / `isPaid`.

## Ready / negative

- List ready: `/store/apps/details?id=` + `AF_initDataCallback`
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
