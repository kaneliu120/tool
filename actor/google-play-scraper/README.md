## Google Play Store scraper

Scrape the **[Google Play Store](https://play.google.com/store/apps)** without a Google account, unofficial SDK, or invented package IDs.

Give the Actor a **keyword**, **category CODE**, **country (`gl`)**, or a live **package name** → get structured **Android app** rows: title, developer, rating, installs, price, IAP flags, screenshots, and optional **data-safety** summaries. Download **JSON, CSV, or Excel**, or pull the dataset through the **Apify API / Python / JavaScript**. Schedule runs, monitor them in Console, or pipe results into Make, n8n, Zapier, or MCP.

This Actor is a **Google Play API alternative** for public listing pages: search, home, category (including FAMILY age chips), developer pages, app details (JSON-LD), and data-safety overviews. **183 storefronts** (`hl` + `gl` on `play.google.com`). Review *bodies* and login-walled data are **not** scraped.

Free Apify-plan users (Actor developer policy): up to **10 runs** and **200 results per run**. Paid Apify plans are unlimited on those caps.

***

## What is Google Play Scraper?

**Google Play Scraper** is a **Google Play Store scraper** that extracts public **Android app** data for **ASO**, competitor tracking, and market research.

| You want | This Actor returns |
| --- | --- |
| Keyword search (`c=apps`) | First-pack app cards with `packageId`, name, developer, rating |
| Category / GAME / WATCH_FACE | Live apps on `/store/apps/category/{CODE}` |
| Home shelf | Featured apps for a country |
| App details | JSON-LD: rating, price, `isPaid`, screenshots, description, IAP chip |
| Developer page | Apps under a numeric `/store/apps/dev?id=` |
| Data safety | Heading-level summary (shared / collected / practices) |

Primary key: **package ID** (the `id=` on `play.google.com/store/apps/details?id=`). The Actor never invents ids.

Pair it with [App Store Scraper](https://apify.com/lentic_clockss/apple-app-store-scraper) when you need **dual-store ASO** (Google Play + Apple App Store).

***

## What data can you extract from Google Play Store?

| Field | Description |
| --- | --- |
| `packageId` / `listingId` | Android package name |
| `name` | App title |
| `developer` / `developerId` | Publisher name and numeric Play developer id |
| `ratingValue` / `ratingCount` | Stars and rating count (detail / enrich) |
| `installs` | Installs chip (e.g. `10B+`) |
| `price` / `priceCurrency` / `priceDisplay` / `isPaid` | JSON-LD `offers.price` (Free or paid, e.g. `USD 4.99`) |
| `inAppPurchases` | “In-app purchases” chip |
| `screenshots` | JSON-LD screenshot URLs when present |
| `contentRating` | e.g. Everyone |
| `applicationCategory` | Play category CODE |
| `containsAds` | Ads chip |
| `description` | Store description (detail) |
| `listingUrl` | Canonical details URL with `hl` / `gl` |
| `country` | Play `gl` |
| `dataSafety` | Optional datasafety summary |

***

## What can this Google Play scraper do?

| Capability | What it means |
| --- | --- |
| 183 countries | Opened `gl` presets (home + search + GAME). Override with `hl` / `gl`. |
| 50 US category CODEs | Including `APPLICATION` and `WATCH_FACE`. FAMILY `AGE_RANGE1/2/3` chips. |
| Search + category + home | First-pack HTML (`AF_initDataCallback` + live `details?id=` links) |
| Detail enrich | `enrichDetails=true` fetches JSON-LD (price, rating, screenshots) |
| Data safety | `/store/apps/datasafety` headings (partial field tree) |
| Empty shelves | DATING / MEDICAL / some FAMILY_* return `status=empty` (0 rows), not a fake catalog |
| No proxies to configure | Worker-owned egress (`WORKER_PROVIDES_PROXY`) |
| Platform extras | Default **1024 MB**, Standby + MCP/API, schedules, webhooks, CSV / Excel / JSON export |

***

## What can you do with Google Play data?

### ASO keyword research

**In plain English:** enter a search term such as `sudoku daily` and a storefront (`us`, `jp`, `kr`) → get the first pack of ranking apps with ratings.

**You give:** `mode=search`, `q`, `market` (or `hl`/`gl`)

**You get:** package ID, name, developer, rating, Play URL — ready for a keyword-rank spreadsheet.

### Category and country competitor tracking

**In plain English:** pull GAME, TOOLS, or FINANCE for Cyprus, Mexico, or Korea → see who is featured this week.

**You give:** `mode=category`, `category=GAME`, `market=cy`

### App details, prices, and IAP

**In plain English:** turn list rows into full details (or pass live `packageIds` / detail URLs). Paid apps expose JSON-LD `offers.price`; free apps show `priceDisplay=Free`.

Turn on `enrichDetails` after a search, or use `mode=detail` with ids from a previous run.

### Developer portfolios

**In plain English:** copy the numeric id from a details page (`/store/apps/dev?id=…`) → list that publisher’s apps.

### Data-safety screening

**In plain English:** fetch the public data-safety page for compliance or vendor review (`includeDataSafety` or `mode=datasafety`).

### Feed Python, n8n, Make, or an AI agent

Run the Actor from the [Apify API](https://docs.apify.com/api/v2), Python client, JavaScript client, or MCP. Results land in a dataset you can export or pipe into RAG / BI.

***

## More Actors like this

Use a **specialized Actor** when one exists for your site. Pair this Google Play scraper with the Apple App Store Actor for dual-store ASO.

**App Stores & ASO**

- [Google Play Scraper](https://apify.com/lentic_clockss/google-play-scraper)
- [App Store Scraper | Charts, Apps, Reviews](https://apify.com/lentic_clockss/apple-app-store-scraper)

**General tools**

- [Stealth Web Scraper](https://apify.com/lentic_clockss/stealth-web-scraper)
- [Email Risk Validator](https://apify.com/lentic_clockss/email-risk-validator)
- [Phone Number Intelligence](https://apify.com/lentic_clockss/phone-number-intelligence)

**Prefer a dedicated site scraper?**

**Jobs & Freelance**

- [LinkedIn Jobs Scraper](https://apify.com/lentic_clockss/linkedin-jobs-scraper)
- [Indeed Jobs Scraper](https://apify.com/lentic_clockss/indeed-jobs-scraper)
- [Upwork Jobs Scraper](https://apify.com/lentic_clockss/upwork-jobs-scraper)
- [Glassdoor Scraper](https://apify.com/lentic_clockss/glassdoor-scraper)
- [Fiverr Gigs Scraper](https://apify.com/lentic_clockss/fiverr-programming-tech-gigs-scraper)
- [Bayt Jobs Scraper](https://apify.com/lentic_clockss/bayt-scraper)

**E-commerce**

- [Walmart Product Scraper](https://apify.com/lentic_clockss/walmart-scraper)
- [Amazon Search Scraper](https://apify.com/lentic_clockss/amazon-search-results-collector)
- [Shopee Search Scraper](https://apify.com/lentic_clockss/shopee-search-scraper)
- [Etsy Scraper](https://apify.com/lentic_clockss/etsy-scraper)
- [SHEIN Product Scraper](https://apify.com/lentic_clockss/shein-scraper)
- [Temu Product Scraper](https://apify.com/lentic_clockss/temu-scraper)
- [Target Product Scraper](https://apify.com/lentic_clockss/target-scraper)
- [Allegro Scraper](https://apify.com/lentic_clockss/allegro-scraper)

**Real Estate**

- [Zillow & Zumper Scraper](https://apify.com/lentic_clockss/us-real-estate-scraper)
- [Realtor.com Scraper](https://apify.com/lentic_clockss/realtor-com-scraper)
- [Apartments.com Rental Scraper](https://apify.com/lentic_clockss/apartments-com-rental-scraper)
- [Rightmove Scraper](https://apify.com/lentic_clockss/rightmove-property-scraper)
- [Idealista Scraper](https://apify.com/lentic_clockss/idealista-scraper)
- [realestate.com.au Scraper](https://apify.com/lentic_clockss/realestate-com-au-scraper)

**Travel & Stays**

- [Booking.com Hotels Scraper](https://apify.com/lentic_clockss/booking-hotels-scraper)
- [Airbnb Listings Scraper](https://apify.com/lentic_clockss/airbnb-listings-scraper)
- [Expedia Scraper](https://apify.com/lentic_clockss/expedia-scraper)
- [TripAdvisor Scraper](https://apify.com/lentic_clockss/tripadvisor-scraper)

**Social & Content**

- [YouTube Research Scraper](https://apify.com/lentic_clockss/youtube-research-scraper)
- [TikTok Scraper](https://apify.com/lentic_clockss/tiktok-scraper)
- [Reddit Scraper](https://apify.com/lentic_clockss/reddit-scraper)
- [YouTube Shorts Scraper](https://apify.com/lentic_clockss/youtube-shorts-scraper)

**Ads Intelligence**

- [Facebook Ad Library Scraper](https://apify.com/lentic_clockss/facebook-ad-library-scraper)
- [TikTok Ads Scraper](https://apify.com/lentic_clockss/tiktok-ads-top-ads-actor)

**Local & Maps**

- [Google Maps Scraper](https://apify.com/lentic_clockss/google-maps-scraper)

→ Full catalog in [Related Actors](#related-actors), or browse [apify.com/lentic_clockss](https://apify.com/lentic_clockss).

Need a **custom** listing+detail scraper for another site? [Submit a custom scraper request](https://custom-scraper-intake-977720205770.us-central1.run.app/).

***

## How to use

### How to scrape Google Play Store

1. Open this Actor and click **Try for free**
2. Pick a **mode**: `search` (keyword), `category`, `home`, `developer`, `detail`, or `datasafety`
3. For search, enter `q` (any Play keyword — not only the schema default)
4. Set **market** (e.g. `us`, `jp`, `kr`) or override `hl` / `gl`
5. Optional: turn on **enrichDetails** for JSON-LD prices and ratings
6. Set `maxResults` (start with 3–10)
7. Click **Start** — rows appear in the Dataset tab
8. Download **JSON / CSV / Excel**, or read the dataset via API

Empty `{}` input still runs (search default `q=flashlight`) so platform auto-tests succeed. Production jobs should use a real keyword and storefront.

### How to extract Google Play data in Python

Use the official client, then read the dataset:

```python
from apify_client import ApifyClient

client = ApifyClient("<YOUR_API_TOKEN>")
run = client.actor("lentic_clockss/google-play-scraper").call(
    run_input={"mode": "search", "q": "tide chart", "market": "us", "maxResults": 10}
)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["name"], item["packageId"])
```

### How to scrape Google Play Store with JavaScript

```javascript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: '<YOUR_API_TOKEN>' });
const run = await client.actor('lentic_clockss/google-play-scraper').call({
    mode: 'search',
    q: 'tide chart',
    market: 'us',
    maxResults: 10,
});
const { items } = await client.dataset(run.defaultDatasetId).listItems();
console.log(items.map((row) => [row.name, row.packageId]));
```

***

## Input example

```json
{
  "mode": "search",
  "q": "blood pressure log",
  "c": "apps",
  "market": "us",
  "maxResults": 10,
  "enrichDetails": true
}
```

Category + FAMILY age chip:

```json
{
  "mode": "category",
  "category": "FAMILY",
  "age": "AGE_RANGE1",
  "market": "us",
  "maxResults": 10
}
```

Detail from live package ids (do not invent names):

```json
{
  "mode": "detail",
  "packageIds": ["com.google.android.apps.maps"],
  "market": "us",
  "includeDataSafety": true
}
```

### Input fields

| Field | Use |
| --- | --- |
| `mode` | `search` / `category` / `home` / `developer` / `detail` / `datasafety` |
| `q` | Play search query (`c=apps` only; `c=games` is closed / HTTP 404) |
| `category` | Play CODE (`GAME`, `SPORTS`, `WATCH_FACE`, …) |
| `age` | FAMILY chip `AGE_RANGE1` (5 & under) / `AGE_RANGE2` / `AGE_RANGE3` |
| `market` | 183 opened ISO presets |
| `hl` / `gl` | Language / country override |
| `developerId` | Numeric Play developer id |
| `packageIds` / `detailUrls` | Live ids or `https://play.google.com/store/apps/details?id=…` |
| `enrichDetails` | Fetch JSON-LD after list scrape |
| `includeDataSafety` | Attach data-safety summary |
| `maxResults` | 1–1000 (free plan capped at 200) |

***

## Output example

```json
{
  "listingId": "com.google.android.apps.maps",
  "packageId": "com.google.android.apps.maps",
  "name": "Google Maps",
  "type": "app",
  "status": "listed",
  "country": "US",
  "authority": "play.google.com",
  "developer": "Google LLC",
  "ratingValue": 3.24,
  "priceDisplay": "Free",
  "isPaid": false,
  "listingUrl": "https://play.google.com/store/apps/details?id=com.google.android.apps.maps&hl=en&gl=US"
}
```

***

## How much does it cost to scrape Google Play?

**Pay per event.** You pay a small **Actor start** fee plus a **result** fee for each dataset row. You do **not** pay Apify platform compute on top of that (developer covers platform usage).

| Event | Price |
| --- | --- |
| Actor start (`apify-actor-start`) | **$0.005** per run (one event per GB of memory; this Actor defaults to 1024 MB → one start) |
| Result (`apify-default-dataset-item`) | **$3.00 / 1,000** rows on FREE & BRONZE ($0.003 each) |

Store discount on **result** (same table as peer Actors):

| Tier | $/1,000 | per result |
| --- | --- | --- |
| FREE* | $3.00 | $0.003 |
| BRONZE | $3.00 | $0.003 |
| SILVER | $2.60 | $0.0026 |
| GOLD | $2.20 | $0.0022 |
| PLATINUM | $2.00 | $0.002 |
| DIAMOND | $1.60 | $0.0016 |

**Examples (FREE/BRONZE, 1024 MB):**

| Job | Approx. charge |
| --- | --- |
| 10 apps | $0.005 + $0.03 = **$0.035** |
| 100 apps | $0.005 + $0.30 = **$0.305** |
| 1,000 apps | $0.005 + $3.00 = **$3.005** |

Empty category shelves (e.g. DATING first-pack) write **0 results** → you still pay the start event only.

***

## Is scraping Google Play Store free?

You can try the Actor with Apify’s free plan subject to the **10 runs / 200 results** developer cap. After that, PPE applies as above. There is no Google Play API key to buy.

***

## FAQ

### Is there an official Google Play API?

Google does not offer a public, complete Play Store listing API for third-party ASO. This Actor is a **Google Play Store scraper / API alternative** over public HTML + JSON-LD.

### Can I scrape Google Play reviews?

**Review bodies are not collected.** Enabling `includeReviews` only adds a warning. Use a dedicated reviews Actor if you need full comment text.

### Do I need proxies or a Google login?

No Google account. Egress is provided by the scrape worker. Optional `hl` / `gl` select language and country.

### Why is a category empty?

Some CODEs (`DATING`, `MEDICAL`, `LIBRARIES_AND_DEMO`, `GAME_CASINO`, deprecated `FAMILY_*`) return HTTP 200 with **zero live** `details?id=` cards. The run **succeeds** with 0 items (`workerStatus=empty`).

### Why did `c=games` fail?

Play search catalog `c=games` returned HTTP 404 in measurement. Use `c=apps` and category `GAME` / `GAME_*`.

### How is this different from other Google Play scrapers?

Many Store Actors focus on **uncapped reviews** or **top charts**. This one focuses on **183 storefronts**, first-pack **search / category / home**, honest empty shelves, JSON-LD **prices**, and **data-safety** — without forging `batchexecute` or inventing package names.

| Need | This Actor |
| --- | --- |
| Keyword search + category + home across 183 `gl` | Yes |
| App details, price, IAP, screenshots | Yes (`enrichDetails` or `mode=detail`) |
| Data-safety headings | Yes |
| Dual-store ASO with Apple App Store | Yes (pair Actor) |
| Uncapped review bodies | No |
| Top Free / Top Paid / Top Grossing charts | No (legacy `/collection/topselling_*` is empty ESF) |

### Is it legal to scrape Google Play Store?

The Actor only reads **public listing pages**. You are responsible for complying with Google Play terms, local law, and your own use case (research, ASO, internal analytics). Do not use the data to spam developers.

### How do I integrate this Google Play scraper?

Use the [Apify API](https://docs.apify.com/api/v2), [Python client](https://docs.apify.com/api/client/python), [JavaScript client](https://docs.apify.com/api/client/js), [MCP](https://docs.apify.com/integrations/mcp), schedules, or webhooks. Export **JSON, CSV, or Excel** from the dataset.

***

## Support

Issues and feature requests: open them on the Actor page or ping telegram [@kane1200](https://t.me/kane1200). Custom scrapers: [intake form](https://custom-scraper-intake-977720205770.us-central1.run.app/).

***

## Related Actors

Public Actors from [lentic_clockss](https://apify.com/lentic_clockss). Click a name to open the Store detail page.

**App Stores & ASO**

- [Google Play Scraper](https://apify.com/lentic_clockss/google-play-scraper)
- [App Store Scraper | Charts, Apps, Reviews](https://apify.com/lentic_clockss/apple-app-store-scraper)

**Jobs & Freelance**

- [LinkedIn Jobs Scraper](https://apify.com/lentic_clockss/linkedin-jobs-scraper)
- [Bayt Jobs Scraper](https://apify.com/lentic_clockss/bayt-scraper)
- [Fiverr Gigs Scraper](https://apify.com/lentic_clockss/fiverr-programming-tech-gigs-scraper)
- [Freelancer.com Scraper](https://apify.com/lentic_clockss/freelancer-scraper)
- [Glassdoor Scraper](https://apify.com/lentic_clockss/glassdoor-scraper)
- [Himalayas Jobs Scraper](https://apify.com/lentic_clockss/himalayas-jobs-scraper)
- [Indeed Jobs Scraper](https://apify.com/lentic_clockss/indeed-jobs-scraper)
- [Jobicy Remote Jobs Scraper](https://apify.com/lentic_clockss/jobicy-remote-jobs-scraper)
- [RemoteOK Jobs Scraper](https://apify.com/lentic_clockss/remoteok-all-jobs-scraper)
- [SEEK Jobs Scraper](https://apify.com/lentic_clockss/seek-scraper)
- [Upwork Jobs Scraper](https://apify.com/lentic_clockss/upwork-jobs-scraper)

**Real Estate**

- [Zillow & Zumper Scraper](https://apify.com/lentic_clockss/us-real-estate-scraper)
- [Realtor.com Scraper](https://apify.com/lentic_clockss/realtor-com-scraper)
- [99.co Scraper](https://apify.com/lentic_clockss/ninetynine-co-sg-scraper)
- [Realtor.com Agents Scraper](https://apify.com/lentic_clockss/realtor-com-agents-scraper)
- [Apartments.com Rental Scraper](https://apify.com/lentic_clockss/apartments-com-rental-scraper)
- [Bayut Scraper](https://apify.com/lentic_clockss/bayut-uae-scraper)
- [Craigslist Housing Scraper](https://apify.com/lentic_clockss/craigslist-housing-scraper)
- [Daft.ie Scraper](https://apify.com/lentic_clockss/daft-property-scraper)
- [Dot Property Scraper](https://apify.com/lentic_clockss/dot-property-th-scraper)
- [FINN.no Scraper](https://apify.com/lentic_clockss/finn-scraper)
- [Funda Scraper](https://apify.com/lentic_clockss/funda-scraper)
- [Hepsiemlak Scraper](https://apify.com/lentic_clockss/hepsiemlak-scraper)
- [Idealista Scraper](https://apify.com/lentic_clockss/idealista-scraper)
- [Immobiliare.it Scraper](https://apify.com/lentic_clockss/immobiliare-property-scraper)
- [ImmoScout24 Scraper](https://apify.com/lentic_clockss/immobilienscout24-scraper)
- [Naver Land Scraper](https://apify.com/lentic_clockss/naver-land-scraper)
- [OpenSooq Scraper](https://apify.com/lentic_clockss/opensooq-real-estate-scraper)
- [Otodom Scraper](https://apify.com/lentic_clockss/otodom-scraper)
- [Property Finder Scraper](https://apify.com/lentic_clockss/property-finder-uae-scraper)
- [PropertyGuru Scraper](https://apify.com/lentic_clockss/propertyguru-sg-scraper)
- [realestate.com.au Scraper](https://apify.com/lentic_clockss/realestate-com-au-scraper)
- [Realtor.ca Scraper](https://apify.com/lentic_clockss/realtor-ca-scraper)
- [Rightmove Scraper](https://apify.com/lentic_clockss/rightmove-property-scraper)
- [SeLoger Scraper](https://apify.com/lentic_clockss/seloger-property-scraper)
- [SUUMO Scraper](https://apify.com/lentic_clockss/suumo-property-scraper)
- [Zillow Group Scraper](https://apify.com/lentic_clockss/zillow-group-scraper)

**E-commerce**

- [Shopee Search Scraper](https://apify.com/lentic_clockss/shopee-search-scraper)
- [E-commerce Scraper](https://apify.com/lentic_clockss/ecommerce-scraper)
- [1688 Global Product Search Scraper](https://apify.com/lentic_clockss/1688-global-scraper)
- [Allegro Scraper](https://apify.com/lentic_clockss/allegro-scraper)
- [Amazon Search Scraper](https://apify.com/lentic_clockss/amazon-search-results-collector)
- [ASOS Product Scraper](https://apify.com/lentic_clockss/asos-scraper)
- [Cdiscount Product Scraper](https://apify.com/lentic_clockss/cdiscount-scraper)
- [Costco Product Scraper](https://apify.com/lentic_clockss/costco-scraper)
- [Coupang Product Scraper](https://apify.com/lentic_clockss/coupang-scraper)
- [Etsy Scraper](https://apify.com/lentic_clockss/etsy-scraper)
- [Lazada Scraper](https://apify.com/lentic_clockss/lazada-ph-search-results-collector)
- [MercadoLibre Scraper](https://apify.com/lentic_clockss/mercadolibre-scraper)
- [Mercari Japan Scraper](https://apify.com/lentic_clockss/mercari-scraper)
- [Rakuten Japan Scraper](https://apify.com/lentic_clockss/rakuten-scraper)
- [SHEIN Product Scraper](https://apify.com/lentic_clockss/shein-scraper)
- [Target Product Scraper](https://apify.com/lentic_clockss/target-scraper)
- [Temu Product Scraper](https://apify.com/lentic_clockss/temu-scraper)
- [Walmart Product Scraper](https://apify.com/lentic_clockss/walmart-scraper)

**Travel & Stays**

- [Booking.com & Airbnb Scraper](https://apify.com/lentic_clockss/booking-airbnb-scraper)
- [Agoda Scraper](https://apify.com/lentic_clockss/agoda-scraper)
- [Airbnb Listings Scraper](https://apify.com/lentic_clockss/airbnb-listings-scraper)
- [Booking.com Hotels Scraper](https://apify.com/lentic_clockss/booking-hotels-scraper)
- [Despegar Scraper](https://apify.com/lentic_clockss/despegar-scraper)
- [Expedia Scraper](https://apify.com/lentic_clockss/expedia-scraper)
- [Traveloka Scraper](https://apify.com/lentic_clockss/traveloka-scraper)
- [Travelstart Flights Scraper](https://apify.com/lentic_clockss/travelstart-scraper)
- [Trip.com Scraper](https://apify.com/lentic_clockss/trip-com-scraper)
- [TripAdvisor Scraper](https://apify.com/lentic_clockss/tripadvisor-scraper)

**Social & Content**

- [TikTok Scraper](https://apify.com/lentic_clockss/tiktok-scraper)
- [Reddit Scraper](https://apify.com/lentic_clockss/reddit-scraper)
- [YouTube Shorts Scraper](https://apify.com/lentic_clockss/youtube-shorts-scraper)
- [YouTube Research Scraper](https://apify.com/lentic_clockss/youtube-research-scraper)
- [Hacker News Scraper](https://apify.com/lentic_clockss/hacker-news-scraper)

**Ads Intelligence**

- [Facebook Ad Library Scraper](https://apify.com/lentic_clockss/facebook-ad-library-scraper)
- [Google Ads Transparency VN](https://apify.com/lentic_clockss/google-ads-transparency-center-vn)
- [TikTok Ads Scraper](https://apify.com/lentic_clockss/tiktok-ads-top-ads-actor)

**Local & Maps**

- [Google Maps Scraper](https://apify.com/lentic_clockss/google-maps-scraper)

**General Tools**

- [Stealth Web Scraper](https://apify.com/lentic_clockss/stealth-web-scraper)
- [Email Risk Validator](https://apify.com/lentic_clockss/email-risk-validator)
- [Phone Number Intelligence](https://apify.com/lentic_clockss/phone-number-intelligence)

→ Browse the full profile: [apify.com/lentic_clockss](https://apify.com/lentic_clockss)
