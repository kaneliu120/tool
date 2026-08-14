# Migration examples (Actor → worker)

## LinkedIn Jobs (patchright)

| | |
| --- | --- |
| Actor ID | `vbjPXhgJ9u8XhMcCW` (`lentic_clockss/linkedin-jobs-scraper`) |
| Worker | `google run worker/linkedin-com` |
| Region | `us-central1` |
| Engine | Inherit Patchright CloakBrowser + Guest Jobs |
| Shell | bayt-com Dockerfile (Chrome/Xvfb) |
| Actor thin | `worker_client` + PPE `result` / dataset item + Standby→worker |
| Store | Inherit PPE; `isPPEPlatformUsagePaidByUser: true` |

## Facebook Ad Library (curl_cffi GraphQL)

| | |
| --- | --- |
| Actor ID | `ktGss02P7vYV4uGOS` (`lentic_clockss/facebook-ad-library-scraper`) |
| Worker | `google run worker/facebook-com` |
| Region | `us-central1` |
| Engine | Inherit curl_cffi + Ad Library GraphQL |
| Shell | glassdoor-com / zillow-com (slim Python) |
| Actor thin | Keep `checkpoint` + optional CDN `assets`; remove GraphQL from Actor |
| Pitfall | First push may need rebuild with `applyEnvVarsToBuild=true` so `WORKER_AUTH` is present |
| Store | Prices unchanged ($0.005 start / $0.002 item); platform usage yes |

## TikTok (patchright + CapSolver)

| | |
| --- | --- |
| Actor ID | `wsdAqpLn1ykYGHqAU` (`lentic_clockss/tiktok-scraper`) |
| Worker | `google run worker/tiktok-com` |
| Region | `us-central1` |
| Engine | Inherit Patchright CloakBrowser + XHR + CapSolver |
| Shell | bayt/linkedin Dockerfile (Chrome/Xvfb) |
| Actor thin | Keep optional video download via httpx; remove browser engine |
| Pitfall | `WorkerCollectionResult` must include fields main.py expects (`timings`); CapSolver secret may not be readable via API — set `CAPSOLVER_API_KEY` on Cloud Run env separately |
| Store | Inherit PPE; platform usage yes; prices unchanged |

## Booking.com Hotels (patchright)

| | |
| --- | --- |
| Actor ID | `vXrlagWWqZiiL48YR` (`lentic_clockss/booking-hotels-scraper`) |
| Worker | `google run worker/booking-com` |
| Region | `europe-west4` (Booking.com NL/EU HQ) |
| Engine | Inherit Patchright headed Chrome + Xvfb + CF wait (no CapSolver) |
| Shell | linkedin-com / bayt-com Dockerfile (Chrome/Xvfb) |
| Actor thin | `worker_client` + PPE dataset item + Standby façade; no browser in Actor |
| Pitfall | Slim `engine/__init__.py` after stripping Apify proxy helpers (`resolve_sticky_proxy`); cold-start: lazy-import scrape stack so PORT binds quickly; first Cloud Run deploy may need `--cpu-boost` |
| Store | Prices unchanged ($0.005 start / $0.003 item); `isPPEPlatformUsagePaidByUser: true` |


## Jobicy Remote Jobs (curl_cffi API)

| | |
| --- | --- |
| Actor ID | `WLN1jUzN2xm9fa4RN` (`lentic_clockss/jobicy-remote-jobs-scraper`) |
| Worker | `google run worker/jobicy-com` |
| Region | `us-central1` |
| Engine | Inherit curl_cffi → public Jobicy JSON API (no browser, no proxy required) |
| Shell | facebook-com / glassdoor-com (slim Python) |
| Actor thin | `worker_client` + Standby façade; remove `jobicy_client`/`collector` |
| Store | Prices unchanged ($0.005 start / $0.002 item); platform usage already yes |

## Lazada Product Search (Playwright AJAX)

| | |
| --- | --- |
| Actor ID | `Q6NsHrUhBzxboRav8` (`lentic_clockss/lazada-ph-search-results-collector`) |
| Worker | `google run worker/lazada-com` |
| Region | `australia-southeast1` (fallback — `asia-southeast1/2` new-region quota exceeded) |
| Engine | Inherit Store Playwright Chromium + in-page catalog AJAX; curl_cffi punished on smoke → escalated |
| Shell | Playwright Python base image (`mcr.microsoft.com/playwright/python:v1.60.0-jammy`) |
| Actor thin | `worker_client` + mint Apify RESIDENTIAL (country=market); remove browser stack |
| Pitfall | Pin `pydantic<2.12` (2.13 breaks apify/crawlee import); SEA region quota may force AU deploy |
| Store | Prices unchanged (`result-item` $0.0019); platform usage already yes |

## Himalayas Remote Jobs (curl_cffi API)

| | |
| --- | --- |
| Actor ID | `QOAYoqT7eaNUUceXb` (`lentic_clockss/himalayas-jobs-scraper`) |
| Worker | `google run worker/himalayas-com` |
| Region | `us-central1` |
| Engine | Inherit curl_cffi → public Himalayas paginated JSON API (`/jobs/api`, offset/limit 20) |
| Shell | jobicy-com (slim Python) |
| Actor thin | `worker_client` + Standby façade; remove `himalayas_client`/`collector` |
| Store | Prices unchanged ($0.005 start / $0.002 item); platform usage already yes |

## Daft.ie Property (curl_cffi + __NEXT_DATA__)

| | |
| --- | --- |
| Actor ID | `NWVnO9Yt3UsKQijLc` (`lentic_clockss/daft-property-scraper`) |
| Worker | `google run worker/daft-ie` |
| Region | `europe-west1` (Ireland / EU) |
| Engine | Inherit curl_cffi → HTML `__NEXT_DATA__` SRP+LDP; RESIDENTIAL IE `proxyUrl` |
| Shell | otodom-pl (curl Next.js EU twin) |
| Actor thin | `worker_client` + mint Apify RESIDENTIAL IE; remove scrape stack |
| Store | Prices unchanged ($0.005 start / $0.0025 item); platform usage already yes |

## Common pitfalls

1. **Wrong console ID** — always API-resolve `username/name` before push.
2. **Actor-run proxy on Cloud Run** — fall back to worker `PROXY_URL`.
3. **Env after push** — secrets on version may need rebuild to apply to `latest` runtime.
4. **Store PUT** — never mutate event unit prices; only inherit / ensure platform-usage flag.
5. **Worker `engine/__init__.py`** — after thinning proxy helpers, drop Apify-only exports or imports crash on first `/v1/search`.
