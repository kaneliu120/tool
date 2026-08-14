---
name: website-page-research
description: >-
  Research a target website through the user's real Chrome session: surface
  map, data layers, field groups, internal channel contracts, pagination,
  per-surface gates, and coverage matrix; write a Chinese recon report to
  Downloads as hard inputs for Actor/worker work. Use when the user asks to
  调用我的浏览器调研页面, 页面调研分析报告, analyze page structure/fields/APIs,
  recon a site like Glassdoor/Realtor/Shopee/Ticketmaster, or needs measured
  scrape-architecture inputs (not guesses).
---

# Website Page Research (Chrome session → Chinese report)

**Cloud Agent:** no AppleScript Chrome and no `/Users/kane`. Do not call `osascript`
or follow [`../use-my-browser/SKILL.md`](../use-my-browser/SKILL.md) on this VM.
Use the VM desktop / Playwright, or HTTP probes + `scripts/` in this skill.
Write the report under `/tmp` or the workspace — not macOS Downloads.

The product of this skill is **not** a pretty Markdown essay. It is:

1. a **coverage matrix** (markets × categories × services)
2. a **per-surface channel contract** (primary layer, ready signal, identity keys, pager keys, gate)
3. measured **engineering inputs** a worker can implement without re-browsing

Call the user's **real Google Chrome** on macOS (see Cloud Agent note above). Probe live pages, contrast non-browser HTTP, write the report under Downloads (Mac) or `/tmp` (Cloud).

**macOS only:** read and follow [`../use-my-browser/SKILL.md`](../use-my-browser/SKILL.md) first (`chrome_js_bridge.py`, prove-bridge, exact-prefix retarget). **Chrome is one session — never parallel page-context probes** (tabs mix).

Exemplar reports (method, not URL dogma):

- `/Users/kane/Downloads/Shopee页面调研分析报告_2026-08-13.md`
- `/Users/kane/Downloads/Glassdoor页面调研分析报告_2026-07-22.md` (may be archived; lessons in [references/glassdoor-report-lessons.md](references/glassdoor-report-lessons.md))

Before coding a Cloud Run worker, this report must be able to fill `apify-actor-cloud-run-development` §1b coverage. Empty matrix cells stay **未验证** — do not claim full-site coverage.

## When to use

- User says: 调用我的浏览器对某站做页面调研 / 分析页面结构、字段、接口 / 生成调研报告
- Need live evidence of SSR/CSR/RSC/BFF, JSON-LD, DOM `data-test`, internal `/graph`|`/api` **path shapes**
- Planning Actor / worker architecture and need measured inputs (not guesses)

If a vertical pack matches, **read that pack after this file** (do not force sale/rent or jobs tabs onto unrelated sites):

| Pack | When |
|---|---|
| [packs/ticketing.md](packs/ticketing.md) | events, venues, seat maps, ticket checkout |
| [packs/ecommerce.md](packs/ecommerce.md) | marketplace / PDP / category / mall |
| [packs/jobs.md](packs/jobs.md) | job boards, employer reviews/salaries |
| [packs/real-estate.md](packs/real-estate.md) | sale/rent SRP/LDP, agents, map search |
| [packs/food-delivery.md](packs/food-delivery.md) | city lists, store, menu |
| [packs/b2b-catalog.md](packs/b2b-catalog.md) | product/company catalogs, RFQ |

## Hard rules

1. Existing Chrome profile + **dedicated research tab**. Prefer `use-my-browser` helpers.
2. Never click Apply / contact / Reply / lead / payment / permission / 2FA / login submit. Stop and ask.
3. Every JS probe returns `JSON.stringify(...)`; `try/catch`; bound output; redact PII.
4. Cookie **names only**. Prefer keys, counts, testids over page text.
5. Internal channels are **path-shape observations**, never “public APIs”. Record method + query/body **field names** + required **header names** (values redacted).
6. No bypass / CAPTCHA-solving / signature-forge / bulk-scrape playbooks. Engineering = measured inputs only.
7. Label every claim: **已验证 / 部分 / 未验证**. Conclusions: **已确认 / 仅侧证 / 未确认**.
8. Retarget by **exact URL prefix**. Serialize Chrome. Delete `/tmp/*recon*` / probe copies when done.
9. **Do not invent detail IDs.** Derive detail URLs from live list links. Open real sub-routes/overlays, not only the list page.
10. Challenge / pause / verify / EPS pages are **first-class surfaces**. Record symptoms only. Do **not** infer API schemas, selectors, or a named WAF from a challenge shell.
11. Do not stop because `#__NEXT_DATA__` is missing, because HTML contains the brand string, or because bodyLen looks “big enough”. Need a **ready signal** (business keys) and a **negative signal** (pause/verify title).
12. Do not research or write robots.txt / Terms / 合规边界. Sitemap/nav are URL-discovery only, not permission.

## Standard execution (three phases)

Copy and track:

```
Phase 0 — map (parallel OK; prefer non-browser)
- [ ] Time + Chrome bridge prove
- [ ] Fill surface ontology (absent = 本站无)
- [ ] Coverage matrix skeleton (markets × taxonomy × services)
- [ ] HTTP contrast: 3 UAs × each URL class (search vs category vs detail separately)
- [ ] Optional: sitemap / nav live links / Firecrawl Map (仅侧证 — Chrome live links win)

Phase 1 — Chrome deep (strictly serial)
- [ ] One surface at a time: generic_page_probe.js
- [ ] RSC keyword grep when App Router / no __NEXT_DATA__
- [ ] One whitelist action (facet / sort / load-more) → record delta only
- [ ] One live-link detail + any overlay/sub-route
- [ ] Stop on verify/pause/challenge and log that surface

Phase 2 — contract + report
- [ ] Channel contract per probed surface
- [ ] Pagination: which layer actually pages (HTML vs XHR vs JSON-LD)
- [ ] Write Chinese report (outline + worker one-pager)
- [ ] Verify file; delete temp probes
```

Do **not** start Phase 1 DOM archaeology before Phase 0 HTTP contrast. A 200 CSSR shell is not a listing.

### Chrome + time

```bash
date '+%Y-%m-%d %H:%M:%S %Z'
python3 ~/.cursor/skills/use-my-browser/scripts/chrome_js_bridge.py status
python3 ~/.cursor/skills/use-my-browser/scripts/chrome_js_bridge.py js \
  'JSON.stringify({url:location.href,title:document.title,ready:document.readyState,len:document.body?.innerText?.length||0})'
```

Confirm login/session is not stale before recon. After every navigation, **re-run the probe** (fetch hooks die on navigation).

Whitelist actions only: change one facet, change sort, click load-more, open a live-link detail. After each: store **delta** (URL, card count, new XHR path, new gate). Never Apply.

## Surface ontology (fill before browsing)

Mark each row 打开 / 本站无 / 未验证. Do not rename rows to job-board or real-estate labels.

| Code | Meaning | Open |
|---|---|---|
| Home | Default unscrolled shelf | `/` |
| Search / SERP | Typed query | site-native search URL |
| Taxonomy / Category | Browse by category | live nav/cat link |
| Collection / Shelf | Mall, editorial, ranking | if present |
| Entity list | Brand / shop / artist / venue index | if present |
| Detail / LDP | Single object | **live list link only** |
| Detail sub-route / overlay | Tabs, drawers, seatmap, reviews pane | if the product has them |
| Map / geo | Map or nearby | if present |
| Filter/sort chrome | Same page type, different result universe | change **once** |
| Pager surface | Page/cursor/load-more or dedicated pager XHR | verify behavior |
| Auth / verify / pause / challenge | Login wall, traffic verify, queue, pause | **first-class** if it appears |
| Locale / market switch | TLD, language, currency | ≥1 secondary market when the site has them |
| SEO / sitemap assist | City landings, sitemap | templates only, not primary data |

Jobs/real-estate mappings are examples only — see packs.

## Field groups (tick, then fill keys)

Do not invent a free-form field list. Tick groups per surface, then record concrete keys:

| Group | Must answer |
|---|---|
| Identity | Primary key, foreign keys, canonical URL template |
| Title / name | Visible title vs SEO title vs H1 |
| Taxonomy | Category / tags / segment — may be absent from search JSON |
| Economics | Price, currency, fees, strikethrough |
| Availability | In stock, on sale, sold out, queue |
| Geo | Place name, coords path, region id |
| Time | Start/end, timezone, whether date filters are fuzzy |
| Media | Image hash vs URL |
| Reputation | Score, count, login-gated? |
| Seller / org | Shop / employer / venue / promoter |
| Counts | total / maxPages / hasNext (may be missing) |
| Pagination keys | `page` / `cursor` / `newest` / `pagerId` — HTML vs XHR may differ |
| Auth depth | `guest` / `soft-gate` / `hard-block` / `unknown` |
| Raw refs | Stable ids for worker dedupe (not tracking tokens) |

Packs **add** groups; they do not rename these.

## Per-page probe (use the stock script)

Do not write a new probe from scratch. Copy and optionally add `EXTRA_KEYS`:

```bash
SKILL_DIR="$HOME/.cursor/skills/website-page-research"   # same tree: ~/.agents/skills/website-page-research
cp "$SKILL_DIR/scripts/generic_page_probe.js" /tmp/<site>_probe.js
# edit EXTRA_KEYS at top, then:
python3 ~/.cursor/skills/use-my-browser/scripts/chrome_js_bridge.py file /tmp/<site>_probe.js
```

Second pass on App Router / RSC:

```bash
cp "$SKILL_DIR/scripts/rsc_keyword_grep.js" /tmp/<site>_rsc.js
python3 ~/.cursor/skills/use-my-browser/scripts/chrome_js_bridge.py file /tmp/<site>_rsc.js
```

The generic probe already returns: url/title/h1/ready/bodyLen, render family signals, `__NEXT_DATA__` **key shapes** (not the blob), RSC push count + concat size, JSON-LD types, `data-test*` inventory, class stems, controls, detail-link samples, resource host/path shapes, script keyword hits, cookie **names**, gate phrases, captcha iframe count, `EXTRA_KEYS` hits.

Selector policy: `data-test*` / `data-testid` / `itemprop` / aria **over** hashed CSS modules.

Full walk order: [references/data-layer-tree.md](references/data-layer-tree.md).  
Pitfalls: [references/pitfalls.md](references/pitfalls.md).

For every claimed path: **parse → walk → type-check → sample keys → 已验证/部分/未验证**. Sibling keys matter (`pageProps.edpData` vs `pageProps.seatManifest`).

## Non-browser HTTP contrast

Against **each URL class** (Home, Search, Category, Detail — never infer Detail from Search 200):

```bash
bash "$HOME/.cursor/skills/website-page-research/scripts/http_contrast.sh" 'https://example.com/path'
```

Three UAs: python-requests-like, plain curl, browser-like Chrome. Record status, `server`, `cf-ray` / `Cf-Mitigated`, bytes, whether listing-like HTML / hydration keys appear.

`browser_session: works` + `plain_http: 403/challenge` → session / TLS / edge — **not** a parser bug. No captcha iframe still can be a hard block.

Optional Firecrawl `Map` / markdown scrape is **仅侧证**. CSR/BFF sites yield shells; Chrome live links win.

## Pagination / filters

Do not assume `?page=N`. Verify:

- URL change vs same URL + DOM append vs **no pager at all**
- `rel=next`, load-more, infinite scroll, cursor, offset
- Card count before/after one whitelist click
- Whether **JSON-LD** updates (often an SEO floor that does not page)
- Whether XHR pager keys differ from HTML (`page` vs `newest` vs `pagerId`)

Record filter/sort encoding with examples. **Actually change** one filter; do not guess param names (`q` vs `keyword`).

## Write the report

Path:

```text
/Users/kane/Downloads/{Platform}页面调研分析报告_YYYY-MM-DD.md
```

Chinese Markdown. Use [templates/report-outline.md](templates/report-outline.md).

Must include: 已确认/仅侧证/未确认, verification table, ontology map, per-surface contracts, gates, data-architecture table, **12 engineering inputs**, **worker one-pager**, field appendix, gaps.

Contract template: [references/engineering-contract.md](references/engineering-contract.md).

### Engineering inputs (measured only)

1. Preferred data-source order per surface
2. Whether non-browser HTML is enough or a real browser session is required
3. Pagination pattern **and which layer pages**
4. Multi-app / multi-mono / microfrontend forks
5. Login / `contentDepth` / guest vs authenticated field holes
6. Anti-bot symptoms (HTTP vs browser), per surface
7. **Coverage matrix draft** — opened vs 未验证 cells
8. **Suggested ladder** (no bypass): same-origin JSON BFF → TLS-impersonating HTTP → real browser session → hosted browser **only if already production-proven**. Each rung: what this session verified
9. Identity / dedupe keys
10. Hydration **ready** + **negative** signals
11. Market/host forks (geo ignored, short-query 400, page caps)
12. Worker-implemented surfaces vs colder surfaces this session could render (product choice, not a bypass)

### Success bar (another agent must start without re-browsing)

1. Matrix includes Search, Category (if any), Detail, ≥1 market fork, any gate surface seen
2. Each probed surface: primary channel + ready signal + identity shape
3. At least one guessed-vs-measured param (or explicit “filter change verified”)
4. HTTP vs Chrome listed separately; 200 shells are not listings
5. Worker one-pager can paste into a worker README coverage/ladder draft
6. Every 已验证 path was parse → walk → sample keys

## Privacy & safety

- Redact emails, phones, full reviews, person-attached salaries, tracking tokens
- Do not retain raw listing IDs longer than needed for structure proof
- Signature/header Capture that needs js-reverse: stop and say Rebuild has not started — this skill does not forge

## Additional resources

- Bridge: [`../use-my-browser/SKILL.md`](../use-my-browser/SKILL.md)
- Pitfalls: [references/pitfalls.md](references/pitfalls.md)
- Data-layer tree: [references/data-layer-tree.md](references/data-layer-tree.md)
- Engineering contract: [references/engineering-contract.md](references/engineering-contract.md)
- Glassdoor method checks: [references/glassdoor-report-lessons.md](references/glassdoor-report-lessons.md)
- Actor coverage: [`../apify-actor-cloud-run-development/SKILL.md`](../apify-actor-cloud-run-development/SKILL.md) Phase 0 consumes this one-pager (`templates/worker-contract.md`)
- Hermes (optional historical): `~/.hermes/skills/research/job-board-browser-research`, `real-estate-browser-research`, `browser-session-research`
