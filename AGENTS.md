# AGENTS.md

## Cursor Cloud specific instructions

This VM cannot use macOS Keychain or `ssh -N mem0` to `localhost:8888`. Kane's Mem0 REST/Dashboard stay private; **public ingress is MCP only**.

### Call the memory system

1. Public health (no key): `python scripts/mem0ctl.py health`
2. Authenticated search/add needs **`MEM0_API_KEY`** (user REST/MCP key, not the admin `/configure` key).
3. Default scope: `user_id=kane`. Do **not** use stdlib `urllib` against the public host (Cloudflare 1010). Use `mem0ctl` / `httpx` / `curl`.
4. Do **not** use the official `mem0ai` Python client against this self-hosted stack.
5. Never commit API keys, Atlas URIs, or NVIDIA/Voyage tokens.

```bash
# no auth
python scripts/mem0ctl.py health

# requires MEM0_API_KEY in the Cloud Agent secret store
python scripts/mem0ctl.py search "hiking Taipei"
python scripts/mem0ctl.py add --raw "handoff note"
python scripts/mem0ctl.py list
```

Python:

```python
from mem0_client import Mem0Client
with Mem0Client() as mem0:
    mem0.health()
    mem0.search("Kane 怎么部署", top_k=5)
```

### Secrets and MCP this agent cannot set itself

- **Runtime Secret** `MEM0_API_KEY` at [cursor.com/dashboard/cloud-agents](https://cursor.com/dashboard/cloud-agents) — injected as a VM env var so `mem0ctl` works. Restart the agent after adding it.
- **HTTP MCP** named `mem0-selfhost` at [cursor.com/agents](https://cursor.com/agents) (Cloud Agents do not load `.cursor/mcp.json`):
  - URL: `https://mem0-mcp.opendata.best/mcp`
  - Headers: `Authorization: Bearer <MEM0_API_KEY>` and `X-API-Key: <MEM0_API_KEY>`
  - Transport must be HTTP (not SSE).

Optional env: `MEM0_MCP_URL` (default `https://mem0-mcp.opendata.best`), `MEM0_USER_ID` (default `kane`), `MEM0_REST_URL` (only if an SSH tunnel to REST `:8888` exists).

Local Cursor IDE can use `.cursor/mcp.json` with `${env:MEM0_API_KEY}`.

## Skills / hooks / rules copied from Kane's Mac

Cloud Agents **do not** load `~/.cursor/` from the laptop. This repo checkout is the source.

### Skills (`.cursor/skills/`)

| Skill | Cloud |
|---|---|
| `mem0-selfhost` | Yes — use `scripts/mem0ctl.py` + HTTP MCP |
| `apify-actor-cloud-run-development` (+ redirects) | Yes as methodology; Kane's `~/Projects/google run worker` paths are **not** on this VM |
| `apify-publish-tasks` | Yes; Console publish needs a browser (VM desktop, not Mac Chrome) |
| `bright-data-riskbypass` / `camoufox-cloud-run` | Yes as docs |
| `website-page-research` | Partial — no AppleScript Chrome |
| `reverse-skill` | Router only — full pack not in this clone |
| `use-my-browser` | **Stub only** — do not `osascript` |

Skipped: `harvest-transcripts` (Mac agent-transcripts). Built-in `~/.cursor/skills-cursor/` is provided by Cursor, not copied.

### Hooks (`.cursor/hooks.json`)

Command hooks only, after the VM is writable:

- `beforeSubmitPrompt` → `.cursor/hooks/mem0_before_prompt.py`
- `stop` → `.cursor/hooks/mem0_stop_handoff.py` (follow-up uses `python3 scripts/mem0ctl.py`)
- `preCompact` → `.cursor/hooks/mem0_precompact.py`

**Not on Cloud:** `sessionStart`, `sessionEnd`, prompt-based hooks, Tab hooks, MCP execution hooks. Mem0 recall at start comes from always-apply rule `mem0-mandatory.mdc` + this file.

### Rules (`.cursor/rules/*.mdc`, alwaysApply)

- `mem0-mandatory.mdc`
- `apify-actor-cloud-run-development.mdc`
- `apify-cloud-smoke-random.mdc`
- `apify-publish-tasks.mdc`

User Rules in Cursor Settings still apply to Cloud sessions (account-level). Team dashboard rules apply if configured.

### What you still configure in the Dashboard (not git)

1. Runtime Secret `MEM0_API_KEY`
2. HTTP MCP `mem0-selfhost` on [cursor.com/agents](https://cursor.com/agents)
3. Re-open a **new** Cloud Agent on this branch after push — existing runs will not pick up new git files until they clone this revision.
