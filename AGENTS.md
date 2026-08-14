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
