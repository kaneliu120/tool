"""Unified HTML provider protocol."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class FetchResult:
    url: str
    final_url: str | None
    html: str
    status_code: int | None
    provider: str
    engine: str | None
    blocked: bool
    error: str | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, *, include_html: bool = True) -> dict[str, Any]:
        payload = asdict(self)
        if not include_html:
            payload["html"] = f"<omitted {len(self.html)} chars>"
        return payload


@runtime_checkable
class HtmlProvider(Protocol):
    name: str

    async def fetch(
        self,
        url: str,
        *,
        kind: str,
        context: dict[str, Any] | None = None,
    ) -> FetchResult:
        ...
