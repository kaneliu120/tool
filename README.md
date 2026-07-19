# REA Kasada HTML Unblocker Toolkit

Self-hosted acquisition layer for `realestate.com.au`: **Provider Gateway + classifier + contract tests + Kasada recorder + Mac runner adapter**.

This repository implements the Phase 0 / MVP from the internal REA-Kasada research plan. It deliberately does **not** make Apify Linux/Xvfb the default path.

## Verified facts (2026-07-19)

- REA listing data lives in `window.ArgonautExchange` → `urqlClientCache` (ScrapFly-aligned parser kept frozen).
- Direct HTTP from this environment returns **HTTP 429** and a **~715B KPSDK shell** (`window.KPSDK` + `ips.js` + `KP_UIDz`).
- Product bottleneck is HTML acquisition environment, not the parser.

See:

- `docs/AUDIT_CROSS_VERIFICATION.md`
- `docs/PRODUCT_PLAN.md`
- `config/rea-target-profile.yaml`

## Layout

```text
src/rea_unblocker/
  classifier/     # classify_html (KPSDK / Argonaut)
  providers/      # FetchResult, mock, remote Mac/Windows runners, registry
  gateway/        # FastAPI POST /v1/fetch-html
  parser/         # frozen ArgonautExchange parser
  recorder/       # Kasada challenge probe (no solver)
  actor/          # Apify Actor client + RUN_SUMMARY
  runner/         # Mac Chrome runner skeleton
```

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# unit + contract tests
pytest -q

# 4-URL contract harness (fixture provider)
python scripts/test_html_provider.py --provider mock_fixture

# local actor canary
python scripts/run_canary_local.py

# record a live Kasada shell (observability only)
python scripts/kasada_probe_rea.py

# start gateway with mock provider for local integration
REA_INCLUDE_MOCK=1 uvicorn rea_unblocker.gateway.app:app --port 8080
```

## Production wiring

| Env var | Purpose |
|---|---|
| `REA_MAC_RUNNER_URL` | Base URL of Mac Chrome runner (`POST /v1/fetch`) |
| `REA_MAC_RUNNER_TOKEN` | Bearer token for Mac runner |
| `REA_WIN_RUNNER_URL` | Windows runner URL |
| `REA_GATEWAY_TOKEN` | Gateway auth token |
| `REA_INCLUDE_MOCK` | `1` enables fixture provider (dev/CI only) |

Provider priority for REA:

1. `internal_mac_runner`
2. `internal_windows_runner`
3. fail closed

Forbidden defaults: Apify Xvfb Chrome, Camoufox-for-REA.

## Closed-loop status

| Gate | Status |
|---|---|
| Document audit + cross-check | Done |
| FetchResult / classify_html / gateway | Done |
| 4-URL contract tests (fixture) | Done |
| Kasada shell recorder (live) | Done |
| Mac hardware canary | Pending (needs macOS host) |
| Apify remote `maxItems=2` | Pending (needs Actor deploy + runner) |

## Safety

- Domain allowlist: `*.realestate.com.au` only
- Fail closed on KPSDK shells / missing Argonaut
- Recorder stores challenge samples; it does **not** implement a Kasada solver
