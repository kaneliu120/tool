---
name: bright-data-riskbypass
description: >-
  Integrate Bright Data (Web Unlocker + Scraping Browser/Browser API) and
  RiskByPass (Kasada / captcha / TLS forward) into Cloud Run scrape workers.
  Use when wiring BRIGHTDATA_* / RISKBYPASS_* env, choosing unlock vs browser
  vs Kasada solvers, debugging 407/premium/traffic-verify/ip_blacklisted, or
  when the user mentions Bright Data, Scraping Browser, Web Unlocker,
  RiskByPass, Kasada, x-kpsdk-ct, or superproxy.io.
---

# Bright Data + RiskByPass integration

Personal playbook for **Cloud Run workers** (thick scrape). Do **not** put these
stacks back into thin Apify Actors once a worker exists — see
[`apify-actor-cloud-run-development`](../apify-actor-cloud-run-development/SKILL.md).

**Credentials / per-worker policy (2026-07-27+):** prefer the fleet control plane
[`egress-control`](../apify-actor-cloud-run-development/egress-control.md)
(`https://worker.opendata.best`) + `egress_control_client.apply_runtime_env`.
Use this skill for **product fit** (Unlocker vs Browser vs Kasada), env **names**,
CDP/API shapes, and measured gotchas. Optional Cloud Run env remains **fallback**
only — do not treat per-worker Secret sprawl as the primary path for new workers.

## Choose the product (measure first)

| Need | Prefer | Avoid when |
| --- | --- | --- |
| HTML / JSON via HTTP, site unlockable server-side | **Bright Data Web Unlocker** | SPA needs real browser XHR capture |
| Full Chromium + captcha + network capture (`search_items`, etc.) | **Bright Data Scraping Browser** (CDP) | Budget tight; static HTML is enough |
| Kasada / `x-kpsdk-*` token then your own `curl_cffi` fetch | **RiskByPass `kasada` + `kasada_cd`** | Site is WAF/traffic-gate only (not Kasada) |
| Generic TLS fingerprint forward | RiskByPass `tls_forward` (if offered) | JS challenges, SPA hydration, Shopee-style traffic verify |

**Measured notes (this workspace):**

- **Shopee**: plain residential Playwright → `/verify/traffic`; Web Unlocker can return HTML shells; **Scraping Browser** unlocked live `search_items`. RiskByPass was **not** suitable (WAF/captcha solver ≠ Shopee traffic gate).
- **realestate.com.au**: Web Unlocker primary; RiskByPass Kasada path as failover (`ealestate-com-au`).
- **Zillow**: Web Unlocker HTML/JSON helpers (`zillow-com`); often failover, not default.

Escalate only with smoke evidence, not habit.

## Secrets (never commit)

| Env | Product |
| --- | --- |
| `BRIGHTDATA_API_KEY` / `BRIGHT_DATA_API_KEY` | Unlocker Bearer token |
| `BRIGHTDATA_UNLOCKER_ZONE` / `BRIGHT_DATA_UNLOCKER_ZONE` | Unlocker zone name |
| `BRIGHTDATA_COUNTRY` | Unlocker country (e.g. `au`, `us`, `ph`) |
| `BRIGHTDATA_BROWSER_WS` | Full `wss://user:pass@brd.superproxy.io:9222` |
| `BRIGHTDATA_BROWSER_AUTH` | Alt: `user:pass` → build WSS |
| `BRIGHTDATA_BROWSER_COUNTRY` | Optional pin (`ph` / `auto`); **default off** (can 407) |
| `RISKBYPASS_TOKEN` | RiskByPass `x-api-key` |
| `PROXY_URL` | Required for RiskByPass Kasada + optional Playwright fallback |

Store in **egress-control** (primary) and/or Cloud Run / Secret Manager (fallback).
Never paste passwords into README/git/Mem0/Actor env.

## Bright Data — Web Unlocker

**Endpoint:** `POST https://api.brightdata.com/request`

```python
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
body = {
    "zone": zone,
    "url": target_url,
    "format": "raw",
    "country": country.lower(),  # optional
    # optional: "method": "GET"|"POST"|..., "body": "...", "headers": {...}
}
resp = requests.post(API_URL, headers=headers, json=body, timeout=180)
```

**Checks:**

- `x-brd-error` / `x-brd-error-code` headers
- `premium` / “Premium Domains” → enable Premium Domains on the zone
- HTTP ≥400 or empty body → fail with diagnostics (`httpStatus`, `brdErrorCode`, bytes)

**Reference implementations:**

- `google run worker/ealestate-com-au/src/brightdata.py` — HTML
- `google run worker/zillow-com/src/brightdata.py` — HTML + JSON/`method`

## Bright Data — Scraping Browser (Browser API)

**Endpoints:**

| Client | URL |
| --- | --- |
| Playwright / Puppeteer | `wss://USER:PASS@brd.superproxy.io:9222` |
| Selenium | `https://USER:PASS@brd.superproxy.io:9515` |

Wrong port → **407**.

### Connect (Playwright)

```python
browser = await playwright.chromium.connect_over_cdp(ws, timeout=90_000)
page = await browser.new_page()  # official pattern
# Do NOT set Accept-Language via set_extra_http_headers — BD forbids it
page.set_default_navigation_timeout(120_000)
await page.goto(url, wait_until="domcontentloaded", timeout=120_000)
client = await page.context.new_cdp_session(page)
result = await client.send("Captcha.waitForSolve", {"detectTimeout": 20_000})
# status: solved | not_detected | timeout | ...
```

### Worker integration rules

1. Provider name: `brightdata_browser` (aliases: `scraping_browser`, `brightdata`).
2. Env: `BRIGHTDATA_BROWSER_WS` + `SCRAPE_PROVIDER=brightdata_browser`.
3. Actor usually **does not** need Apify `proxyUrl` for this path.
4. Fresh session ≈ new exit IP → **retry 2×** on traffic-verify / 0 rows.
5. Shopee `/verify/traffic` often returns Captcha `not_detected` — don't burn 60s+ on `Captcha.solve`; reconnect instead.
6. Prefer site **network capture** (XHR) over brittle DOM; keep DOM as fallback.
7. Parse modern BFF shapes (e.g. Shopee `item_basic=null` → `item_card_displayed_asset`).

**Reference:** `google run worker/shopee-com/src/browser_factory.py` + `shopee_search.py`.

## RiskByPass

**Base:** `https://riskbypass.com`  
**Auth header:** `x-api-key: <RISKBYPASS_TOKEN>`

### Task loop

1. `POST /task/submit` with JSON `{ task_type, ... }` → `task_id`
2. Poll `GET /task/result/{task_id}` until `SUCCESS` / failure / timeout
3. Read `result` object

### Kasada (proven on REA)

```text
task_type=kasada
  proxy, target_url, protected_api_domain, kasada_js_domain
→ x-kpsdk-ct, x-kpsdk-st, x-kpsdk-fc, user-agent, sec-ch-ua, ...

task_type=kasada_cd
  ct, st, fc?, site (REA uses site=twitch template in practice)
→ x-kpsdk-cd
```

Then fetch target with **`curl_cffi`** (`impersonate="chrome131"`), same `proxy`, headers + cookies:

- Headers: `x-kpsdk-ct`, `x-kpsdk-v`, optional `x-kpsdk-cd`, UA / sec-ch-ua from solve
- Cookies: site-specific (REA: `tkrm_alpekz_s1.3` / `…-ssn` = ct)

**Requires `PROXY_URL`** (residential). Token alone is not enough.

**Reference:** `google run worker/ealestate-com-au/src/riskbypass.py`.

### When RiskByPass is the wrong tool

- Target blocked by **non-Kasada** bot gates (e.g. Shopee traffic verify type=4)
- You need rendered SPA + authenticated XHR capture → Scraping Browser
- Balance OK but responses are empty shells → escalate engine, don't loop RiskByPass

## Worker provider wiring pattern

```text
resolve_provider():
  request.provider → else SCRAPE_PROVIDER → else credential-based default

brightdata (Unlocker)     → needs API key + zone (+ country)
brightdata_browser        → needs BRIGHTDATA_BROWSER_WS
riskbypass                → needs RISKBYPASS_TOKEN + PROXY_URL
playwright / browser      → needs proxyUrl / PROXY_URL
```

Document default + failover in worker README **Engine evaluation** block.

## Pitfalls checklist

- [ ] Secrets only in Cloud Run env / Secret Manager
- [ ] Unlocker: Premium Domains enabled for the target TLD
- [ ] Scraping Browser: port **9222** (Playwright), not 9515
- [ ] No `Accept-Language` override on BD browser pages
- [ ] `-country-*` on Browser username only if zone accepts it
- [ ] `ip_blacklisted` / 407 → caller egress blocked by BD ACL; test from Cloud Run region
- [ ] Don't wrap scrape errors as `BrowserLaunchError` (only wrap connect/new_page)
- [ ] RiskByPass: always pass residential `proxy` into `kasada` tasks
- [ ] Prove success with authenticated `/v1/search` smoke before declaring default

## More detail

- Code templates + env matrices: [reference.md](reference.md)
