# Thin Actor compute cost (Apify run options)

Kane’s thin Actors are **HTTP clients** to Cloud Run. Wall-clock time is almost
entirely **waiting on the worker**. Apify **compute units (CU)** still scale with
**allocated memory × runtime**, so oversized Actor memory wastes money without
speeding scrapes.

## Why it matters (two bills)

| Bill | Who pays (typical Kane PPE) | How memory hurts |
| --- | --- | --- |
| **Platform CU** | Developer when `isPPEPlatformUsagePaidByUser` is `false` / `null` (“User pays platform usage = No”) | CU ≈ `(memoryGB) × (runTimeHours)` — linear in memory |
| **PPE `apify-actor-start`** | End user | **One start event per GB, minimum one** — **2048 MB → 2× start charge** |

Do **not** leave thin Actors on Apify’s implicit **4096 MB** default (brain gotcha:
“4GB = 16× compute waste”). Do **not** default thin worker-backed Actors to
**2048 MB** without a measured reason.

## Defaults (new / refactored thin Actors)

| Field | Robust default | Aggressive (after smoke) | Notes |
| --- | --- | --- | --- |
| `defaultRunOptions.memoryMbytes` | **1024** | **512** | Align with seek / glassdoor / funda / otodom / finn |
| `minMemoryMbytes` | **512** | **256–512** | Allow Console/API override down |
| `maxMemoryMbytes` | **4096** (or **2048**) | — | Cap abuse; no need for 8GB on thin HTTP |
| `defaultRunOptions.timeoutSecs` | **3600** (or **1800**) | — | Must stay **>** `worker_client` HTTP timeout (often 600–850s) |
| Standby `memoryMbytes` | **≤ run default** (usually **1024**, optional **512**) | — | Live View is also thin |

```json
"defaultRunOptions": {
  "build": "latest",
  "timeoutSecs": 3600,
  "memoryMbytes": 1024
},
"minMemoryMbytes": 512,
"maxMemoryMbytes": 4096
```

**Cloud Run worker** memory (`--memory=2Gi` / browser `4Gi`) is a **separate**
bill — do not confuse it with Actor `memoryMbytes`.

## Cost tune without redeploy (preferred for memory-only)

Changing **only** remote `defaultRunOptions` does **not** require `apify push` or
a new build:

1. `GET /v2/acts/{id}` → read `defaultRunOptions`
2. `PUT /v2/acts/{id}` with `{ "defaultRunOptions": { ...memoryMbytes: 1024 } }`
3. Re-read and confirm
4. Smoke **without** forcing high `-m` (omit `-m` or use `-m 1024`)

**Always align local files** so the next push does not revert:

- `.actor/actor.json` → same `memoryMbytes` / `minMemoryMbytes`
- Any `scripts/configure_store.py` that hard-codes `memoryMbytes` → same value

Standby / PPE prices / worker deploy can stay untouched for a memory-only tune.

## Smoke / acceptance checks

When verifying cost defaults:

```bash
# Prefer Actor default (after remote PUT) — do NOT pass -m 2048
apify call "<user>/<actor>" -b latest -f /tmp/accept.json -t 900

# Or explicitly match the robust default
apify call "<user>/<actor>" -b latest -f /tmp/accept.json -m 1024 -t 900
```

Assert from run API / Console:

- `options.memoryMbytes` equals the intended default  
- `SUCCEEDED` + rows ≥ 1  
- Record `stats.computeUnits` + `runTimeSecs` in handoff for before/after

Rough check: same wall time at half memory ≈ **half CU**.

## Analysis workflow (when Kane asks “optimize run cost”)

1. Confirm Actor is thin (no browser in image; `WORKER_BASE_URL` path).  
2. Read remote `defaultRunOptions` + Standby memory + recent run `memoryMbytes` / CU.  
3. Compare peer thin Actors (1024 / min 512).  
4. Propose **robust 1024** (API-only) vs **aggressive 512** (needs smoke).  
5. Apply only after Kane confirms; write Mem0 handoff with run id + CU.

## Proven example (walmart-scraper, 2026-07-27)

| | Before | After (no rebuild) |
| --- | --- | --- |
| Default memory | 2048 MB | **1024 MB** |
| Build | 0.1.13 | **same** 0.1.13 |
| Smoke | — | `N61Xgc9T1Q65Jvgmg` SUCCEEDED, CU ≈ **0.023** @ ~84s |
| Prior 2GB catalog CU | ~0.043 @ ~78s | ~half expected |

## Related gotchas

- CLI `apify call -m 2048` **overrides** Actor default — smokes can lie about cost.  
- `apify actors info --json` may break on huge `sourceFiles`; use HTTP GET + token or text `apify actors info`.  
- Unused pins (e.g. `browserforge` only for crawlee compat) do not justify 2GB RAM.  
- PPE README examples that assume **one** start event are wrong if default memory ≥ 2048 MB.
