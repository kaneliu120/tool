#!/usr/bin/env python3
"""stop: after each completed agent turn, force one Mem0 handoff write.

Uses an awaiting marker so the handoff follow-up turn itself does not
trigger another follow-up (avoids infinite loops). loop_limit in hooks.json
must be high enough for multi-turn chats.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

STATE = Path.home() / ".cursor" / "mem0-state"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    if os.environ.get("MEM0_SILENT") in {"1", "true", "yes"}:
        print("{}")
        return

    status = str(payload.get("status") or "")
    if status and status != "completed":
        print("{}")
        return

    session_id = str(
        payload.get("session_id")
        or payload.get("conversation_id")
        or os.environ.get("MEM0_SESSION_ID")
        or "default"
    )[:32]
    project = (
        os.environ.get("MEM0_PROJECT")
        or os.environ.get("CURSOR_PROJECT_DIR")
        or ""
    )
    project_name = Path(project).name if project else "workspace"

    STATE.mkdir(parents=True, exist_ok=True)
    awaiting = STATE / f"awaiting-handoff-{session_id}"

    # Previous stop already asked for handoff; this completion is that turn.
    if awaiting.is_file():
        try:
            awaiting.unlink()
        except OSError:
            pass
        print("{}")
        return

    try:
        awaiting.write_text("1\n", encoding="utf-8")
    except OSError:
        pass

    msg = (
        "【Mem0 强制收工 · 交接写入】\n"
        f"项目 `{project_name}` session `{session_id}`。\n"
        "立刻写入 Mem0（不要问是否需要）。优先 MCP `handoff`；否则：\n\n"
        "```bash\n"
        "python3 scripts/mem0ctl.py handoff \\\n"
        f"  --project '{project_name}' \\\n"
        "  --verdict '一句话结论' \\\n"
        "  --done '做了什么（要点）' \\\n"
        "  --status '当前真实状态' \\\n"
        "  --gotchas '坑点（无则写无）' \\\n"
        "  --next '下一步' \\\n"
        "  --evidence '路径/命令/验证'\n"
        "```\n\n"
        "要求：真实、直接；未验证勿写已上线/已闭环。"
        "若本轮已写入，search 确认后简短回复即可。"
        "写完附 memory id 前缀。"
    )
    print(json.dumps({"followup_message": msg}, ensure_ascii=False))


if __name__ == "__main__":
    main()
