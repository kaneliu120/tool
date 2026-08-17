"""Free Apify-plan limits. Console has no N-runs toggle — enforce here."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from src.errors import FreeTierLimitError

logger = logging.getLogger(__name__)

FREE_MAX_RUNS = 10
FREE_MAX_RESULTS = 200
STATE_STORE_NAME = "google-play-scraper-free-tier"

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
