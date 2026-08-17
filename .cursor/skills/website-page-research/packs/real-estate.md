# Real-estate pack

Read after the core skill for property marketplaces. Sale and rent are **separate surfaces** when the site splits them — still fill the generic ontology first.

## Extra surfaces

| Extra | Open |
|---|---|
| Sale SRP | high-signal city the site actually uses |
| Sale LDP | live SRP link |
| Rent SRP | even if sale already probed |
| Rent LDP | live rent link |
| Project / developer / building | if present |
| Agent / broker | if present |
| Map search | if the product is map-first |
| Price history / schools / amenities tabs | overlays |

## Extra field groups

- Listing type: sale vs rent vs auction vs commercial
- Area, beds, baths, price, currency
- Geo: lat/lng path (do not keep exact addresses in the report)
- Agent / agency ids
- Status: listed / under offer / sold

## Habits

- Record whether sale and rent share the **same pager and API**
- JSON-LD may be complete on LDP and thin on SRP
- Map pages often use a different channel than card SRP
- Never click lead / contact / email / call / request-viewing
- Kasada / DataDome / AWS WAF / Cloudflare appear at different strengths on SRP vs LDP — split the gate table

## Probe EXTRA_KEYS

`listing`, `property`, `rent`, `buy`, `__NEXT_DATA__`, `map`
