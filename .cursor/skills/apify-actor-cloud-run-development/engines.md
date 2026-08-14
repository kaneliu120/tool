# Scrape engine evaluation (worker)

> Updated: 2026-08-14  
> Parent: [SKILL.md](SKILL.md)
> Purpose: when developing a Cloud Run worker, **first read the Phase 0 recon channel contract**, then evaluate engines, **then default to inheriting** the source Actor’s proven engine as a **floor**. Stars do not beat measured BFF/RSC/DOM. Egress: [egress-control.md](egress-control.md) §8. Recon: [`../website-page-research/SKILL.md`](../website-page-research/SKILL.md).

---

## 1. Workflow (mandatory order)

```
Phase 0 recon contract (channels, per-surface gates, ready/negative signals)
        ↓
Evaluate engines (A historical Actors → B GitHub typology → C public research)
        ↓
Default: inherit source Actor engine + features (floor, not ceiling)
        ↓
Escalate ladder only if measured blocks require it
        ↓
Document decision in worker README → implement
```

0. **Recon contract first** ([templates/worker-contract.md](templates/worker-contract.md)): primary channel per surface (same-origin BFF / RSC / DOM), Search vs Detail gates, ready vs pause signals. No contract → no engine decision.
1. Clarify worker needs: site/brands, channels, antibot signals, volume, latency, geo/proxy.
2. **Evaluate** with sources A/B/C below (do not skip). GitHub star counts never override a measured BFF.
3. **Default inherit** the source Actor’s engine class, warm-up, pagination, enrich, and proxy pattern as a **floor**. Source skipping a market does not cap §1b.
4. Escalate only after measuring 403/challenge / empty-hydration rates.
5. Write the decision into the worker README, then code.

Canonical pair: `zillow-com` worker + `zillow-scraper` Actor (`curl_cffi` + **worker-owned egress** via egress-control / `PROXY_URL`; Actor `WORKER_PROVIDES_PROXY=1`).

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
| Fetcher typology (not a runtime) | [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling) | HTTP / TLS impersonation / dynamic browser = **labels** for this ladder. Do **not** add Scrapling as a Cloud Run dependency |
| URL map (Phase 0 仅侧证) | Firecrawl Map | Discover candidate paths for the coverage matrix. Do **not** treat the map as 已验证; do **not** run Firecrawl as the worker |

**Conclusion:** default **curl_cffi + residential**; reserve camoufox/patchright/orch CDP for JS/challenge gates. Do not ship Crawlee/Firecrawl/Scrapling inside Kane workers.

### C. Public research / X.com (tertiary)

Use indexed public discussion and creator benchmarks when direct X search is gated:

| Theme | Implication |
| --- | --- |
| curl_cffi first for TLS-only gates | Aligns with Actor majority |
| Browser once for clearance, then HTTP volume | Optional hybrid failover |
| Residential IPs required; datacenter dies fast | Keep residential via **egress-control** / worker `PROXY_URL` (not Actor mint by default) |
| Pick tool by antibot **layer**, not brand | Record gate type in the audit |

**Conclusion:** same ladder as workspace practice — impersonated HTTP + residential, escalate to stealth browsers on evidence.

---

## 3. Engine ladder

```
0. Native / same-origin JSON (GraphQL, BFF, RSC payload, __NEXT_DATA__, InnerTube)
1. curl_cffi Session(impersonate="chrome…") + residential proxy
   (+ homepage warm-up / sticky session when needed)
2. Stealth browser: camoufox OR patchright/cloakbrowser
3. Hosted Chrome CDP via orchestrator (orch.opendata.best /v1/sessions/lease)
   — own residential; NOT orch /v1/unlock (that path may still be Bright Data)
4. Hybrid: browser clearance cookies → curl_cffi volume
5. Unlocker last auto-ladder rung if already production-proven
   — do not disable fleet-wide because a provider=orchestrator pin worked once
```

| Site signal | Prefer |
| --- | --- |
| SSR / `__NEXT_DATA__` / search JSON / same-origin BFF | curl_cffi |
| Soft TLS bot score | curl_cffi + residential + warm |
| DataDome / Firefox-favored | camoufox (if Actor already uses it) |
| Proven Chromium Actor stack | patchright / cloakbrowser |
| CF / hydration needs real Chrome, BD browser too heavy | orchestrator CDP (Ticketmaster-measured) |
| Actor already stable on engine X | **keep X** as floor |

| Engine | Relative cost | Typical concurrency |
| --- | --- | --- |
| API / httpx | 1× | higher |
| curl_cffi | ~1–1.2× | 1–5 |
| camoufox / patchright | ~8–20× | 1 |

---

## 4. Pre-implementation audit checklist

Before writing worker code:

0. Phase 0 contract exists (channels + gates + ready/negative). Else stop.
1. Locate source Actor (Store pull / `_source-analysis/` / local clone).
2. Record **requirements**: brands, channels, geo, antibot notes.
3. Record **Actor engine** (`requirements.txt`, impersonate, browser launch, GraphQL).
4. Record **proxy / unlock** plan: egress-control `workerId`, residential country/sticky, Unlocker/Browser/Kasada/CapSolver if needed.
5. Record **capabilities** to preserve: channels, filters, pagination, enrich, warm-up.
6. Score efficiency: requests/listing, concurrency, API vs HTML.
7. Cross-check §2 A/B/C — any cheaper rung that still matches success mode?
8. Write README decision:

```text
Engine evaluation:
  A (historical): ...
  B (GitHub): ...
  C (public/X): ...
Default provider: curl   # or camoufox / patchright / httpx / orchestrator
Inherited from: <actor-name> (<engine>)  # floor, not coverage ceiling
Recon channels: Search=… Detail=… (from worker-contract.md)
Proxy: worker egress-control → PROXY_URL / provider (Actor WORKER_PROVIDES_PROXY=1)
Egress workerId: <service-name>
Unlocker: still on as last auto rung | N/A
```

9. Implement worker default = that decision. Thin Actor passes `provider` over **authenticated HTTPS**; **omit `proxyUrl`** when worker-owned (see [egress-control.md](egress-control.md)).

---

## 5. Worker env (engine / proxy)

| Variable / field | Meaning |
| --- | --- |
| `EGRESS_CONTROL_BASE_URL` | `https://worker.opendata.best` (required for new workers) |
| `EGRESS_CONTROL_API_KEY` | Control-plane **runtime** key (not admin) |
| `EGRESS_CONTROL_WORKER_ID` | Cloud Run service name |
| `SCRAPE_PROVIDER` | Inherited default (`curl` / `camoufox` / `patchright` / `httpx`) |
| Request `provider` | Optional per-call override |
| `PROXY_URL` | Fallback / local smoke; usually filled by `apply_runtime_env` |
| Request `proxyUrl` | Optional override; **not** the new-Actor default path |

Failover: same-engine retry / sticky rotate → optional stealth browser / Unlocker. Keep chains documented in README. Prefer control-plane policy changes over editing 40+ workers.

**Provider × engine (do not skip):** Oxylabs dedicated ≠ CloakBrowser/Camoufox; Apify GOOGLE_SERP ≠ Maps; Apify username commas must stay literal for Camoufox; wipe stale `PROXY_COUNTRY` on dedicated. Full matrix + worker checklist: [egress-control.md §8](egress-control.md).

---

## 6. Unlock / Kasada vendors

When evaluation points to **Bright Data** (Web Unlocker / Scraping Browser), **RiskByPass** (Kasada), or CapSolver, follow [`bright-data-riskbypass`](../bright-data-riskbypass/SKILL.md) for **product fit**, env **names**, CDP/API shapes, and measured notes (e.g. Shopee → Scraping Browser; REA → Unlocker ± RiskByPass).

**Credentials and per-worker policy** live in **egress-control** (`worker.opendata.best`). Optional Cloud Run env remains fallback only — do not treat per-worker Secret sprawl as the primary path for new services.
