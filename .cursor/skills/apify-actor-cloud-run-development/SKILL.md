---
name: apify-actor-cloud-run-development
description: >-
  Kane's end-to-end Apify Actor + Cloud Run worker workflow: thin Actor, thick
  authenticated worker, recon contract before parse, full-site coverage matrix,
  engine evaluation, Standby, free-tier, thin-Actor compute (1024 MB), live
  Store migration, randomized cloud smoke, egress-control. Use when building or
  refactoring Actors/workers, WORKER_BASE_URL / WORKER_AUTH / WORKER_PROVIDES_PROXY,
  改成 actor+worker, 覆盖矩阵, 调研契约, online acceptance, or Cloud Run deploy.
  Vertical field lists live in website-page-research packs — do not duplicate.
---

# Apify Actor + Cloud Run development (unified)

**Source of truth:** this skill directory (`~/.cursor/skills/apify-actor-cloud-run-development/` or `~/.agents/skills/…`).  
`Apify Actors/docs/CLOUD_RUN_ACTOR_DEVELOPMENT_STANDARD.md` and `google run worker/docs/…` are **mirrors** — edit here first, then copy. Do not three-way edit.

Thin Actor / thick worker / egress-control. Replaces split skills `cloud-run-apify-actor`, `migrate-apify-actor-worker`, `apify-actor-free-tier-limits` (redirect stubs).

Official Apify `apify-actor-development` (Crawlee-in-Actor) is **not** this architecture. Use it only for Store discovery / thick-Actor packaging. Kane workers: this skill.

## Route the request

| User intent | Branch |
| --- | --- |
| New worker/Actor, or refactor offline | **A. Build** — four phases below |
| Paste Console URL / “改成 actor+worker” | **B. Live migration** ([migrate.md](migrate.md)) + A |
| Free-tier / `APIFY_USER_IS_PAYING` | **C** [free-tier.md](free-tier.md) |
| Memory / CU / `defaultRunOptions` | **D** [actor-compute-cost.md](actor-compute-cost.md) |
| Egress / `worker.opendata.best` / proxy×engine | **E** [egress-control.md](egress-control.md) |
| Bright Data / RiskByPass / Kasada **fit** | [`bright-data-riskbypass`](../bright-data-riskbypass/SKILL.md) — creds via egress |
| Camoufox crashes on Cloud Run | [`camoufox-cloud-run`](../camoufox-cloud-run/SKILL.md) |
| Publish Task / Examples | [`apify-publish-tasks`](../apify-publish-tasks/SKILL.md) |
| Page structure / fields / gates | [`website-page-research`](../website-page-research/SKILL.md) — **Phase 0** |

Pitfalls: [pitfalls.md](pitfalls.md). Copy vs rewrite: [templates/copy-vs-rewrite.md](templates/copy-vs-rewrite.md).

## Four phases (do not skip)

```
Phase 0  Recon contract (website-page-research one-pager or live recon)
Phase 1  Factory: scaffold worker infra + thin Actor (no site selectors)
Phase 2  Site delta: parse / ladder / markets only
Phase 3  Gates: cwd → register workerId → deploy → triple smoke → random Actor smoke
```

**No contract → no parse → no “ready”.** Scripts failing = not done (do not tick by hand).

Factory vs delta: [templates/copy-vs-rewrite.md](templates/copy-vs-rewrite.md). Vertical fields: `website-page-research/packs/` (ticketing, ecommerce, jobs, …) — do not copy field lists into this skill.

## Progress checklist (copy and tick)

```
- [ ] 0. Identity: Actor ID + local Actor path + worker path (API-resolve; do not trust wrong Console links)
- [ ] 0cwd. bash scripts/assert_cwd.sh worker|actor before edits/deploy; print_deploy_plan.sh before gcloud
- [ ] 0a. Recon contract: coverage matrix + per-surface channel contract + ready/negative signals + suggested ladder
      (website-page-research report or templates/worker-contract.md). Empty cells = 未验证
- [ ] 0b. Full coverage matrix in README (§1b + templates/coverage-matrix.md) — non-MVP
- [ ] 1. Engine: recon channels first, then A/B/C (engines.md); inherit source as floor; region by site geography
- [ ] 2. Worker factory: OpenAPI + WORKER_API_KEY; sync_shared; scripts/scaffold_worker.sh from peer
- [ ] 2b. Register workerId (scripts/register_egress_worker.sh) then Cloud Run with runtime key — never --set-env-vars wipe
- [ ] 2c. Proxy↔engine per egress-control.md §8
- [ ] 3. bash scripts/worker_triple_smoke.sh (health 200, unauth 401, auth rows ≥1)
- [ ] 4. Thin Actor factory: worker_client, 1024 MB, Standby, WORKER_PROVIDES_PROXY=1 (scripts/scaffold_actor.sh)
- [ ] 4s. Schema: every REQUIRED field has default (= prefill) or is optional; empty {} run SUCCEEDED
- [ ] 5. Actor env: WORKER_BASE_URL + WORKER_AUTH + WORKER_PROVIDES_PROXY=1; rebuild latest if env is new
- [ ] 6. Free tier when Store-facing
- [ ] 7. python3 scripts/random_smoke_input.py → apify call -f (never README/prefill)
- [ ] 8. Live migration only: inherit prices; platform usage yes
```

---

## 1b. Full product coverage (non-MVP)

Entire product surface — not MVP / single-market. Template: [templates/coverage-matrix.md](templates/coverage-matrix.md).

| Dimension | Required |
| --- | --- |
| **Countries / regions** | All locales / TLDs / market switches the site exposes |
| **Product categories** | All taxonomy branches in scope |
| **Services / modes** | Map to recon ontology: Search, Category, Detail, overlay, market switch — not a vague “all services” sentence |

Rules: matrix in README before coding; source Actor is a **floor**; schema exposes the full matrix; random smoke draws from **opened** cells + spot-check ≥1 secondary market and ≥1 non-primary category; partial ship is a defect without Kane waiver.

---

## 1. Architecture (do not invert)

```
Apify Actor (thin)  --HTTPS + API key-->  Cloud Run worker (heavy)  -->  target site
  input / dataset / PPE / Standby           scrape + parse + OpenAPI
  free-tier                                 engine + apply_runtime_env
                                              │
                                              ▼
                                    egress-control https://worker.opendata.best
```

| Layer | Owns | Must not own |
| --- | --- | --- |
| **egress-control** | Fleet proxy/unlock + per-worker policy | Scrape logic; Actor I/O; PPE |
| **Worker** | Engine, parse, pagination, OpenAPI, scrape auth | Dataset, SEO, PPE, free-tier, **admin** egress key |
| **Actor** | Input, worker client, push_data, KV, README/SEO, PPE, Standby, free-tier | Browser/Kasada/unlock; egress-control calls; vendor secrets |

| Type | Path |
| --- | --- |
| Worker | `/Users/kane/Projects/google run worker/<site>-com/` |
| Actor | `/Users/kane/Projects/Apify Actors/<actor-name>/` (migrate **in place**) |
| GCP | `woker-260722` |

Details: [reference.md](reference.md).

---

## 2. Non-negotiable security + contract

| Rule | Detail |
| --- | --- |
| OpenAPI 3.x | `/openapi.json`, `/openapi.yaml`, `/docs` |
| HTTPS | Production `WORKER_BASE_URL` is `https://` |
| Worker secret | `WORKER_API_KEY`; scrape routes Bearer and/or `X-Api-Key` |
| Actor secret | **`WORKER_AUTH`** (legacy `WORKER_API_KEY` fallback) |
| Public | `/health` + docs; `/v1/search|listings|categories` **401** without key |
| Override | `workerBaseUrl` only if HTTPS + allowlisted — never send auth to arbitrary URLs |
| Secrets | Never commit keys / full `proxyUrl` |

Envelope: `{ status, items, diagnostics, provider, warnings, worker, schemaVersion }`.

---

## 3. Engine + region

Order: **recon channel contract** → A historical → B GitHub → C public. Stars do not beat measured BFF/RSC/DOM. Inherit source engine as floor; escalate only on measured blocks.

Ladder (see [engines.md](engines.md)): native/same-origin JSON → `curl_cffi`+residential → Camoufox/Patchright → **orchestrator CDP** (hosted Chrome + own residential; **not** orch `/v1/unlock`, which may still be Bright Data) → Unlocker last if already production-proven. Do not claim Unlocker can be dropped because a pin path worked once.

Do **not** add Scrapling/Firecrawl/Crawlee as worker runtimes. Firecrawl Map = Phase 0 URL discovery 仅侧证.

| Site geography | Cloud Run `--region` |
| --- | --- |
| US | `us-central1` / `us-east1` |
| AU | `australia-southeast1` |
| EU | `europe-west1` / `europe-west4` |
| MENA | `me-west1` else `europe-west1` |

Region is immutable — redeploy to move, then update `WORKER_BASE_URL`.

---

## 4. Worker build + deploy

Scaffold: `scripts/scaffold_worker.sh <peer> <dest>` then rewrite only delta files ([templates/copy-vs-rewrite.md](templates/copy-vs-rewrite.md)).

| Engine | Peer |
| --- | --- |
| curl_cffi / HTTP | `zillow-com` / `glassdoor-com` |
| Camoufox + Xvfb | `apartments-com` (**gen2**) |
| Patchright + Chrome | `bayt-com` / `linkedin-com` / `walmart-com` |

Must: `auth.py`, OpenAPI security, `/health`+docs, protected `/v1/*`, `_shared/sync_shared.sh`, `apply_runtime_env`. Ignore `apify_actor_run` proxy URLs on Cloud Run.

**Before `gcloud run deploy --source=.`:** `bash scripts/assert_cwd.sh worker` then `bash scripts/print_deploy_plan.sh --region <geo> --env-file /tmp/<service>-env.yaml` (never from an Actor folder).

```bash
gcloud run deploy <service> \
  --project=woker-260722 --region=<geo> --source=. \
  --allow-unauthenticated --memory=2Gi --cpu=2 --timeout=900 \
  --concurrency=1 --min-instances=0 --max-instances=2 \
  --env-vars-file=/tmp/<service>-env.yaml
```

**Never** `--set-env-vars` as a wipe. After first deploy: `--update-env-vars` for additive keys. Comma-in-value (Apify proxy user) → **only** `--env-vars-file`.

Register then fetch runtime key (not admin, not fleet master): `scripts/register_egress_worker.sh <service>`.

Smoke: `scripts/worker_triple_smoke.sh`.

### 4b. Egress

Plane: `https://worker.opendata.best`. Full: [egress-control.md](egress-control.md) §8 matrix. Actor: `WORKER_PROVIDES_PROXY=1`, omit `proxyUrl`.

---

## 5. Thin Actor

Factory: `scripts/scaffold_actor.sh`. Keep schemas / Standby / `INPUT_ECHO` / `RUN_SUMMARY`. Remove browser/unlock.

- `worker_client.py` — HTTPS, allowlist, auth  
- `input_model.py` — omit `proxyUrl` when worker-owned  
- `main.py` — free-tier → healthcheck → `call_worker` → `push_data`  
- Docker: `apify/actor-python` · `CMD ["python", "-m", "src"]`  
- `WORKER_BASE_URL` env is production source of truth  

**Schema:** every REQUIRED field has `default` equal to `prefill`, or is optional. Platform auto-test uses `default`, not `prefill`. Empty `{}` must **SUCCEEDED** (not `Actor.fail()`). Kane cloud acceptance still uses **random** `--input-file`, not that default.

New env vars (including `WORKER_PROVIDES_PROXY`) may need **rebuild** `latest` before they appear in runs. Verify `proxySource=worker-env`.

### 5b. Compute

`defaultRunOptions.memoryMbytes` **1024** (not 2048/4096); min **512**; Standby ≤ run default. Do not smoke with `-m 2048`. Details: [actor-compute-cost.md](actor-compute-cost.md).

---

## 6. PPE / Store

New build: do **not** set PPE or Store-publish unless asked. Live migration: inherit prices; `isPPEPlatformUsagePaidByUser: true`. Never `charged_event_name="apify-default-dataset-item"` (synthetic).

### 6b. Overnight stop line

Agent: develop → GCP deploy → Apify push → acceptance. Kane: confirm, prices, Store publish.

**Must not claim ready** if any is missing: recon contract, matrix cells labeled, triple smoke JSON, random `--input-file` JSON, `assert_cwd` used on deploy. Do not mutate USD prices / `isPublic` / second listing.

Handoff: Actor ID + build · worker URL + region · matrix · free-tier caps · exact smoke JSON · open items (Unlocker still on, unopened markets).

---

## 7–8. Migration / free tier

[migrate.md](migrate.md) · [free-tier.md](free-tier.md). Free caps in **Actor** code; quota → `FREE_TIER_LIMIT` + SUCCEEDED.

---

## 9. Cloud smoke

Forbidden: README / How-to / schema prefill/default / Standby example / reused canaries.  
Required: `python3 scripts/random_smoke_input.py` from **opened** matrix cells; `maxResults` 2–5; `--input-file`; re-roll on 0 rows.

```bash
python3 "$SKILL_DIR/scripts/random_smoke_input.py" --matrix ./coverage-matrix.json --out /tmp/accept.json
apify call "<user>/<actor>" -b latest -f /tmp/accept.json -m 1024 -t 900
```

Assert SUCCEEDED, `workerBaseUrlSource=env`, rows ≥ 1, exact JSON in the note.

---

## 10. Definition of done

Scripts + contract beat verbal ticks.

- [ ] Recon contract + coverage matrix (empty = 未验证); not MVP  
- [ ] Engine + region in worker README (recon channels recorded)  
- [ ] `assert_cwd.sh` passed on worker deploy and Actor push  
- [ ] Worker OpenAPI; scrape 401 without key; triple smoke log saved  
- [ ] Egress: client wired; **registered** workerId; Cloud Run **runtime** key; §8 pairing  
- [ ] Thin Actor: no browser; no egress-control; `WORKER_PROVIDES_PROXY=1`; 1024 MB  
- [ ] REQUIRED schema defaults; `{}` SUCCEEDED  
- [ ] Free tier when Store-facing  
- [ ] Random `--input-file` from matrix SUCCEEDED + DQ  
- [ ] Kane handoff (§6b) — prices/publish left to Kane  

## Do not

- Skip Phase 0 / ship MVP without waiver  
- `gcloud run deploy --source=.` from an Actor directory  
- `--set-env-vars` wipe; `--update-env-vars` for comma-values  
- Cloud Run admin/master egress key; Actor calling the control plane  
- Unlock/browser in Actor; Crawlee/Firecrawl/Scrapling as worker default  
- orch `/v1/unlock` as “first-party unlock”  
- README/prefill as cloud acceptance; `-m 2048` to prove 1024  
- PPE Store publish on overnight runs  
- Duplicate website-page-research field packs here  

## Progressive disclosure

| File | When |
| --- | --- |
| [pitfalls.md](pitfalls.md) | Before deploy / when something “mysteriously” 422/405 |
| `scripts/print_deploy_plan.sh` | Before every `gcloud run deploy` |
| [templates/worker-contract.md](templates/worker-contract.md) | Phase 0 output |
| [templates/coverage-matrix.md](templates/coverage-matrix.md) | §1b table |
| [templates/copy-vs-rewrite.md](templates/copy-vs-rewrite.md) | Scaffold |
| [reference.md](reference.md) | OpenAPI, deploy flags, DQ |
| [engines.md](engines.md) | Ladder + audit |
| [egress-control.md](egress-control.md) | Runtime vs admin, §8 |
| [free-tier.md](free-tier.md) / [migrate.md](migrate.md) / [actor-compute-cost.md](actor-compute-cost.md) | Branches |
| [examples.md](examples.md) | Peer notes |
| [`../website-page-research/SKILL.md`](../website-page-research/SKILL.md) | Recon |
