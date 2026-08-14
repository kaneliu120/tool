# Bright Data + RiskByPass — reference

Companion to [SKILL.md](SKILL.md). Copy patterns; adapt zone/country/domains per site.

## Workspace canonical code

| Path | Role |
| --- | --- |
| `google run worker/ealestate-com-au/src/brightdata.py` | Unlocker HTML |
| `google run worker/ealestate-com-au/src/riskbypass.py` | Kasada + kasada_cd + curl_cffi fetch |
| `google run worker/zillow-com/src/brightdata.py` | Unlocker HTML + JSON methods |
| `google run worker/shopee-com/src/browser_factory.py` | Scraping Browser CDP connect |
| `google run worker/shopee-com/src/shopee_search.py` | Captcha.waitForSolve + XHR capture |

## Env matrix

### Unlocker worker

```bash
SCRAPE_PROVIDER=brightdata
BRIGHTDATA_API_KEY=...
BRIGHTDATA_UNLOCKER_ZONE=...          # e.g. shopee_unlocker_api / web_unlocker1
BRIGHTDATA_COUNTRY=au                 # market-matched
# optional failover:
# BRIGHTDATA_FAILOVER=1
```

### Scraping Browser worker

```bash
SCRAPE_PROVIDER=brightdata_browser
BRIGHTDATA_BROWSER_WS=wss://brd-customer-XXX-zone-ZONE:PASSWORD@brd.superproxy.io:9222
# optional:
# BRIGHTDATA_BROWSER_AUTH=brd-customer-XXX-zone-ZONE:PASSWORD
# BRIGHTDATA_BROWSER_COUNTRY=off|ph|auto
```

### RiskByPass worker

```bash
SCRAPE_PROVIDER=riskbypass
RISKBYPASS_TOKEN=...
PROXY_URL=http://user:pass@host:port   # residential; required
```

## Unlocker request shapes

### HTML GET

```json
{
  "zone": "ZONE",
  "url": "https://example.com/path",
  "format": "raw",
  "country": "au"
}
```

### JSON / custom method (Zillow-style)

```json
{
  "zone": "ZONE",
  "url": "https://api.example.com/...",
  "format": "raw",
  "method": "PUT",
  "country": "us",
  "headers": { "Content-Type": "application/json" },
  "body": "{\"key\":\"value\"}"
}
```

Response body is raw target payload. Inspect `x-brd-error*` on failure.

## Scraping Browser — minimal async Playwright

```python
from playwright.async_api import async_playwright

WS = "wss://USER:PASS@brd.superproxy.io:9222"

async def scrape(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(WS, timeout=90_000)
        try:
            page = await browser.new_page()
            page.set_default_navigation_timeout(120_000)
            client = await page.context.new_cdp_session(page)
            await page.goto(url, wait_until="domcontentloaded", timeout=120_000)
            captcha = await client.send(
                "Captcha.waitForSolve", {"detectTimeout": 20_000}
            )
            # optional: listen Captcha.detected / solveFinished / solveFailed
            return await page.content(), captcha.get("status")
        finally:
            await browser.close()
```

### Captcha CDP helpers

| Command | Use |
| --- | --- |
| `Captcha.waitForSolve` | After goto; `detectTimeout` ms |
| `Captcha.solve` | Explicit solve attempt |
| `Captcha.setAutoSolve` | `{ "autoSolve": false }` to disable |

Shopee traffic pages often yield `not_detected` — treat as soft block and **new browser session**.

### Selenium note

Use `https://USER:PASS@brd.superproxy.io:9515` only for Selenium WebDriver. Playwright must use WSS `:9222`.

## RiskByPass — submit / poll

```python
BASE = "https://riskbypass.com"
headers = {"Content-Type": "application/json", "x-api-key": token}

# submit
r = requests.post(f"{BASE}/task/submit", headers=headers, json=payload, timeout=30)
task_id = r.json()["task_id"]

# poll
while True:
    out = requests.get(
        f"{BASE}/task/result/{task_id}",
        headers={"x-api-key": token, "Cache-Control": "no-cache"},
        timeout=30,
    ).json()
    if out["status"] == "SUCCESS":
        return out["result"]
    if out["status"] in {"RUNNING", "QUEUED"}:
        time.sleep(1.5)
        continue
    raise RuntimeError(out)
```

### Kasada payload

```json
{
  "task_type": "kasada",
  "proxy": "http://user:pass@host:port",
  "target_url": "https://www.realestate.com.au/...",
  "protected_api_domain": "www.realestate.com.au",
  "kasada_js_domain": "www.realestate.com.au"
}
```

### Kasada CD payload

```json
{
  "task_type": "kasada_cd",
  "ct": "<x-kpsdk-ct>",
  "st": "<x-kpsdk-st>",
  "fc": "<x-kpsdk-fc optional>",
  "site": "twitch"
}
```

### Fetch after solve (sketch)

```python
from curl_cffi import requests as c_requests

headers = {
    "user-agent": kasada["user-agent"],
    "sec-ch-ua": kasada.get("sec-ch-ua") or "",
    "sec-ch-ua-platform": kasada.get("sec-ch-ua-platform") or '"Windows"',
    "x-kpsdk-ct": kasada["x-kpsdk-ct"],
    "x-kpsdk-v": kasada.get("x-kpsdk-v") or "j-1.2.522",
}
if cd:
    headers["x-kpsdk-cd"] = cd
cookies = {
    "tkrm_alpekz_s1.3-ssn": kasada["x-kpsdk-ct"],
    "tkrm_alpekz_s1.3": kasada["x-kpsdk-ct"],
}
resp = c_requests.get(
    target_url,
    headers=headers,
    cookies=cookies,
    proxies={"http": proxy_url, "https": proxy_url},
    impersonate="chrome131",
    timeout=60,
)
```

Cookie / header names are **site-specific** — copy from a working worker for that brand; do not invent.

## Decision smoke checklist

1. Credential present on Cloud Run (not only laptop).
2. Authenticated worker `/v1/search` (or equivalent) returns `status=ok` and ≥1 items.
3. Diagnostics record `provider` + useful unlock fields (`brdErrorCode`, `captchaStatus`, Kasada keys).
4. Failure modes classified: auth (401/407), premium, traffic-verify, parse-empty, timeout.
5. README engine evaluation updated with measured default.

## Anti-patterns

- Committing zone passwords or RiskByPass tokens
- Using Unlocker zone credentials as Scraping Browser WSS (wrong product)
- Forcing `-country-*` on Browser username without testing
- Setting Scraping Browser as default without a successful Cloud Run smoke
- Using RiskByPass as generic “anti-bot” for every site
- Putting Bright Data / RiskByPass clients inside thin Actors after worker migration
