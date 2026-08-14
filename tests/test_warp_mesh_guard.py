from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _eval(text: str) -> list[str]:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "warp_mesh_guard", ROOT / ".cursor" / "warp_mesh_guard.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.evaluate(text)


def test_refuse_default_exclude_warp_mode() -> None:
    blob = """
(default)\tMode: Warp
(api defaults)\tExclude mode, with hosts/ips:
  100.64.0.0/10
  10.0.0.0/8
"""
    errors = _eval(blob)
    assert errors
    assert any("tunnel_only" in e for e in errors)
    assert any("100.96.0.0/12" in e for e in errors)
    assert any("100.64.0.0/10" in e for e in errors)


def test_ok_tunnel_only_include_mesh() -> None:
    blob = """
(user)\tMode: TunnelOnly
(user)\tInclude mode, with hosts/ips:
  100.96.0.0/12
  100.64.0.0/12
  172.64.128.0/20
"""
    assert _eval(blob) == []
