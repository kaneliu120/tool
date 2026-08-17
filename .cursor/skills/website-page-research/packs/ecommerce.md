# Ecommerce / marketplace pack

Read after the core skill for shops, marketplaces, PDP, mall/collection shelves.

## Extra surfaces

| Extra | Open |
|---|---|
| Keyword Search | worker’s usual hottest gate |
| Category listing | often colder than keyword search — **must open** |
| Mall / collection / flash sale | different list API than search |
| PDP | live `-i.` / slug link; do not invent ids |
| Shop / seller | username or shopid URL |
| Cart/mini (observe only) | never click checkout |

Search and Category are **different surfaces**. A guest session may render category cards and still hard-block `/search`.

## Extra field groups

- Commerce ids: `itemid`+`shopid` (or SKU)
- Price scale (integer × 10^n vs display string)
- Sold count / historical_sold
- Variants / SKU
- Shop rating vs item rating

## Habits (Shopee-class, 2026-08 measured)

- PC may be **module federation** (`pcmall-*` manifest), not Next — no `__NEXT_DATA__`
- Non-browser HTTP 200 + ~160KB CSR shell with **zero** item ids is normal
- JSON-LD `ItemList` may be a fixed SEO floor (~10) that **does not page**; DOM `data-sqe=item` (or equivalent) is the visible list
- Keyword Search and PDP may redirect to `/verify/traffic` type=4 **without** a captcha iframe (`Login Required`)
- Naked `/api/v4/...` may 403 with a stable error code — record the code as 部分; do not call it a public API
- Category `?page=N` (0-based) can be real while keyword XHR uses another key (`page` vs `newest`) — measure each
- Prefer `data-sqe` (or pack-equivalent) over pagebuilder `data-pbc-*`
- type=4 ≠ standard captcha wait; do not write solve playbooks here
- If signature headers are required to replay XHR: stop, mark Rebuild not started

## Probe EXTRA_KEYS

`itemid`, `shopid`, `search_items`, `item_basic`, `data-sqe`, `pcmall`
