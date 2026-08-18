"""Actor input → worker payload. No proxyUrl when worker owns egress."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ActorInput:
    mode: str
    q: str | None
    category: str | None
    developer_id: str | None
    package_ids: list[str]
    detail_urls: list[str]
    c: str
    hl: str | None
    gl: str | None
    market: str | None
    max_results: int
    enrich_details: bool
    include_data_safety: bool
    include_reviews: bool
    age: str | None
    worker_base_url: str | None
    fields: list[str] | None

    def to_worker_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "mode": self.mode,
            "c": self.c,
            "maxResults": self.max_results,
            "enrichDetails": self.enrich_details,
            "includeDataSafety": self.include_data_safety,
            "includeReviews": self.include_reviews,
        }
        if self.q:
            payload["q"] = self.q
        if self.category:
            payload["category"] = self.category
        if self.developer_id:
            payload["developerId"] = self.developer_id
        if self.package_ids:
            payload["packageIds"] = self.package_ids
        if self.detail_urls:
            payload["detailUrls"] = self.detail_urls
        if self.hl:
            payload["hl"] = self.hl
        if self.gl:
            payload["gl"] = self.gl
        if self.market:
            payload["market"] = self.market
        if self.age:
            payload["age"] = self.age
        if self.fields:
            payload["fields"] = self.fields
        payload.pop("proxyUrl", None)
        return payload


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    out: list[str] = []
    for item in value:
        s = str(item).strip()
        if s:
            out.append(s)
    return out


def parse_input(raw: dict[str, Any] | None) -> ActorInput:
    data = raw or {}
    max_results = data.get("maxResults", 10)
    try:
        max_results = int(max_results)
    except (TypeError, ValueError):
        max_results = 10
    max_results = max(1, min(max_results, 1000))
    mode = str(data.get("mode") or "search").strip().lower() or "search"
    q = (data.get("q") or data.get("searchQuery") or "").strip()
    if mode == "search" and not q:
        q = "flashlight"
    return ActorInput(
        mode=mode,
        q=q or None,
        category=(data.get("category") or "").strip() or None,
        developer_id=str(data.get("developerId") or "").strip() or None,
        package_ids=_as_list(data.get("packageIds")),
        detail_urls=_as_list(data.get("detailUrls")),
        c=(data.get("c") or "apps").strip() or "apps",
        hl=(data.get("hl") or "").strip() or None,
        gl=(data.get("gl") or "").strip().upper() or None,
        market=(data.get("market") or "us").strip().lower() or "us",
        max_results=max_results,
        enrich_details=bool(data.get("enrichDetails")),
        include_data_safety=bool(data.get("includeDataSafety")),
        include_reviews=bool(data.get("includeReviews")),
        age=(data.get("age") or "").strip().upper() or None,
        worker_base_url=(data.get("workerBaseUrl") or "").strip() or None,
        fields=_as_list(data.get("fields")) or None,
    )
