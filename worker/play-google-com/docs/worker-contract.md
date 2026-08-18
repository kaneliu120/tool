# Worker contract — play.google.com

Paste source: `GooglePlay页面调研分析报告_2026-08-17.md` + Cloud Agent HTTP (2026-08-17, expansion 2026-08-18).

## Identity

| | |
| --- | --- |
| Site | play.google.com |
| Worker dir | `worker/play-google-com` (Cloud Agent; Kane Mac path would be `google run worker/play-google-com`) |
| Actor dir | `actor/google-play-scraper` |
| Cloud Run service / `workerId` | `play-google-com` |
| Region (site geography) | `us-central1` (Play is global on one host) |
| Recon report | 2026-08-17 Google Play 页面调研分析报告 |

## Coverage matrix

| 市场 | Search `c=apps` | Home | Category | Detail | Overlay / extra | 闸门 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 183 ISO `gl` presets | 已验证 | 已验证 | GAME 已验证；US 另 49 CODE 已验证（含 APPLICATION / WATCH_FACE） | JSON-LD 已验证；付费 `offers.price` 已验证 | Developer 已验证；FAMILY `age=` 已验证；Data safety 部分；Reviews overlay 不扒正文 | guest | 打开 |
| `c=games` | HTTP 404 | — | — | — | — | | 关闭 |
| DATING / MEDICAL / LIBRARIES_AND_DEMO / GAME_CASINO / FAMILY_ACTION / FAMILY_CREATE / FAMILY_EDUCATION | — | — | first-pack 0 活链 | — | — | guest | empty |
| Legacy `collection/topselling_*` | — | empty ESF | — | — | — | guest | 关闭 |

Device chips / cluster `gsr` **未验证**. Unlisted ISO `gl` **未验证**.

## Per-surface channel

```text
Surface: Search / SERP
Final URL template: /store/search?q={q}&c=apps&hl={hl}&gl={gl}
Market / host: play.google.com
Primary channel: first-pack HTML AF_initDataCallback + a[href*="/store/apps/details?id="]
Path / headers (names only): GET HTML; Accept-Language follows hl; batchexecute observed, body 未验证 — do not forge
Identity keys: package id
Pagination: none (no page=); first pack 20–30 cards
Ready signal: details?id= anchors + AF_initDataCallback
Empty signal: AF_initDataCallback + 0 details?id= (HTTP 200)
Negative signal: title Not Found / tiny body / no id=
Gate: guest
Suggested ladder rung: curl_cffi
Validation: 已验证 (183 presets)
```

```text
Surface: Category
Final URL template: /store/apps/category/{CODE}[?age=AGE_RANGE*]
Primary channel: same HTML family
Ready signal: details?id= + AF_initDataCallback
Validation: 50 US CODE 已验证; 7 empty first-pack; FAMILY age chips 已验证
```

```text
Surface: Detail / LDP
Final URL template: /store/apps/details?id={package}
Primary channel: JSON-LD SoftwareApplication + itemprop + chips (installs, ads, IAP) + offers.price + screenshot
Ready signal: SoftwareApplication or itemprop=name
Pagination: JSON-LD does not page
Validation: 已验证（活链，不编包名；付费价 Terraria 4.99 USD 本会话）
```

```text
Surface: Data safety
Final URL template: /store/apps/datasafety?id={package}
Primary channel: HTML headings (h2.q1rIdc)
Validation: 部分（页面 200，字段树未 walk ds:N）
```

```text
Surface: Developer
Final URL template: /store/apps/dev?id={numeric}
Primary channel: same card anchors
Validation: 已验证（Google LLC 数字 id）
```

## Ladder (measured this session only)

```text
Default: curl_cffi chrome impersonate + first-pack HTML/JSON-LD
Escalate when: production HTTP empty shell / 403 / verify page
Do not fallback: do not forge batchexecute; do not treat "challenge" substring as Cloudflare
Unlocker: N/A — recon HTTP 200 ESF, no CF
```

## Smoke

Random inputs from opened cells only. Fresh `q` (never hardcode `maps` / schema default `flashlight`). Category from opened CODE. Detail package ids must come from that run's live links. `enrichDetails` cell is opened.

## Do not

- Invent package names
- Treat `gsr` as a stable id
- Treat HTML `challenge` as Cloudflare
- Solve reCAPTCHA
- Bulk-scrape review bodies
- Forge batchexecute
