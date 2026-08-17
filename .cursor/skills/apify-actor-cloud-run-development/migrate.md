# Live migration: thick Actor → thin Actor + Cloud Run worker

Parent skill: [SKILL.md](SKILL.md). Use only when the user explicitly asks to replace a
**live** Store Actor (`改成 actor+worker`, Console Actor URL, “replace online”).

## Defaults

| Item | Default |
| --- | --- |
| Comm language | Match the user (often 中文) |
| Worker path | `/Users/kane/Projects/google run worker/<site>-com/` |
| Actor path | `/Users/kane/Projects/Apify Actors/<actor-name>/` (**in place**) |
| GCP | `woker-260722` |
| Auth | Worker `WORKER_API_KEY`; Actor `WORKER_BASE_URL` + `WORKER_AUTH` (secret) |
| Store | **Publish** after smoke; **inherit all** Store config; **do not change prices** |
| Platform usage | Ensure `isPPEPlatformUsagePaidByUser: true` |
| PPE / Store prices | Out of scope unless user explicitly asks to change |

## Checklist

```
- [ ] 0. Resolve Actor ID / local path (do not trust wrong console IDs)
- [ ] 0a. Recon contract + coverage matrix (website-page-research one-pager or templates/worker-contract.md)
- [ ] 1. Engine evaluation from recon channels → inherit source as floor ([engines.md](engines.md))
- [ ] 2. Scaffold + implement worker (OpenAPI + API key); scripts/assert_cwd.sh worker
- [ ] 3. Register workerId → deploy (never --set-env-vars) → scripts/worker_triple_smoke.sh
- [ ] 4. Thin Actor in place (worker_client, slim Docker, Standby+PPE)
- [ ] 5. Set Actor env → apify push → rebuild with env if needed
- [ ] 6. Cloud smoke + DQ (random-valid --input-file — parent §9)
- [ ] 7. Store publish (inherit config, no price change, platform usage yes) — Kane unless asked
```

## 0. Resolve identity

1. Console URL `https://console.apify.com/actors/<ID>` → fetch via Apify API / `apify` CLI.
2. Confirm `username/name` and **local folder** under `Apify Actors/`.
3. **Verify ID matches the intended product** (past mistake: LinkedIn link → Facebook Actor).
4. `move_agent_to_root` multi-root: worker dir (create empty if needed) + Actor dir.

## 1–4. Build path

Follow parent skill §3–§5. Write engine evaluation into worker README before deploy:

```text
Engine evaluation:
  A (historical): ...
  B (GitHub): ...
  C (public): ...
Default provider: curl | patchright | camoufox | ...
Inherited from: <actor-name> (<engine>)
Proxy: worker egress-control → PROXY_URL / provider (Actor WORKER_PROVIDES_PROXY=1)
Egress workerId: <service-name>
Region: <region> (<site geography rationale>)
Escalate: ...
```

Keep **dataset field names** compatible with existing Store DQ. Strip Apify SDK from
engine modules moved into the worker; accept optional `proxyUrl` + `PROXY_URL` after
`apply_runtime_env` ([egress-control.md](egress-control.md)).

## 5. Replace online Actor

1. Set env on **all relevant versions**:
   - `WORKER_BASE_URL` (plain)
   - `WORKER_AUTH` (**isSecret**) = worker `WORKER_API_KEY`
   - **`WORKER_PROVIDES_PROXY=1`** (default for worker-backed Actors)
2. `apify push` from Actor dir (same Actor ID / name — do not create a new listing).
3. If first run fails missing env: rebuild with **`applyEnvVarsToBuild=true`**; tag `latest`.
4. Confirm build log: **Found web server schema** when Standby OpenAPI is packaged.

## 6. Cloud smoke + DQ

Use parent §9 random-input policy. Require:

- Status **SUCCEEDED**
- Dataset ≥ 1 item
- Preview/schema fields present
- Logs show worker health + `provider`; `workerBaseUrlSource=env`

## 7. Store publish (inherit, no price change)

**Goal:** same Store listing, new build live, metadata/PPE unchanged.

1. Snapshot **before**: `title`, `categories`, SEO, `isPublic`, full `pricingInfos`
   (event names + USD), especially `isPPEPlatformUsagePaidByUser`.
2. Publish method that worked in practice:
   - `PUT /v2/acts/{actorId}` with inherited public metadata + `taggedBuilds.latest` → new build
   - **Do not** send pricing mutation fields unless only flipping
     `isPPEPlatformUsagePaidByUser` to true while copying prices exactly
3. Snapshot **after**: prices identical; `isPPEPlatformUsagePaidByUser === true`;
   same actor id / Store URL
4. Do **not** create a second Store listing or change username

If platform usage already `true`, leave it; if `false`/`null`, append a new PPE
`pricingInfos` entry only by **copying all event prices** and setting
`isPPEPlatformUsagePaidByUser: true`.

## Definition of done (migration)

- [ ] Engine evaluation in worker README; default provider inherited
- [ ] Region matches site geography
- [ ] Worker OpenAPI live; scrape routes 401 without key
- [ ] Actor calls worker only via `https://` + API key
- [ ] Online Actor build replaced; cloud run SUCCEEDED with ≥1 Dataset items
- [ ] Standby schema builds cleanly when applicable
- [ ] Store published: same listing, prices unchanged, User pays platform usage = **yes**

## Reference pairs

| Worker | Actor | Engine |
| --- | --- | --- |
| `zillow-com` | `zillow-scraper` | curl_cffi |
| `apartments-com` | `apartments-com-rental-scraper` | camoufox (gen2) |
| `linkedin-com` | `linkedin-jobs-scraper` | patchright |
| `facebook-com` | `facebook-ad-library-scraper` | curl_cffi GraphQL |
| `realtor-com` | `realtor-com-scraper` | GraphQL + free tier |
| `ealestate-com-au` | `realestate-com-au-scraper` | Bright Data unlock + free tier |

Concrete notes: [examples.md](examples.md)
