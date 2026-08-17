# Lessons from Glassdoor report (2026-07-22)

Source exemplar: `/Users/kane/Downloads/Glassdoor页面调研分析报告_2026-07-22.md`

Use these as **method checks** for any site recon — not Glassdoor-only dogma. Cross-site pitfalls (Ticketmaster/Shopee/LinkedIn/…) live in [pitfalls.md](pitfalls.md). The durable recon product is the coverage matrix + channel contract, not a Glassdoor-shaped outline.

## What the report got right (reuse)

1. **Real Chrome + AppleScript JS bridge** as primary evidence; curl/UA matrix as contrast.
2. **Evidence tiers** up front: 已确认 / 仅侧证 / 未确认.
3. **Multi-surface map** (Jobs SERP/LDP + Employer tabs) instead of forcing sale/rent.
4. **Two frontend monos** detected via asset prefixes (`job-search-next` vs `employer-profile-mono`).
5. **Did not stop** when `#__NEXT_DATA__` was missing — found App Router RSC (`self.__next_f.push`) + JSON-LD `JobPosting`.
6. **Selector policy:** `data-test` / JSON-LD over hashed CSS modules.
7. **Internal `/graph`** recorded as path shape + RSC-embedded variables — never called a public API.
8. **Login soft-gates** recorded per surface (`Sign in to unlock…`) with later `contentDepth` updates.
9. **Engineering section** lists measured priorities only — no bypass recipes.
10. **Pagination verified by behavior** (`data-test="load-more"` append) instead of assuming `?page=N`.

## Durable pitfalls (generalize)

| Pitfall | Correct habit |
|---|---|
| Stop when `__NEXT_DATA__` absent | Check RSC `__next_f` concat size + keyword grep |
| Treat CSS module hashes as stable | Prefer `data-test*` / schema.org |
| Assume `?page=N` | Click/observe load-more; compare card counts |
| Call `/graph` a public API | Path + variables observation only |
| Equate “no captcha iframe” with “no protection” | Compare HTTP 403 / TLS fingerprint / cookie names |
| Install persistent `fetch` via AppleScript | Hooks die on navigation; use `performance` + RSC text |
| Guess detail URLs | Derive from live list; RSC regex fallback for ids if DOM links empty |
| Mix tabs mid-run | Retarget by exact URL prefix |
| Over-claim guest preview as full history | Record login state + contentDepth |

## RSC extraction recipe (when App Router)

1. Count scripts containing `self.__next_f.push`.
2. Concatenate push payloads in page order (often 350–600KB+ on heavy sites).
3. Grep for business keys, GraphQL `variables`, header **names** (redact token values in the report).
4. Cross-check against JSON-LD and visible DOM — do not invent fields from a single hit.

## Report quality bar

A finished recon should let an engineer answer without re-browsing:

- Which URL templates are real?
- What is the primary structured data layer per surface?
- What breaks under plain HTTP?
- What is P0 vs P1 to build — with evidence?
