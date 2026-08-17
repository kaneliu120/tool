# Apify free-tier limits — templates

Reference Actor: `/Users/kane/Projects/Apify Actors/linkedin-jobs-scraper`

## `src/errors.py` addition

```python
class FreeTierLimitError(ActorError):
    """Free Apify-plan usage limit reached (developer policy, not a platform bug)."""
```

## `src/free_tier.py` skeleton

Tune constants per Actor. Keep detection + clamp + enforce API stable.

```python
"""Free Apify-plan limits. Console has no N-runs toggle — enforce here."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from src.errors import FreeTierLimitError

logger = logging.getLogger(__name__)

FREE_MAX_RUNS = 10
FREE_MAX_RESULTS = 1000
STATE_STORE_NAME = "my-actor-free-tier"  # unique per Actor

RUN_LIMIT_MESSAGE = (
    f"Free Apify plan limit reached: this Actor allows {FREE_MAX_RUNS} runs for free-plan users "
    f"(up to {FREE_MAX_RESULTS} results per run). This limit was set by the Actor developer, not Apify. "
    "Upgrade to a paid Apify plan to continue with unlimited runs."
)
RESULTS_NOTE = (
    f"Free Apify plan: maxResults capped at {FREE_MAX_RESULTS} per run "
    "(set by the Actor developer)."
)


@dataclass(frozen=True)
class FreeTierPlan:
    is_limited: bool
    effective_max_results: int
    prior_runs: int
    max_runs: int = FREE_MAX_RUNS
    max_results: int = FREE_MAX_RESULTS
    results_clamped: bool = False


def _env_flag(name: str) -> bool:
    return str(os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def is_paying_user(actor: Any) -> bool:
    if _env_flag("FORCE_FREE_TIER"):
        return False
    if _env_flag("FREE_TIER_DISABLED"):
        return True
    try:
        if not actor.is_at_home():
            return True
    except Exception:
        if not _as_bool(os.getenv("APIFY_IS_AT_HOME")):
            return True
    if str(os.getenv("APIFY_META_ORIGIN") or "").strip().upper() == "TEST":
        return True
    try:
        paying = getattr(actor.configuration, "user_is_paying", None)
        if paying is not None:
            return _as_bool(paying)
    except Exception:
        pass
    return _as_bool(os.getenv("APIFY_USER_IS_PAYING"))


def clamp_max_results(requested: int, *, is_limited: bool) -> tuple[int, bool]:
    requested = max(1, int(requested))
    if not is_limited:
        return requested, False
    effective = min(requested, FREE_MAX_RESULTS)
    return effective, effective < requested


def _count_prior_runs_via_api(actor: Any, actor_id: str, current_run_id: str) -> int | None:
    if not actor_id:
        return None
    try:
        counted = 0
        offset = 0
        page_size = 100
        while True:
            page = actor.apify_client.runs().list(limit=page_size, offset=offset, desc=True)
            items = list(getattr(page, "items", None) or [])
            if not items:
                break
            for run in items:
                act = (
                    (run.get("actId") if isinstance(run, dict) else None)
                    or getattr(run, "act_id", None)
                    or ""
                )
                rid = (run.get("id") if isinstance(run, dict) else None) or getattr(run, "id", None) or ""
                if str(act) != actor_id:
                    continue
                if rid and str(rid) == current_run_id:
                    continue
                counted += 1
                if counted >= FREE_MAX_RUNS:
                    return counted
            total = getattr(page, "total", None)
            if total is not None and offset + len(items) >= int(total):
                break
            if len(items) < page_size:
                break
            offset += page_size
            if offset > 2000:
                break
        return counted
    except Exception as exc:
        logger.warning("Free-tier run count via API failed: %s", exc)
        return None


async def _read_kv_count(actor: Any, user_id: str) -> int:
    try:
        store = await actor.open_key_value_store(name=STATE_STORE_NAME)
        state = await store.get_value(user_id)
        if isinstance(state, dict):
            return max(0, int(state.get("runCount") or 0))
    except Exception as exc:
        logger.warning("Free-tier KV read failed: %s", exc)
    return 0


async def _write_kv_count(actor: Any, user_id: str, run_count: int) -> None:
    try:
        store = await actor.open_key_value_store(name=STATE_STORE_NAME)
        await store.set_value(
            user_id,
            {
                "runCount": run_count,
                "maxRuns": FREE_MAX_RUNS,
                "maxResultsPerRun": FREE_MAX_RESULTS,
            },
        )
    except Exception as exc:
        logger.warning("Free-tier KV write failed: %s", exc)


async def enforce_free_tier(actor: Any, requested_max_results: int) -> FreeTierPlan:
    if is_paying_user(actor):
        effective, clamped = clamp_max_results(requested_max_results, is_limited=False)
        return FreeTierPlan(
            is_limited=False,
            effective_max_results=effective,
            prior_runs=0,
            results_clamped=clamped,
        )

    cfg = actor.configuration
    actor_id = str(getattr(cfg, "actor_id", None) or os.getenv("APIFY_ACTOR_ID") or "")
    run_id = str(getattr(cfg, "actor_run_id", None) or os.getenv("APIFY_ACTOR_RUN_ID") or "")
    user_id = str(getattr(cfg, "user_id", None) or os.getenv("APIFY_USER_ID") or "anonymous")

    api_count = _count_prior_runs_via_api(actor, actor_id, run_id)
    kv_count = await _read_kv_count(actor, user_id)
    prior_runs = max(api_count if api_count is not None else 0, kv_count)

    if prior_runs >= FREE_MAX_RUNS:
        raise FreeTierLimitError(RUN_LIMIT_MESSAGE)

    await _write_kv_count(actor, user_id, prior_runs + 1)

    effective, clamped = clamp_max_results(requested_max_results, is_limited=True)
    return FreeTierPlan(
        is_limited=True,
        effective_max_results=effective,
        prior_runs=prior_runs,
        results_clamped=clamped,
    )
```

### Harder anti-tamper (optional)

User-owned named KV can be deleted by the user. For stricter counters, store state on **your** account with a secret token env (`FREE_TIER_STATE_TOKEN` / scoped API token) and key by `APIFY_USER_ID`. Prefer a token restricted to that one KV store.

## `main.py` wiring

```python
from src.errors import FreeTierLimitError
from src.free_tier import FREE_MAX_RESULTS, FREE_MAX_RUNS, RESULTS_NOTE, enforce_free_tier

async def main() -> None:
    async with Actor:
        try:
            config = parse_input(await Actor.get_input() or {})

            free_plan = await enforce_free_tier(Actor, config.max_results)
            config.max_results = free_plan.effective_max_results
            if free_plan.is_limited:
                await Actor.set_status_message(
                    f"Free Apify plan: run {free_plan.prior_runs + 1}/{free_plan.max_runs}, "
                    f"up to {free_plan.effective_max_results} results this run."
                )
            if free_plan.results_clamped:
                await Actor.set_status_message(RESULTS_NOTE)

            # ... proxy + call_worker with clamped max_results ...

            pushed = 0
            for row in items:
                if pushed >= free_plan.effective_max_results:
                    break
                await Actor.push_data(row)
                pushed += 1

            await Actor.set_value("RUN_SUMMARY", {
                ...,
                "freeTierLimited": free_plan.is_limited,
                "freeTierPriorRuns": free_plan.prior_runs,
                "freeTierMaxRuns": free_plan.max_runs,
            })

        except FreeTierLimitError as exc:
            message = str(exc).replace("\n", " ").strip()
            await Actor.set_value("RUN_SUMMARY", {
                "status": "FREE_TIER_LIMIT",
                "message": message,
                "freeTierMaxRuns": FREE_MAX_RUNS,
                "freeTierMaxResults": FREE_MAX_RESULTS,
            })
            await Actor.set_status_message(message)
            return  # graceful SUCCEEDED — not Actor.fail
```

## Copy snippets

### input_schema top-level

```json
"description": "Free Apify plan users: up to 10 runs of this Actor and up to 1,000 results per run. These limits are set by the Actor developer (not Apify). Upgrade to a paid Apify plan for unlimited runs."
```

### maxResults field

```json
"maxResults": {
  "title": "Max results (max 1,000; free users capped at 1,000/run)",
  "description": "Maximum results this run (1–1,000). Free Apify plan users: also limited to 10 total runs of this Actor (Actor developer policy)."
}
```

### README table

```markdown
### Free Apify plan limits (set by this Actor's developer)

| Limit | Free Apify plan | Paid Apify plan |
| --- | --- | --- |
| Runs of this Actor | **10 runs total** | Unlimited |
| Results per run | **Up to 1,000** | Up to schema max |

When the run cap is hit, the run finishes with a clear status message — not an Apify platform error.
```

## Unit tests (outline)

```python
def test_clamp_free():
    assert clamp_max_results(5000, is_limited=True) == (1000, True)

def test_paying_local_bypass():
    actor = SimpleNamespace(is_at_home=lambda: False, configuration=SimpleNamespace(user_is_paying=False))
    assert is_paying_user(actor) is True

@pytest.mark.asyncio
async def test_blocks_at_max(monkeypatch):
    monkeypatch.setenv("FORCE_FREE_TIER", "1")
    # mock KV runCount == FREE_MAX_RUNS → raises FreeTierLimitError
```

## Push + acceptance

**Required:** online smoke/acceptance uses a **fresh random-valid** input.  
**Forbidden:** README How-to JSON, schema `prefill`/`default`, Standby `/input-example`, or any fixed canary reused every run.

```bash
# Keep URL + secrets on new versions
# .actor/actor.json → environmentVariables:
#   WORKER_BASE_URL = "https://…run.app"
#   WORKER_AUTH = "@<secret>"

apify push --force

# 1) Generate random-valid input at call time (do NOT paste README/prefill).
#    Domain-specific: random city/ZIP, keyword, feed, filters, etc.
#    Keep maxResults/maxItems small (2–5). Prefer combos that usually return rows;
#    if empty, re-roll — do not fall back to the docs example.
# 2) Prefer --input-file so local KV INPUT cannot override.
apify call <user>/<actor> -b latest -t 300 -m 1024 --input-file /tmp/input.json --json

# Inspect
apify key-value-stores get-value <kvsId> RUN_SUMMARY
apify datasets get-items <datasetId> --format json
```

Paying owner smoke: expect `freeTierLimited: false`, `workerBaseUrlSource: "env"`, normal dataset rows.  
Free-path logic: covered by unit tests + `FORCE_FREE_TIER` locally.  
Acceptance report must include the **exact randomized input JSON** used for that run.

---

## Config-driven worker URL (`src/worker_client.py`)

Reference: `Apify Actors/linkedin-jobs-scraper/src/worker_client.py`.

```python
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse
import os, logging

logger = logging.getLogger(__name__)
DEFAULT_WORKER_BASE_URL = "https://example-worker.run.app"  # last resort only
UrlSource = Literal["input", "env", "default"]


@dataclass(frozen=True)
class WorkerEndpoint:
    base_url: str
    source: UrlSource


def _env_flag(name: str) -> bool:
    return str(os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def worker_provides_proxy() -> bool:
    """Actor skips Apify RESIDENTIAL; worker uses PROXY_URL."""
    return _env_flag("WORKER_PROVIDES_PROXY") or _env_flag("SKIP_APIFY_PROXY")


def _validate_base_url(raw: str) -> str:
    root = raw.strip().rstrip("/")
    parsed = urlparse(root)
    local = (parsed.hostname or "").lower() in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not local:
        raise AcquisitionError(f"WORKER_BASE_URL must use https:// (got {parsed.scheme})")
    return root


def resolve_worker_endpoint(override: str | None = None) -> WorkerEndpoint:
    if (override or "").strip():
        return WorkerEndpoint(_validate_base_url(override), "input")
    env_url = (os.getenv("WORKER_BASE_URL") or "").strip()
    if env_url:
        return WorkerEndpoint(_validate_base_url(env_url), "env")
    logger.warning(
        "WORKER_BASE_URL unset; using built-in default. Set Actor env for zero-code migrations."
    )
    return WorkerEndpoint(_validate_base_url(DEFAULT_WORKER_BASE_URL), "default")
```

### main.py wiring (worker + optional own proxy)

```python
endpoint = resolve_worker_endpoint(config.worker_base_url)
base_url = endpoint.base_url
Actor.log.info("Worker base URL: %s (source=%s)", base_url, endpoint.source)

use_worker_proxy = worker_provides_proxy()
if use_worker_proxy:
    proxy_url = ""
    payload = config.to_worker_payload(proxy_url="")
    payload.pop("proxyUrl", None)  # worker PROXY_URL
else:
    proxy_url = await mint_apify_residential(...)
    payload = config.to_worker_payload(proxy_url=proxy_url)

# RUN_SUMMARY / INPUT_ECHO
"workerBaseUrl": base_url,
"workerBaseUrlSource": endpoint.source,  # expect "env" in production
"proxySource": "worker-env" if use_worker_proxy else "apify-residential",
```

### input_schema Advanced field

```json
"workerBaseUrl": {
  "title": "Worker base URL (optional)",
  "type": "string",
  "description": "Override worker origin for this run. Default: Actor env WORKER_BASE_URL. Production migrations should update WORKER_BASE_URL in Actor settings (no code change).",
  "editor": "textfield",
  "sectionCaption": "Advanced"
}
```

### URL resolve tests

```python
def test_resolve_prefers_input(monkeypatch):
    monkeypatch.setenv("WORKER_BASE_URL", "https://env.example.com")
    ep = resolve_worker_endpoint("https://input.example.com")
    assert ep.source == "input"

def test_resolve_uses_env(monkeypatch):
    monkeypatch.setenv("WORKER_BASE_URL", "https://env.example.com/")
    ep = resolve_worker_endpoint(None)
    assert ep.base_url == "https://env.example.com"
    assert ep.source == "env"
```

### Migrate worker (ops)

| Step | Action |
| --- | --- |
| 1 | Deploy new worker; keep OpenAPI paths + API key contract |
| 2 | Console → Actor env: `WORKER_BASE_URL=https://new-host` |
| 3 | If key changed: update `WORKER_AUTH` secret |
| 4 | Optional: `WORKER_PROVIDES_PROXY=1` + worker `PROXY_URL` |
| 5 | Smoke run → log `source=env`; no Actor git/code change |
| 6 | Before next `apify push`, sync `actor.json` `WORKER_BASE_URL` so push does not revert Console |
