# Worker contract — play.google.com

Paste source: `GooglePlay页面调研分析报告_2026-08-17.md` + this Cloud Agent HTTP (2026-08-17).

## Identity

| | |
| --- | --- |
| Site | play.google.com |
| Worker dir | `worker/play-google-com` (Cloud Agent; Kane Mac path would be `google run worker/play-google-com`) |
| Actor dir | `actor/google-play-scraper` |
| Cloud Run service / `workerId` | `play-google-com` |
| Region (site geography) | `us-central1` (Play is global on one host; US market opened; Google HQ) |
| Recon report | 2026-08-17 Google Play 页面调研分析报告 |

## Coverage matrix

| 市场 | Search `c=apps` | Category | Detail | Overlay / extra | 闸门 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| PH `hl=zh-CN&gl=PH` | 已验证 | GAME 已验证 | 已验证 | Reviews overlay 已验证（不扒正文） | guest | 打开 |
| US `hl=en&gl=US` | 已验证 | GAME + SPORTS 已验证 | 已验证 JSON-LD | Developer 已验证；Data safety 部分 | guest | 打开 |
| 其他 `gl` | 未验证 | 未验证 | 未验证 | 未验证 | | 未验证 |
| `c=games` | HTTP 404 | — | — | — | | 关闭 |

Home `/store/apps` US 已验证（裸 HTTP 活链）。Device chips / cluster `gsr` / 付费价 **未验证**。

## Per-surface channel

```text
Surface: Search / SERP
Final URL template: /store/search?q={q}&c=apps&hl={hl}&gl={gl}
Market / host: play.google.com
Primary channel: first-pack HTML AF_initDataCallback + a[href*="/store/apps/details?id="]
Path / headers (names only): GET HTML; batchexecute observed, body 未验证 — do not forge
Identity keys: package id
Pagination: none (no page=); first pack 20–30 cards
Ready signal: details?id= anchors + AF_initDataCallback (~1.2MB)
Negative signal: title Not Found / tiny body / no id=
Gate: guest
Suggested ladder rung: curl_cffi
Validation: 已验证
```

```text
Surface: Category
Final URL template: /store/apps/category/{CODE}
Primary channel: same HTML family
Ready signal: details?id= + AF_initDataCallback
Validation: GAME、SPORTS 已验证；其余 CODE 形状/未验证
```

```text
Surface: Detail / LDP
Final URL template: /store/apps/details?id={package}
Primary channel: JSON-LD SoftwareApplication + itemprop + chips (installs, ads)
Ready signal: SoftwareApplication or itemprop=name
Pagination: JSON-LD does not page
Validation: 已验证（活链，不编包名）
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
Validation: 已验证（Google LLC 数字 id，11 个活链）
```

## Ladder (measured this session only)

```text
Default: curl_cffi chrome impersonate + first-pack HTML/JSON-LD
Escalate when: production HTTP empty shell / 403 / verify page
Do not fallback: do not forge batchexecute; do not treat "challenge" substring as Cloudflare
Unlocker: N/A — recon HTTP 200 ESF, no CF
```

## Smoke

Random inputs from opened cells only. Fresh `q` (never hardcode `maps`). Category from opened CODE. Detail package ids must come from that run's live links.

## Do not

- Invent package names
- Treat `gsr` as a stable id
- Treat HTML `challenge` as Cloudflare
- Solve reCAPTCHA
- Bulk-scrape review bodies
- Forge batchexecute
