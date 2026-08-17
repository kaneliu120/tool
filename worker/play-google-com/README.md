# play-google-com (Cloud Run worker)

Thin scrape API for **Google Play** (`play.google.com`). Paired Actor: `actor/google-play-scraper`.

| | |
| --- | --- |
| Service / `workerId` | `play-google-com` |
| Region | `us-central1` (Play is global on one host; US market opened) |
| Engine | `curl_cffi` Chrome impersonate → first-pack HTML (`AF_initDataCallback` + `details?id=`) + detail JSON-LD |
| Proxy | egress-control runtime config / `PROXY_URL` fallback. Actor `WORKER_PROVIDES_PROXY=1` |
| Schema | `2026-08-17.1` |

## Engine decision

Recon (2026-08-17) + this session HTTP:

| Source | Finding |
| --- | --- |
| Phase 0 channel | Same-origin HTML 200 ESF, no Cloudflare, no `__NEXT_DATA__` / RSC. JSON-LD only on detail. |
| A historical | No source Play worker. Kane HTTP floor = `curl_cffi` (zillow/daft class). |
| B GitHub | curl_cffi TLS impersonation; do not add Scrapling/Firecrawl/Crawlee. |
| C public | Impersonated HTTP first; browser only on measured blocks. |

**Default:** curl_cffi + first-pack parse. **Do not** forge `PlayStoreUi/data/batchexecute`. Escalate to a browser rung only if production HTTP starts returning empty shells / 403.

## Coverage matrix

| 市场/host | Search `c=apps` | Category | Detail | Overlay | 闸门 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| `gl=PH` `hl=zh-CN` | 已验证 | GAME 已验证 | 已验证 | Reviews 已验证（不采集正文） | guest | 打开 |
| `gl=US` `hl=en` | 已验证 | GAME + SPORTS 已验证 | 已验证 JSON-LD | Developer 已验证；Data safety 部分 | guest | 打开 |
| 其他 `gl` | 未验证 | 未验证 | 未验证 | 未验证 | guest? | 未验证 |
| `c=games` | HTTP 404 | — | — | — | | 关闭 |

Home `/store/apps` (US) 已验证。Device chips、cluster `gsr`、付费价 **未验证**。`gl` 可传任意 ISO 国家码；未打开市场会带 warning。

## API

Public: `GET /health`, `/openapi.json`, `/openapi.yaml`, `/docs`  
Auth scrape: `GET /v1/categories`, `POST /v1/search`, `POST /v1/listings`  
Headers: `Authorization: Bearer` and/or `X-Api-Key`

Envelope: `{ status, items, diagnostics, provider, warnings, worker, schemaVersion }`

Primary key: **package id**. Preview fields: `name`, `type`, `status`, `country`, `authority`.

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
# then gcloud run deploy from this directory; never --set-env-vars wipe
```
