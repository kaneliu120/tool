# Scrape engine evaluation (worker)

> Updated: 2026-07-23  
> Purpose: when developing a Cloud Run worker, **first evaluate** engines against the worker’s requirements, **then default to inheriting** the source Actor’s proven engine and capabilities.

---

## 1. Workflow (mandatory order)

```
Worker requirements
        ↓
Evaluate engines (A historical Actors → B GitHub → C public research)
        ↓
Default: inherit source Actor engine + features
        ↓
Escalate ladder only if measured blocks require it
        ↓
Document decision in worker README → implement
```

1. Clarify worker needs: site/brands, channels, antibot signals, volume, latency, geo/proxy.
2. **Evaluate** with sources A/B/C below (do not skip).
3. **Default inherit** the source Actor’s engine class, warm-up, pagination, enrich, and proxy pattern.
4. Escalate (HTTP → stealth browser → hybrid) only after measuring 403/challenge rates.
5. Write the decision into the worker README, then code.

Canonical pair: `zillow-com` worker + `zillow-scraper` Actor (`curl_cffi` + Apify RESIDENTIAL `proxyUrl`).

---

## 2. Research sources

### A. Historical Actors / workers (primary)

Survey themes from `~/Projects/Apify Actors` + `~/Projects/google run worker`:

| Engine class | Typical defaults in workspace | Efficiency |
| --- | --- | --- |
| **curl_cffi** (Chrome impersonate) | Most RE HTTP Actors; Rightmove, SUUMO, Dot Property, OpenSooq, Property Finder primary, Lazada/TikTok HTTP, ecommerce-scraper, us-real-estate source analysis, **zillow-com** | Fast; sticky RESIDENTIAL; concurrency often 1–3 |
| **httpx / requests API** | Realtor.com GraphQL, Amazon search HTML, Google ATC | Fastest when JSON/API exists |
| **camoufox** | Apartments.com, realtor.ca, Idealista, IS24, SeLoger, Immobiliare, Naver, PropertyGuru, 99.co | Heavy; concurrency 1. On Cloud Run follow [`camoufox-cloud-run`](../camoufox-cloud-run/SKILL.md) (**gen2** + HOME=/tmp seed + external Xvfb + `headless=True`). Do not abandon for Patchright/Bright Data on first crash. |
| **patchright / cloakbrowser** | Bayut, Airbnb, LinkedIn Jobs, Indeed, TikTok browser, 1688 | Chromium stealth; short warm |
| **Playwright + curl hybrid** | Google Maps (PW + curl RPC), Property Finder fallback | Browser only where needed |

**Conclusion:** most successful stacks are self-hosted HTTP or stealth browser + Apify RESIDENTIAL. Prefer copying that tier into the worker.

### B. GitHub / open source (secondary)

| Signal | Source | Takeaway |
| --- | --- | --- |
| curl_cffi ~6k★ | [lexiforest/curl_cffi](https://github.com/lexiforest/curl_cffi) | First-line TLS/JA3/HTTP2 impersonation |
| Camoufox ~10k★ | [daijro/camoufox](https://github.com/daijro/camoufox) | Firefox C++ fingerprint spoof for hard antibot |
| Patchright ~3.8k★ | [Kaliiiiiiiiii-Vinyzu/patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright) | Playwright fork; prefer real Chrome channel when needed |
| Lists / wiki | [awesome-scrapers](https://github.com/edwardtay/awesome-scrapers), [scraping-wiki](https://github.com/TheWebScrapingClub/scraping-wiki) | Impersonated HTTP → stealth browser → residential |

**Conclusion:** default **curl_cffi + residential**; reserve camoufox/patchright for JS/challenge gates.

### C. Public research / X.com (tertiary)

Use indexed public discussion and creator benchmarks when direct X search is gated:

| Theme | Implication |
| --- | --- |
| curl_cffi first for TLS-only gates | Aligns with Actor majority |
| Browser once for clearance, then HTTP volume | Optional hybrid failover |
| Residential IPs required; datacenter dies fast | Keep Apify RESIDENTIAL / `proxyUrl` |
| Pick tool by antibot **layer**, not brand | Record gate type in the audit |

**Conclusion:** same ladder as workspace practice — impersonated HTTP + residential, escalate to stealth browsers on evidence.

---

## 3. Engine ladder

```
0. Native / internal API (GraphQL, Next data, InnerTube, Maps RPC)
1. curl_cffi Session(impersonate="chrome…") + residential proxy
   (+ homepage warm-up / sticky session when needed)
2. Stealth browser: camoufox OR patchright/cloakbrowser
3. Hybrid: browser clearance cookies → curl_cffi volume
```

| Site signal | Prefer |
| --- | --- |
| SSR / `__NEXT_DATA__` / search JSON | curl_cffi |
| Soft TLS bot score | curl_cffi + residential + warm |
| DataDome / Firefox-favored | camoufox (if Actor already uses it) |
| Proven Chromium Actor stack | patchright / cloakbrowser |
| Actor already stable on engine X | **keep X** |

| Engine | Relative cost | Typical concurrency |
| --- | --- | --- |
| API / httpx | 1× | higher |
| curl_cffi | ~1–1.2× | 1–5 |
| camoufox / patchright | ~8–20× | 1 |

---

## 4. Pre-implementation audit checklist

Before writing worker code:

1. Locate source Actor (Store pull / `_source-analysis/` / local clone).
2. Record **requirements**: brands, channels, geo, antibot notes.
3. Record **Actor engine** (`requirements.txt`, impersonate, browser launch, GraphQL).
4. Record **proxy** (RESIDENTIAL, country, sticky).
5. Record **capabilities** to preserve: channels, filters, pagination, enrich, warm-up.
6. Score efficiency: requests/listing, concurrency, API vs HTML.
7. Cross-check §2 A/B/C — any cheaper rung that still matches success mode?
8. Write README decision:

```text
Engine evaluation:
  A (historical): ...
  B (GitHub): ...
  C (public/X): ...
Default provider: curl   # or camoufox / patchright / httpx
Inherited from: <actor-name> (<engine>)
Proxy: Actor RESIDENTIAL → proxyUrl (fallback PROXY_URL)
```

9. Implement worker default = that decision. Thin Actor passes `provider` + `proxyUrl` over **authenticated HTTPS** (see reference.md security section).

---

## 5. Worker env (engine / proxy)

| Variable / field | Meaning |
| --- | --- |
| `SCRAPE_PROVIDER` | Inherited default (`curl` / `camoufox` / `patchright` / `httpx`) |
| Request `provider` | Optional per-call override |
| `proxyUrl` | Preferred; from Actor Apify RESIDENTIAL |
| `PROXY_URL` | Deploy smoke fallback |

Failover: same-engine retry / sticky rotate → optional stealth browser. Keep chains documented in README.

---

## 6. Unlock / Kasada vendors

When evaluation points to **Bright Data** (Web Unlocker / Scraping Browser) or **RiskByPass** (Kasada), follow the personal skill [`bright-data-riskbypass`](../bright-data-riskbypass/SKILL.md) for env names, CDP/API call shapes, and measured fit (e.g. Shopee → Scraping Browser; REA → Unlocker ± RiskByPass).
