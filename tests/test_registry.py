import pytest

from rea_unblocker.providers.registry import FORBIDDEN_DEFAULT, ProviderRegistry


class _Bad:
    name = "apify_xvfb_chrome"

    async def fetch(self, url, *, kind, context=None):  # noqa: ANN001
        raise AssertionError("should not run")


def test_forbidden_provider_cannot_register():
    registry = ProviderRegistry()
    with pytest.raises(ValueError):
        registry.register(_Bad())
    assert "apify_xvfb_chrome" in FORBIDDEN_DEFAULT
