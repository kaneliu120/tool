#!/usr/bin/env python3
"""Validate Cloud Agent skills, hooks, and rules in this checkout."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURSOR = ROOT / ".cursor"
CLOUD_HOOKS = {"beforeSubmitPrompt", "stop", "preCompact"}
UNSUPPORTED_CLOUD_HOOKS = {
    "sessionStart",
    "sessionEnd",
    "beforeMCPExecution",
    "afterMCPExecution",
    "beforeTabFileRead",
    "afterTabFileEdit",
    "workspaceOpen",
}


def _fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def check_hooks(errors: list[str], notes: list[str]) -> None:
    path = CURSOR / "hooks.json"
    if not path.is_file():
        _fail(errors, "missing .cursor/hooks.json")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1:
        _fail(errors, f"hooks.json version must be 1, got {data.get('version')!r}")
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        _fail(errors, "hooks.json missing hooks object")
        return
    for name in UNSUPPORTED_CLOUD_HOOKS.intersection(hooks):
        notes.append(f"hook {name} is configured but Cloud Agents skip it")
    for event, entries in hooks.items():
        if not isinstance(entries, list):
            _fail(errors, f"hooks.{event} must be a list")
            continue
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict) or "command" not in entry:
                _fail(errors, f"hooks.{event}[{i}] missing command")
                continue
            if entry.get("type") == "prompt":
                _fail(errors, f"hooks.{event}[{i}] is prompt-based (not supported on Cloud)")
            command = str(entry["command"]).split()
            script = None
            if len(command) >= 2 and command[0] in {"python3", "python"}:
                script = command[-1]
            elif command:
                script = command[0]
            if script and not (ROOT / script).is_file():
                _fail(errors, f"hooks.{event}[{i}] script missing: {script}")
    for required in CLOUD_HOOKS:
        if required not in hooks:
            notes.append(f"optional Cloud hook not configured: {required}")


def check_skills(errors: list[str], notes: list[str]) -> None:
    root = CURSOR / "skills"
    if not root.is_dir():
        _fail(errors, "missing .cursor/skills")
        return
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        skill = folder / "SKILL.md"
        if not skill.is_file():
            _fail(errors, f"missing {skill.relative_to(ROOT)}")
            continue
        text = skill.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", text, re.S)
        if not match:
            _fail(errors, f"{skill.relative_to(ROOT)} missing YAML frontmatter")
            continue
        fm = match.group(1)
        name_m = re.search(r"^name:\s*(\S+)\s*$", fm, re.M)
        desc_m = re.search(r"^description:\s*(.+)$", fm, re.M)
        name = name_m.group(1) if name_m else ""
        desc = (desc_m.group(1) if desc_m else "").strip()
        if name != folder.name:
            _fail(errors, f"skill name {name!r} != folder {folder.name!r}")
        if not desc:
            _fail(errors, f"{folder.name} SKILL.md missing description")
        if "DEPRECATED redirect" in text:
            notes.append(f"redirect skill present: {folder.name}")


def check_rules(errors: list[str], notes: list[str]) -> None:
    root = CURSOR / "rules"
    if not root.is_dir():
        _fail(errors, "missing .cursor/rules")
        return
    required = {
        "mem0-mandatory.mdc",
        "project-skills.mdc",
        "apify-actor-cloud-run-development.mdc",
        "apify-cloud-smoke-random.mdc",
        "apify-publish-tasks.mdc",
    }
    found = {p.name for p in root.glob("*.mdc")}
    for name in sorted(required - found):
        _fail(errors, f"missing rule {name}")
    for path in sorted(root.glob("*.mdc")):
        text = path.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", text, re.S)
        if not match:
            _fail(errors, f"{path.name} missing frontmatter")
            continue
        fm = match.group(1)
        if "alwaysApply: true" not in fm:
            notes.append(f"{path.name} is not alwaysApply")
        desc_m = re.search(r"^description:\s*(.*)$", fm, re.M)
        desc = (desc_m.group(1) if desc_m else "").strip()
        if not desc:
            _fail(errors, f"{path.name} has empty description")


def check_mcp_and_env(errors: list[str], notes: list[str]) -> None:
    for rel in (".cursor/mcp.json", ".cursor/environment.json", "AGENTS.md"):
        if not (ROOT / rel).is_file():
            _fail(errors, f"missing {rel}")
    mcp = json.loads((CURSOR / "mcp.json").read_text(encoding="utf-8"))
    server = (mcp.get("mcpServers") or {}).get("mem0-selfhost") or {}
    if not str(server.get("url", "")).endswith("/mcp"):
        _fail(errors, "mcp.json mem0-selfhost url must end with /mcp")
    env = json.loads((CURSOR / "environment.json").read_text(encoding="utf-8"))
    if env.get("install") != "./.cursor/install.sh":
        _fail(errors, f"environment.json install must be ./.cursor/install.sh, got {env.get('install')!r}")
    if env.get("start") != "./.cursor/start.sh":
        _fail(errors, f"environment.json start must be ./.cursor/start.sh, got {env.get('start')!r}")
    if not (CURSOR / "start.sh").is_file():
        _fail(errors, "missing .cursor/start.sh")
    elif not os.access(CURSOR / "start.sh", os.X_OK):
        _fail(errors, ".cursor/start.sh is not executable")
    if not (CURSOR / "install.sh").is_file():
        _fail(errors, "missing .cursor/install.sh")
    elif not os.access(CURSOR / "install.sh", os.X_OK):
        _fail(errors, ".cursor/install.sh is not executable")
    ports = env.get("ports") or []
    if not any(isinstance(p, dict) and p.get("port") == 8080 for p in ports):
        _fail(errors, "environment.json must declare gateway port 8080")


def check_hook_runtime(errors: list[str], notes: list[str]) -> None:
    import tempfile

    try:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "HOME": tmp, "MEM0_SILENT": "", "MEM0_FORCE_BLOCK": ""}
            proc = subprocess.run(
                [sys.executable, str(ROOT / ".cursor/hooks/mem0_before_prompt.py")],
                input=json.dumps({"prompt": "hello", "hook_event_name": "beforeSubmitPrompt"}),
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )
            if proc.returncode != 0:
                _fail(errors, f"beforeSubmitPrompt exited {proc.returncode}: {proc.stderr}")
            else:
                out = json.loads(proc.stdout)
                if out.get("continue") is not True:
                    _fail(errors, f"beforeSubmitPrompt expected continue=true, got {out}")
            proc = subprocess.run(
                [sys.executable, str(ROOT / ".cursor/hooks/mem0_precompact.py")],
                input=json.dumps({"trigger": "auto"}),
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )
            if proc.returncode != 0:
                _fail(errors, f"preCompact exited {proc.returncode}: {proc.stderr}")
            else:
                out = json.loads(proc.stdout)
                if "user_message" not in out:
                    _fail(errors, f"preCompact missing user_message: {out}")
    except Exception as exc:  # noqa: BLE001 — report as check failure
        _fail(errors, f"hook runtime: {exc}")


def main() -> int:
    errors: list[str] = []
    notes: list[str] = []
    check_hooks(errors, notes)
    check_skills(errors, notes)
    check_rules(errors, notes)
    check_mcp_and_env(errors, notes)
    check_hook_runtime(errors, notes)
    report = {
        "ok": not errors,
        "errors": errors,
        "notes": notes,
        "mem0_api_key": bool(os.environ.get("MEM0_API_KEY")),
        "venv_python": (ROOT / ".venv" / "bin" / "python").is_file(),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
