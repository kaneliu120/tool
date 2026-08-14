# Cross-site recon pitfalls

Method checks for every site. Evidence from Kane sessions (Ticketmaster, Shopee, Glassdoor, LinkedIn, DoorDash, Faire, Coupang, SeatGeek, MonotaRO, Xometry). Details stay in Mem0; this file is the durable habit list.

| Pitfall | Correct habit |
|---|---|
| Stop when `__NEXT_DATA__` absent | Check RSC `__next_f` concat size + keyword grep; then other families (pcmall, Gatsby `page-data.json`, Nuxt, Mosaic…) |
| Treat CSS module hashes as stable | Prefer `data-test*` / schema.org / aria |
| Assume `?page=N` | Observe load-more / cursor / **no pager**. Coupang: `?page=` ignored and DOM has no real pager |
| Call `/graph` or `/api` a public API | Path + method + field **names** + header **names** only |
| Equate “no captcha iframe” with “no protection” | Compare HTTP 403 / TLS / cookie names / client redirect to `/verify` |
| Install persistent `fetch` via AppleScript | Hooks die on navigation; use `performance` + RSC text; re-probe after nav |
| Guess detail URLs | Derive from live list; open overlays (`details/experience`) not only SERP |
| Mix Chrome tabs / parallel probes | One session; serialize; retarget by exact URL prefix |
| Over-claim guest preview as full data | Record `guest \| soft-gate \| hard-block` + which field groups are empty |
| Use brand string / small HTML as EDP success | Ready = hydration keys (e.g. `__NEXT_DATA__` + `edpData`). Pause pages also contain the brand; ~160KB will not self-heal |
| Eat the full rehydration blob | Stable DOM first; narrow pager payloads (`pagerId` / `screenId`) separately |
| Guess search param names | Change a filter once. Ticketmaster BFF: `q` not `keyword`; missing 4 TM headers → 404; wrong param → 400 — do not HTML-fallback a 400 |
| Infer Detail gate from Search 200 | SeatGeek list vs EDP DataDome; Shopee category OK vs Search/PDP type=4; TM list vs EPS |
| Treat JSON-LD ItemList as the list | Shopee category: ~10 SEO items, does not page; DOM cards ~40 |
| Assume one host’s geo/query rules apply globally | TM lat/long filter only us+ca; au short `q` 400 |
| Flatten nested JSON-LD arrays | DoorDash `Menu.hasMenuSection` is `[[{hasMenuItem}]]` |
| Put sibling hydration keys in the wrong parent | TM `seatManifest` is a `pageProps` sibling of `edpData` |
| Parallelize Chrome `execute javascript` | Parallelize HTTP contrast and URL mapping only |
| Firecrawl markdown / Map as 已验证 | 仅侧证; CSR shells look complete |
| Write bypass / Unlocker / signature recipes | Engineering section = measured ladder candidates only |
| Claim coverage from one market | Fill matrix; secondary TLD/locale stays 未验证 until opened |
| Early-abort large HTML as “still pause” | Pause stays small; 700KB+ is often hydration in progress — aborting throws away a finished EDP |

## Chrome discipline (LinkedIn)

- Confirm login / stale session before recon
- Trust JSON probe dumps over screenshots
- Filter verification = actually toggle geo/company/school/start-count and diff URL vs request body

## Ladder notes (no bypass)

Record what **this session** reached:

- Same-origin JSON BFF (custom headers) 
- TLS-impersonating HTTP
- User Chrome session
- Hosted browser — only if already production-proven for this site

Do not call orchestrator `/v1/unlock` a first-party unlock when it still burns a third-party unlocker. Do not drop a last-rung unlocker because a pin path worked once.
