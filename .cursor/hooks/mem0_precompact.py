#!/usr/bin/env python3
"""preCompact: remind user/agent to dump handoff before context loss."""

from __future__ import annotations

import json
import sys


def main() -> None:
    try:
        json.load(sys.stdin)
    except Exception:
        pass
    print(
        json.dumps(
            {
                "user_message": (
                    "上下文即将压缩：请确认本轮交接已写入 Mem0 "
                    "(`mem0ctl handoff`)。压缩后以 Mem0 检索为准。"
                )
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
