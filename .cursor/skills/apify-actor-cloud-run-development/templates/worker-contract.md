# Worker contract (Phase 0 — start-work license)

Paste from `website-page-research` **给 worker 的一页纸**, or fill from a live recon in this session.  
**No file / empty primary channels → do not write `collector.py` / parse, do not claim Cloud Run ready.**

Vertical field lists: `~/.cursor/skills/website-page-research/packs/` (ticketing, ecommerce, jobs, real-estate, food-delivery, b2b-catalog). Do not duplicate them here.

Copy this file into the worker repo as `docs/worker-contract.md`.

---

## Identity

| | |
| --- | --- |
| Site | |
| Worker dir | `/Users/kane/Projects/google run worker/<service>/` |
| Actor dir | `/Users/kane/Projects/Apify Actors/<actor>/` |
| Cloud Run service / `workerId` | |
| Region (site geography) | |
| Recon report | path or “session-measured” |

## Coverage matrix

Use [coverage-matrix.md](coverage-matrix.md). Empty cells stay **未验证**.

## Per-surface channel (copy one block per opened surface)

```text
Surface: {Search | Category | Detail | Overlay | Market switch}
Final URL template:
Market / host:
Primary channel: {same-origin BFF | RSC | __NEXT_DATA__ | GraphQL | DOM}
Path / headers (names only):
Identity keys:
Pagination:
Ready signal: {keys + approx bytes}
Negative signal: {pause / verify / EPS}
Gate: {guest | soft | hard | unknown}
Suggested ladder rung: {curl_cffi | camoufox | patchright | orch CDP | Unlocker last}
Validation: {已验证 | 部分 | 未验证}
```

## Ladder (measured this session only)

```text
Default:
Escalate when:
Do not fallback: {e.g. BFF 400 must not HTML-fallback}
Unlocker: {still on as last auto rung | N/A — never “drop because pin worked”}
```

## Smoke

Random inputs draw from **opened** cells only. Spot-check ≥1 secondary market and ≥1 non-primary category when those cells are open.

```text
python3 $SKILL/scripts/random_smoke_input.py --matrix ./coverage-matrix.json --out /tmp/accept.json
```

## Do not

- Ship MVP / single-market as done without Kane waiver
- Treat JSON-LD as a pager
- Nest Geonode under orch CDP
- Put admin egress key on Cloud Run
