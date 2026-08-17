# Coverage matrix (README + smoke)

Tick in the **worker README** before coding parse. Status: **已验证** | **部分** | **未验证**.  
Random cloud smoke samples **opened** (已验证 / 部分) cells only — never README prefills.

Ontology = `website-page-research` surfaces: Search, Category, Detail, Overlay (pricing/seats/map), Market switch. Drop columns the site does not have; do not invent sale/rent on a ticketing site.

## Table

| 市场/host | Search | Category | Detail | Overlay | 闸门 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| us | 未验证 | 未验证 | 未验证 | 未验证 | | 未验证 |
| {next} | 未验证 | 未验证 | 未验证 | 未验证 | | 未验证 |

Fill example (Ticketmaster-shaped, illustrative):

| 市场/host | Search | Category | Detail | Overlay | 闸门 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| us | 已验证 BFF `q` | 部分 | orch EDP | `seatManifest` sibling of `edpData` | EPS | 打开 |
| au | BFF 短 q 400 | 未验证 | 未验证 | | | 未验证 |

## Machine-readable (for `random_smoke_input.py`)

Save as `coverage-matrix.json` in the worker or Actor repo (no secrets):

```json
{
  "primaryMarket": "us",
  "queryPool": ["replace-me-with-fresh-queries"],
  "queryKey": "q",
  "maxResults": 3,
  "cells": [
    {
      "market": "us",
      "mode": "search",
      "status": "opened",
      "template": { "q": "{{query}}", "market": "us", "maxResults": 3 }
    }
  ]
}
```

`status` must be `opened` or `partial` to be sampled. `未验证` / `closed` are skipped.

Rules:

- Source Actor coverage is a **floor**, not a ceiling.
- Schema enums must expose every matrix market/mode, including 未验证 (users can request; worker may return partial + warning).
- Spot-check: ≥1 non-primary market + ≥1 non-search mode when those cells are opened.
