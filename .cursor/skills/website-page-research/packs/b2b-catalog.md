# B2B catalog pack

Read after the core skill for product/company search, RFQ, industrial catalogs (iPROS / MonotaRO / Xometry-class).

## Extra surfaces

| Extra | Open |
|---|---|
| Product search / category | |
| Product detail | live link; JSON-LD `Product` often strong |
| Company / manufacturer | |
| Group / family SKU | URL shapes like `/g/{id}/` vs `/p/{a}/{b}/` |
| Case study / capability marketing | may be a **different app** (Gatsby `page-data.json` vs Next RSC) |
| Locale / language pair | ja/en etc. |

## Extra field groups

- Catalog ids (group vs SKU)
- Spec table keys (names, not full spec dumps)
- Company identity
- RFQ / contact chrome — **presence only, never submit**

## Habits

- Marketing www and the commerce app can be dual-channel (Next RSC + leftover `page-data.json`)
- Akamai: non-browser UA may HTTP/2 INTERNAL_ERROR or 0-byte timeout while Chrome reads
- URL templates themselves are identity (`/g/{8}/`, `/p/{4}/{4}/`) — record the shape
- Wholesale / member prices may be empty for guests while retail remains (Faire-class) — tick Economics as locked, not missing

## Probe EXTRA_KEYS

`Product`, `page-data.json`, `sku`, `wholesale`, `rfq`
