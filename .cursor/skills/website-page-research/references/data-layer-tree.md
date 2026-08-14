# Data-layer decision tree

Walk **per surface**. Do not reuse Search conclusions for Detail. Stop at the first **validated** primary path, but still record weaker layers as 仅侧证.

For every claimed path: parse → walk → type-check → sample keys → **已验证 / 部分 / 未验证**.

## 0. Challenge / pause / verify shell

If title/URL/body is login-required, traffic verify, EPS pause, queue, or captcha:

- Record URL, title, bodyLen, cookie **names**, iframe count
- **Do not** infer APIs, selectors, pagination, or a named WAF from the shell
- This surface is first-class in the report, not a footnote

## 1. Framework family (extend this table; do not assume Next)

| Family | Signals | Notes |
|---|---|---|
| Next Pages | `script#__NEXT_DATA__` → `props.pageProps` | Walk **sibling** keys under `pageProps`, not only the first nested object |
| Next App Router / RSC | `self.__next_f.push` count + concat size | Missing `__NEXT_DATA__` is normal. Concat often 350–600KB+. Grep keys; **do not** paste the blob |
| Module federation / microfrontends | `page-manifest`, many `pcmall-*` / similar | Not Next. Shell HTML has 0 business ids |
| Gatsby | `/page-data/{path}/page-data.json` | May coexist with Next on other routes |
| Nuxt | `__NUXT__` | |
| Platform-specific | Mosaic, Argonaut, UFRN, IS24, … | Check **before** generic Next |
| Astro / mixed | JSON-LD Product + modern islands | |
| Pure CSR shell | HTTP 200, no identity keys in HTML | Cards only after Chrome JS |

Do **not** stop because Next is absent. Do **not** treat `innerText` containing the brand as hydration.

## 2. Same-origin BFF / JSON

If `/api/*`, `/graph`, `/graphql`, `/_next/data/` appear in `performance` or bundles:

- Path + HTTP method
- Query / JSON **field names** (measure; do not guess `keyword` vs `q`)
- Required **header names** harvested from the app bundle (values redacted)
- Status machine: 404 vs 400 vs 401 `identify` vs 403 vs 200
- Whether 400 (bad params) must **not** fall through to the HTML ladder

Same-origin JSON with custom headers can be an order of magnitude cheaper than a browser EDP. Record it as a ladder candidate only if this session (or an existing worker) actually got a business-shaped body.

## 3. Hydration object walk

- Top-level `pageProps` (or equivalent) **key list**
- Nested business objects + **siblings** (e.g. `edpData` beside `seatManifest`, not inside it)
- Ready signal: required keys present **and** plausible size
- Negative signal: pause/verify title, tiny HTML (~160KB pause vs ~700KB+ hydrated on some EDPs)

## 4. JSON-LD (`application/ld+json`)

Record `@type` list and top-level key shapes (`JobPosting`, `ItemList`, `Product`, `Menu`…).

JSON-LD is often an **SEO floor**:

- Strong on some LDPs
- On category pages may be a fixed N items that **do not page**
- Nested arrays may be double-wrapped (e.g. `hasMenuSection: [[{...}]]`) — type-check depth

Never call JSON-LD the list data source until paging updates it.

## 5. Window globals

`window.__*` / app config / nav objects. Names + key shapes, not full dumps.

## 6. Internal channel path shapes

From `performance` + script scans. Host + path prefixes only. Do not invent unobserved endpoints. Do not call them public APIs.

## 7. DOM fallback

Prefer `data-test*` / `data-testid` / `itemprop` / aria / semantic class stems. Hashed CSS modules (`JobCard_title__xxxx`, `css-*`) are evidence, not recommended selectors.

## Ready vs success

| Bad proxy for “got the page” | Use instead |
|---|---|
| Brand string in HTML | Business keys (`edpData`, `itemid`, mosaic jobcards, …) |
| `readyState === complete` | Keys + not a challenge title |
| bodyLen “looks big” | Compare pause-size vs hydrated-size for this site |
| HTTP 200 | Listing-like HTML **or** JSON with identity keys |
| No captcha iframe | Still record HTTP 403 / TLS / cookie names |
