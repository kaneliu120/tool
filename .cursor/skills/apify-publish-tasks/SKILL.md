---
name: apify-publish-tasks
description: >-
  Research use cases, design, create, and Publish Apify Actor Tasks (Store
  Examples landing pages + SEO). Default batch size is 10 tasks per Actor.
  Covers scenario research, input design, API task create, Console Publication
  (SEO / visible inputs / dataset view), verify publicConfig + Examples URLs.
  Use when the user asks for Publish Task, public tasks, Actor Examples tab,
  task landing pages, SEO example tasks, 发布 Task, 公开 Task, Examples 落地页,
  or batch-create Store example tasks for an Apify Actor.
---

# Apify Publish Tasks (research → design → create → publish)

End-to-end workflow to ship **public Actor Tasks** as Store **Examples** landing
pages (SEO + AI discovery). Official docs:
[Publish your Actor task](https://docs.apify.com/actors/publishing/publish-task).

**Default batch size: 10 tasks** unless the user names another count (cap 50
per Actor). Prefer quality use-case landings over “default config” dumps.

## What a Task is (and is not)

| Is | Is not |
| --- | --- |
| Saved input + run options for **one** Actor | Multi-Actor orchestrator |
| Optional **Publish** → public `/examples/{slug}` page | Store PPE / monetization setup |
| Appears on Actor **Examples** tab | Automatic “call other Actors” |

Chain other Actors via **Integrations / Schedule / external orchestration** —
see [reference.md](reference.md#related-platform-features). Do not invent
multi-Actor DAG inside a Task.

## When to use

- User: Publish Task / 公开 Task / Examples / SEO landing / batch example tasks
- Actor is Store-published (or about to be) and needs discoverable use cases
- After Actor has `input_schema` + ≥1 `dataset_schema` view

## Agent orchestration (mandatory pattern)

Parent agent **owns the checklist** and may spawn subagents in parallel:

| Phase | Prefer | Notes |
| --- | --- | --- |
| Read Actor I/O + existing tasks | `explore` or parent | `input_schema`, `dataset_schema` views, README modes |
| Use-case / keyword research | `generalPurpose` or WebSearch | Map search intents → Actor capabilities |
| Create tasks via API | `shell` or parent | `apify api` POST actor-tasks |
| Console Publication publish | parent + [`use-my-browser`](../use-my-browser/SKILL.md) | No public publish API — Chrome Console |
| Verify | `shell` | `publicConfig.publishedAt` + Chrome open landing (curl may 403) |

If Apify plugin routing applies (Store/docs MCP), use the Apify subagent for
docs/API discovery; keep **publish** on Kane’s logged-in Chrome.

Copy and tick:

```
- [ ] 0. Prerequisites (published Actor, schema views, auth CLI)
- [ ] 1. Research ≥15 candidate use cases → select default 10
- [ ] 2. Design pack (slug, SEO, input, view, proxy/locale)
- [ ] 3. Create 10 tasks via API (or Console Save as task)
- [ ] 4. Optional: smoke-run cheapest configs (small maxItems)
- [ ] 5. Console Publication ×10 (Display + Input + Dataset + Publish×2)
- [ ] 6. Fix dataset views if mismatched
- [ ] 7. Verify API publicConfig + Chrome Examples/landing
- [ ] 8. Mem0 handoff + artifact JSON under /tmp or Downloads
```

## 0. Prerequisites

1. Actor **owned/maintained** and **published** (public Store page OK).
2. Actor has **input schema** and **≥1 dataset schema view**
   (`.actor/dataset_schema.json` → `views`).
3. Local `apify` CLI logged in as the owning user.
4. Count: **default 10**; remaining capacity = `50 - existingPublicOrPrivateTasks`
   (max 50 tasks/Actor total).

```bash
# Identity
apify api get "acts/<username>~<actor-name>"
# List tasks (filter by actId in client code)
apify api get "actor-tasks?limit=100"
```

If dataset views are missing → **stop publish**; add views + `apify push` first.

## 1. Research use cases

Goal: 10 landings a human/AI would search for — not “default run”.

For each candidate jot:

- **User goal** (verb + object + qualifier): location / industry / workflow
- **Actor mode/path** that actually supports it (must be true)
- **Search / AI keywords** the title should capture
- **Why distinct** from the other 9 (no near-duplicates)

Sources: Actor README + input enums, competitor Store Examples, Web search
intents for the vertical. Produce **≥15 candidates**, then pick **10**.

Weak vs strong (from Apify docs):

| ❌ | ✅ |
| --- | --- |
| Default config / Test run | Find dentists in San Francisco with reviews |
| All fields enabled | Monitor Amazon prices for market research |

## 2. Design pack (one row per task)

Write `/tmp/<actor>_publish_tasks_design.json` (or Downloads) with **exactly 10**
(or N) objects:

```json
{
  "slug": "us-beauty-top-ads-30d",
  "title": "Find US beauty top ads (30 days)",
  "seoTitle": "Find US beauty TikTok top ads (30 days)",
  "seoDescription": "Export … (≈140–160 chars, outcome-focused)",
  "datasetView": "overview",
  "visibleInputFields": ["source", "country", "industries", "period", "maxItems"],
  "input": { },
  "options": { "memoryMbytes": 1024, "timeoutSecs": 3600 }
}
```

Rules:

- **slug**: short kebab-case; used in
  `https://apify.com/<user>/<actor>/examples/<slug>`
- **seoTitle**: action + target + qualifier (user goal, not Actor mechanics)
- **seoDescription**: what you get + for whom; avoid stuffing
- **input**: real runnable config; keep **result caps small** for any smoke
  (e.g. maxItems 10–20); match proxy/country to market when Actor uses proxy
- **datasetView**: view **id** from `dataset_schema.views` that matches the
  output shape of that mode (e.g. ads-library vs creative-center)
- **visibleInputFields**: subset shown on landing; full input still runs
- Mark `isSecret` fields in Actor schema before publish (auto-masked)

## 3. Create tasks (API)

Prefer API create; Publication still needs Console.

```bash
# Body shape (fields per current Apify API — verify with --describe)
apify api POST actor-tasks -d '{
  "actId": "<ACTOR_ID>",
  "name": "<slug>",
  "title": "<title>",
  "input": { },
  "options": { "memoryMbytes": 1024, "timeoutSecs": 3600 }
}'
```

Save ids → `/tmp/<actor>_tasks_created.json` (`slug`, `id`, design fields).

Idempotency: if slug exists, reuse id; do not create duplicates.

## 4. Optional smoke

For risky/new Actors, run 1–2 cheapest tasks (or all 10 with tiny caps) and
confirm dataset rows before publish. Skip only if Kane waives / Actor already
proven for those inputs.

## 5. Publish in Console (required)

**There is no reliable public OpenAPI to set `publicConfig` / publish.**
`PUT /v2/actor-tasks/{id}` with `publicConfig` often fails schema validation
(`renderableAt is not allowed`). Use Chrome:

URL: `https://console.apify.com/actors/tasks/<taskId>/publication`

For each task:

1. **Display information** — slug (if editable), SEO title, SEO description → **Save**
2. **Input** — select fields relevant to the use case (not always “Select all”) → **Save**
3. **Dataset schema** — open tab → pick correct view → **Save**
4. **Publish task** → confirm dialog → click **Publish** again (two clicks)
5. Stop when UI shows **Public** / **Unpublish task** / **View public page**

Browser skill: [`use-my-browser`](../use-my-browser/SKILL.md). Parallelize
reads; serialize Console publishes if the same Chrome profile is shared.

Automation pitfalls → [reference.md](reference.md#console-automation-gotchas).

## 6. Fix dataset view after publish

If `publicConfig.datasetView` is wrong:

1. Console → Publication → **Dataset schema** → select view → **Save**
2. Do **not** rely on PUT `publicConfig` via API

## 7. Verify (do not claim done without this)

Per task:

```bash
apify api get "actor-tasks/<taskId>"
# require: data.publicConfig.publishedAt, seoTitle, seoDescription, datasetView
```

Landing:

- Chrome open `https://apify.com/<user>/<actor>/examples/<slug>` → title/H1 OK
- Actor page Examples links contain all slugs
- **curl may return 403** (WAF) — not proof of failure; prefer Chrome

Report table: slug | taskId | publishedAt | datasetView | landing URL | OK/fail.

## 8. Handoff

Mem0 `handoff` for the Actor project: count published, artifact paths, gotchas,
next (remaining candidates / Integrations). Never store tokens/secrets.

## Quality bar

- Default **10** distinct, searchable use cases
- Titles = user goals; inputs actually valid for the Actor
- Correct **datasetView** per mode
- Secrets never visible on landing
- No “published” claim without `publicConfig.publishedAt` + spot-check landing

## Additional resources

- [reference.md](reference.md) — API/Console gotchas, design templates, Integrations note
- Docs: [tasks](https://docs.apify.com/actors/running/tasks), [publish-task](https://docs.apify.com/actors/publishing/publish-task), [Actor integrations](https://docs.apify.com/integrations/actors)
