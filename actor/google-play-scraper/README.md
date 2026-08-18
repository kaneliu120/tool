# Google Play Scraper (thin Actor)

Collect Google Play search, category, home, developer, and app-detail rows through a Cloud Run worker. The primary key is the **package name**. This Actor does not run a browser and does not invent app ids.

Free Apify plan users: up to **10 runs** of this Actor and up to **200 results per run** (Actor developer policy, not Apify). Paid Apify plans are unlimited.

## Coverage

Measured 2026-08-18 (same-engine `curl_cffi` first-pack). **183** `gl` presets — search `c=apps`, home, and GAME all opened. US category CODEs: 50 opened (`APPLICATION`, `WATCH_FACE` included). Empty first-pack: `DATING`, `MEDICAL`, `LIBRARIES_AND_DEMO`, `GAME_CASINO`, deprecated `FAMILY_*`. FAMILY age chips `AGE_RANGE1/2/3` opened. `c=games` HTTP 404. Device chips, `gsr`, review bodies not collected. Detail JSON-LD includes paid `offers.price` (`priceDisplay` / `isPaid`) plus `screenshots` / `inAppPurchases`. Empty shelves return worker `status=empty` (Actor SUCCEEDED, 0 rows).

## Input

- `mode`: search (default), category, home, developer, detail, datasafety
- `q`: search query (default `flashlight` so empty `{}` can SUCCEEDED)
- `category`: Play CODE (`GAME`, `SPORTS`, `GAME_WORD`, …)
- `packageIds` / `detailUrls`: live links only
- `market`: 183 opened ISO `gl` presets, or other ISO via `hl`/`gl` (未验证 warning)
- `hl` / `gl`: override Play language/country
- `age`: FAMILY age chip `AGE_RANGE1/2/3`
- `enrichDetails`: fetch JSON-LD (rating, price, screenshots, IAP) for list rows
- `maxResults`: 1–1000 (free plan capped at 200)

Cloud acceptance uses a **fresh random** input from `coverage-matrix.json`, never this README.

## Output

Preview: `name`, `type`, `status`, `country`, `authority`. Identity: `packageId` / `listingId`. Detail enrich adds JSON-LD rating, `price` / `priceCurrency` / `priceDisplay` / `isPaid`, `screenshots`, `inAppPurchases`, installs, developer.

## Architecture

Apify Actor (this repo) → HTTPS + API key → Cloud Run `play-google-com` → play.google.com.

Env: `WORKER_BASE_URL`, `WORKER_AUTH`, `WORKER_PROVIDES_PROXY=1`. Memory default **1024 MB**.
