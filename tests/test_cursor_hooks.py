from __future__ import annotations

import json
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1] / ".cursor" / "hooks"


def _run(script: str, payload: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, extra_env: dict[str, str] | None = None):
    import runpy
    import sys
    from io import StringIO

    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("MEM0_FORCE_BLOCK", raising=False)
    monkeypatch.delenv("MEM0_SILENT", raising=False)
    if extra_env:
        for key, value in extra_env.items():
            monkeypatch.setenv(key, value)
    monkeypatch.setattr(sys, "stdin", StringIO(json.dumps(payload)))
    captured = StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    runpy.run_path(str(HOOKS / script), run_name="__main__")
    return json.loads(captured.getvalue()), home


def test_before_prompt_allows_and_stamps_lookup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    out, home = _run(
        "mem0_before_prompt.py",
        {"prompt": "之前 skill hook 怎么配置的"},
        monkeypatch,
        tmp_path,
    )
    assert out == {"continue": True}
    assert (home / ".cursor" / "mem0-state" / "needs-recall").read_text() == "1"
    assert "skill hook" in (home / ".cursor" / "mem0-state" / "last-prompt.txt").read_text()


def test_before_prompt_force_block(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    out, _home = _run(
        "mem0_before_prompt.py",
        {"prompt": "为什么报错"},
        monkeypatch,
        tmp_path,
        extra_env={"MEM0_FORCE_BLOCK": "1"},
    )
    assert out["continue"] is False
    assert "Mem0" in out["user_message"]


def test_stop_followup_then_suppress(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    out, home = _run(
        "mem0_stop_handoff.py",
        {"status": "completed", "conversation_id": "abc123", "loop_count": 0},
        monkeypatch,
        tmp_path,
    )
    assert "followup_message" in out
    assert "mem0ctl.py handoff" in out["followup_message"]
    marker = home / ".cursor" / "mem0-state" / "awaiting-handoff-abc123"
    assert marker.is_file()

    out2, _home = _run(
        "mem0_stop_handoff.py",
        {"status": "completed", "conversation_id": "abc123", "loop_count": 1},
        monkeypatch,
        tmp_path,
    )
    assert out2 == {}
    assert not marker.is_file()


def test_stop_aborted_is_noop(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    out, home = _run(
        "mem0_stop_handoff.py",
        {"status": "aborted", "conversation_id": "zzz"},
        monkeypatch,
        tmp_path,
    )
    assert out == {}
    assert not (home / ".cursor" / "mem0-state" / "awaiting-handoff-zzz").exists()


def test_stop_silent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    out, _home = _run(
        "mem0_stop_handoff.py",
        {"status": "completed"},
        monkeypatch,
        tmp_path,
        extra_env={"MEM0_SILENT": "1"},
    )
    assert out == {}


def test_precompact_user_message(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    out, _home = _run(
        "mem0_precompact.py",
        {"trigger": "auto", "context_usage_percent": 90},
        monkeypatch,
        tmp_path,
    )
    assert "Mem0" in out["user_message"]
