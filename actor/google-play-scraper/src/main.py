from __future__ import annotations

import asyncio
import logging
import os

from apify import Actor

from src.errors import AcquisitionError, FreeTierLimitError, NoRowsCollectedError
from src.free_tier import (
    FREE_MAX_RESULTS,
    FREE_MAX_RUNS,
    RESULTS_NOTE,
    enforce_free_tier,
)
from src.input_model import parse_input
from src.rows import omit_nulls
from src.worker_client import (
    call_worker,
    resolve_worker_endpoint,
    worker_provides_proxy,
)

logger = logging.getLogger(__name__)


def _is_standby() -> bool:
    origin = str(os.getenv("APIFY_META_ORIGIN") or "").strip().upper()
    return origin == "STANDBY"


async def _run() -> None:
    if _is_standby():
        from src.standby import serve

        await serve()
        return

    raw = await Actor.get_input() or {}
    config = parse_input(raw)
    await Actor.set_value("INPUT_ECHO", raw)

    free_plan = await enforce_free_tier(Actor, config.max_results)
    config.max_results = free_plan.effective_max_results
    if free_plan.is_limited:
        await Actor.set_status_message(
            f"Free Apify plan: run {free_plan.prior_runs + 1}/{free_plan.max_runs}, "
            f"up to {free_plan.effective_max_results} results this run."
        )
    if free_plan.results_clamped:
        await Actor.set_status_message(RESULTS_NOTE)

    endpoint = resolve_worker_endpoint(config.worker_base_url)
    Actor.log.info("Worker base URL: %s (source=%s)", endpoint.base_url, endpoint.source)
    use_worker_proxy = worker_provides_proxy()
    payload = config.to_worker_payload()
    payload.pop("proxyUrl", None)

    path = "/v1/listings" if (config.mode in {"detail", "datasafety"} or config.package_ids or config.detail_urls) else "/v1/search"
    envelope = call_worker(endpoint, payload, path=path)
    items = envelope.get("items") or []
    pushed = 0
    for row in items:
        if pushed >= free_plan.effective_max_results:
            break
        if isinstance(row, dict):
            row = omit_nulls(row)
        await Actor.push_data(row)
        pushed += 1

    summary = {
        "status": "ok",
        "itemCount": pushed,
        "workerStatus": envelope.get("status"),
        "worker": envelope.get("worker"),
        "provider": envelope.get("provider"),
        "warnings": envelope.get("warnings") or [],
        "workerBaseUrl": endpoint.base_url,
        "workerBaseUrlSource": endpoint.source,
        "proxySource": "worker-env" if use_worker_proxy else "none",
        "freeTierLimited": free_plan.is_limited,
        "freeTierPriorRuns": free_plan.prior_runs,
        "freeTierMaxRuns": free_plan.max_runs,
        "diagnostics": envelope.get("diagnostics") or {},
    }
    await Actor.set_value("RUN_SUMMARY", summary)
    await Actor.set_status_message(f"Pushed {pushed} Play apps")


async def main() -> None:
    async with Actor:
        try:
            await _run()
        except FreeTierLimitError as exc:
            message = str(exc).replace("\n", " ").strip()
            await Actor.set_value(
                "RUN_SUMMARY",
                {
                    "status": "FREE_TIER_LIMIT",
                    "message": message,
                    "freeTierMaxRuns": FREE_MAX_RUNS,
                    "freeTierMaxResults": FREE_MAX_RESULTS,
                },
            )
            await Actor.set_status_message(message)
            return
        except (AcquisitionError, NoRowsCollectedError) as exc:
            message = str(exc)
            await Actor.set_value("ERROR_SUMMARY", {"error": message})
            await Actor.set_value("RUN_SUMMARY", {"status": "failed", "message": message})
            await Actor.fail(status_message=message)


if __name__ == "__main__":
    asyncio.run(main())
