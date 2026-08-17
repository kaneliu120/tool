---
name: mem0-selfhost
description: Call Kane's self-hosted Mem0 memory system (public MCP / mem0ctl). Use when searching, storing, or listing long-term memories, user preferences, handoffs, or prior decisions.
---

# Mem0 self-host (Cloud Agent)

Public host: `https://mem0-mcp.opendata.best` (`GET /healthz` is unauthenticated). REST `localhost:8888` is **not** reachable here without an SSH tunnel.

Prefer MCP `mem0-selfhost` when it is registered. Otherwise `python3 scripts/mem0ctl.py` (re-execs `.venv` if system Python lacks `httpx`).

## Protocol

- Auth: `Authorization: Bearer $MEM0_API_KEY` **or** `X-API-Key`.
- Default `user_id`: `kane`.
- Search scores are cosine: `0.7+` strong, `0.4–0.6` topical, `<0.35` noise.
- `add` defaults to `infer=true` (LLM extracts facts). Use `--raw` / `infer=false` for identifiers, timestamps, and handoff docs.
- Do not use `urllib`. Do not use the official `mem0ai` client. Do not commit keys.

## Commands

```bash
python3 scripts/mem0ctl.py health
python3 scripts/mem0ctl.py search "QUERY" --top-k 8
python3 scripts/mem0ctl.py search "QUERY" --meta '{"kind":"handoff"}'
python3 scripts/mem0ctl.py add "TEXT"
python3 scripts/mem0ctl.py add --raw "verbatim"
python3 scripts/mem0ctl.py get MEMORY_ID
python3 scripts/mem0ctl.py list --top-k 50
python3 scripts/mem0ctl.py handoff \
  --project 'tool' \
  --verdict '一句话结论' \
  --done '做了什么' \
  --status '当前真实状态' \
  --gotchas '无' \
  --next '下一步' \
  --evidence '路径/命令'
python3 scripts/mem0ctl.py decision "稳定决策" --project tool
python3 scripts/mem0ctl.py gotcha "可复用坑点" --project tool
```

If `MEM0_API_KEY` is missing, stop and tell the user to add a Cloud Agent **Runtime Secret** `MEM0_API_KEY` and/or register HTTP MCP `mem0-selfhost` at cursor.com/agents. Do not invent memories.
