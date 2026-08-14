# Food-delivery pack

Read after the core skill for city-based restaurant / store / menu products.

## Extra surfaces

| Extra | Open |
|---|---|
| City / region SEO list | `/city/...` not only homepage |
| Cuisine / category subpath | if present |
| Store / restaurant detail | live list link (URL may append region id) |
| Menu | on store page or a tab |
| Global search | often a different gate than city SEO |
| Sitemap / CDN sitemap | URL discovery only (may 200 when www is 403) |

## Extra field groups

- Store identity + region/store id
- Menu tree: section → item → modifier
- Hours / delivery area (shapes, not a dump of addresses)
- Ratings

## Habits (DoorDash-class)

- www may be full 403 for all non-browser UAs while `cdn.../sitemaps/*` is 200
- App Router + RSC, no `__NEXT_DATA__`
- `Menu.hasMenuSection` may be a **double array** `[[{ name, hasMenuItem: [...] }]]` — a single-level parse yields 0 items
- Store URLs may auto-append region ids — record the template
- Never click order / checkout / add-to-cart

## Probe EXTRA_KEYS

`hasMenuSection`, `hasMenuItem`, `Menu`, `store`, `regionId`
