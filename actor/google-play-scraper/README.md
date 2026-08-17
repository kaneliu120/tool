# Google Play Scraper (thin Actor)

Collect Google Play search, category, home, developer, and app-detail rows through a Cloud Run worker. The primary key is the **package name**. This Actor does not run a browser and does not invent app ids.

Free Apify plan users: up to **10 runs** of this Actor and up to **200 results per run** (Actor developer policy, not Apify). Paid Apify plans are unlimited.

## Coverage

| Market | Search `c=apps` | Category | Detail | Extra | Status |
| --- | --- | --- | --- | --- | --- |
| US `hl=en&gl=US` | opened | GAME, SPORTS opened | opened (JSON-LD) | developer opened; data safety partial | opened |
| PH `hl=zh-CN&gl=PH` | opened | GAME opened | opened | reviews overlay observed (bodies not collected) | opened |
| Other `gl` | 未验证 | 未验证 | 未验证 | 未验证 | 未验证 |

`c=games` returned HTTP 404 this session. Device chips, cluster `gsr`, and paid prices stay 未验证.

## Input

- `mode`: search (default), category, home, developer, detail, datasafety
- `q`: search query (default `flashlight` so empty `{}` can SUCCEEDED)
- `category`: Play CODE (`GAME`, `SPORTS`, …)
- `packageIds` / `detailUrls`: live links only
- `market`: `us` or `ph` (opened) or other presets (未验证)
- `hl` / `gl`: override Play language/country
- `maxResults`: 1–1000 (free plan capped at 200)

Cloud acceptance uses a **fresh random** input from `coverage-matrix.json`, never this README.

## Output

Preview: `name`, `type`, `status`, `country`, `authority`. Identity: `packageId` / `listingId`. Detail enrich adds JSON-LD rating, price, installs, developer.

## Architecture

Apify Actor (this repo) → HTTPS + API key → Cloud Run `play-google-com` → play.google.com.

Env: `WORKER_BASE_URL`, `WORKER_AUTH`, `WORKER_PROVIDES_PROXY=1`. Memory default **1024 MB**.
