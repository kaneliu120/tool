# Ticketing pack

Read after the core skill when the site sells events / venues / attractions / seats.

## Extra surfaces (on top of ontology)

| Extra | Open |
|---|---|
| Browse / discovery | market home or `/discover` |
| Event detail (EDP) | live search/category link only |
| Venue | from event or venue index |
| Attraction / artist | from event |
| Classification / genre browse | category endpoint or UI |
| Quickpicks / offer list | on EDP if present — observe XHR, do not checkout |
| Seatmap | overlay or sibling hydration key |
| Queue / pause / EPS | first-class gate surface |

## Extra field groups

- Offer / price: list vs all-in fees, currency, offerId
- Inventory: section / row / seat / partition / place counts (shapes, not a dump of every seat)
- Page mode / on-sale / queue (`pageMode`, smartQueue)
- Classification: segment/genre may live on `majorCategory.id`, not `classifications`

## Habits (Ticketmaster-class, 2026-08 measured)

- Same-origin BFF may 404 without custom header **names** from the marketplace bundle; 400 with headers often means **wrong query field** (`q` not `keyword`) — do not HTML-fallback a param 400
- `seatManifest` may be a **sibling** of `edpData` under `pageProps`, not nested inside it
- Ready = `__NEXT_DATA__` + `edpData` (and seat key if that is in-scope). Pause HTML still contains the brand; ~160KB will not self-heal; ~700KB+ is often hydration
- EPS `401 {"response":"identify"}` / pause title: record as gate, not as a parser miss
- List vs EDP gates differ. Geo/query rules differ by host (lat/long may work only on some markets; short `q` may 400)
- Pagination caps may require date-window sharding for full crawls — record the cap, do not invent a bypass
- Pin paths that skip Patchright/Unlocker are debug/smoke, not “Unlocker can be turned off”

## Probe EXTRA_KEYS

`edpData`, `seatManifest`, `quickpicks`, `pageMode`, `smartQueue`, `offerId`
