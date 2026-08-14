#!/usr/bin/env python3
"""beforeSubmitPrompt: allow, stamp lookup-heavy prompts for later hooks.

Cloud Agents skip this hook on the first read-only prompt. It cannot inject
Mem0 context (no additional_context on this event; sessionStart is desktop-only).
Recall is enforced by always-apply ``mem0-mandatory.mdc`` + AGENTS.md.
Blocks only when MEM0_FORCE_BLOCK=1 (debug). Otherwise always continue.
"""

from __future__ import annotations

import json
import os
import re
import sys

LOOKUP_RE = re.compile(
    r"(查|怎么|为何|为什么|报错|失败|坑|gotcha|之前|上次|记得|偏好|决策|"
    r"how|why|error|fail|remember|prefer|decision|handoff|交接)",
    re.I,
)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    prompt = str(payload.get("prompt") or "")

    if os.environ.get("MEM0_FORCE_BLOCK") == "1" and LOOKUP_RE.search(prompt):
        print(
            json.dumps(
                {
                    "continue": False,
                    "user_message": "Mem0 强制模式：请先让 Agent 执行 mem0 search 再继续。",
                },
                ensure_ascii=False,
            )
        )
        return

    try:
        marker = os.path.expanduser("~/.cursor/mem0-state/last-prompt.txt")
        os.makedirs(os.path.dirname(marker), exist_ok=True)
        with open(marker, "w", encoding="utf-8") as f:
            f.write(prompt[:4000])
        if LOOKUP_RE.search(prompt):
            with open(
                os.path.expanduser("~/.cursor/mem0-state/needs-recall"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write("1")
    except OSError:
        pass

    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
