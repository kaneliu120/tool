"""Provider registry with fail-closed failover."""

from __future__ import annotations

from typing import Any

from rea_unblocker.providers.base import FetchResult, HtmlProvider
from rea_unblocker.providers.mock import MockHtmlProvider
from rea_unblocker.providers.remote_runner import (
    mac_runner_from_env,
    windows_runner_from_env,
)

# Explicitly excluded from REA default chain (document §7.3 / §13.1).
FORBIDDEN_DEFAULT = {
    "apify_xvfb_chrome",
    "camoufox_rea",
    "cloakbrowser",
}


class ProviderRegistry:
    def __init__(self, providers: list[HtmlProvider] | None = None) -> None:
        self._providers: dict[str, HtmlProvider] = {}
        self._order: list[str] = []
        for provider in providers or []:
            self.register(provider)

    def register(self, provider: HtmlProvider, *, preferred: bool = True) -> None:
        if provider.name in FORBIDDEN_DEFAULT:
            raise ValueError(f"provider {provider.name} is forbidden for REA defaults")
        self._providers[provider.name] = provider
        if preferred and provider.name not in self._order:
            self._order.append(provider.name)

    def get(self, name: str) -> HtmlProvider:
        if name not in self._providers:
            raise KeyError(f"unknown provider: {name}")
        return self._providers[name]

    def names(self) -> list[str]:
        return list(self._order)

    async def fetch(
        self,
        url: str,
        *,
        kind: str,
        provider: str | None = None,
        context: dict[str, Any] | None = None,
        failover: bool = True,
    ) -> FetchResult:
        context = context or {}
        if provider:
            chain = [provider]
        elif failover:
            chain = list(self._order)
        else:
            if not self._order:
                raise RuntimeError("no providers registered")
            chain = [self._order[0]]

        last: FetchResult | None = None
        errors: list[str] = []
        for name in chain:
            if name in FORBIDDEN_DEFAULT:
                errors.append(f"{name}: forbidden")
                continue
            impl = self.get(name)
            result = await impl.fetch(url, kind=kind, context=context)
            last = result
            if not result.blocked and result.html and not result.error:
                result.diagnostics = {
                    **(result.diagnostics or {}),
                    "attemptedProviders": chain[: chain.index(name) + 1],
                }
                return result
            errors.append(f"{name}: {result.error or 'blocked'}")

        if last is None:
            return FetchResult(
                url=url,
                final_url=None,
                html="",
                status_code=None,
                provider="none",
                engine=None,
                blocked=True,
                error="fail closed: no provider available",
                diagnostics={"errors": errors},
            )

        last.blocked = True
        last.diagnostics = {
            **(last.diagnostics or {}),
            "errors": errors,
            "failClosed": True,
        }
        if not last.error:
            last.error = "fail closed: all providers blocked or failed"
        return last


def build_default_registry(*, include_mock: bool = False) -> ProviderRegistry:
    registry = ProviderRegistry()
    mac = mac_runner_from_env()
    win = windows_runner_from_env()
    if mac:
        registry.register(mac)
    if win:
        registry.register(win)
    if include_mock or not registry.names():
        # Local/dev fallback only — never pretend this is production unblock.
        registry.register(MockHtmlProvider())
    return registry
