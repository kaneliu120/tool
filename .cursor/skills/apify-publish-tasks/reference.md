# Apify Publish Tasks — reference

Companion to [SKILL.md](SKILL.md). Read when implementing create/publish or debugging.

## Limits and product facts

| Fact | Value |
| --- | --- |
| Max tasks per Actor | 50 |
| Public task = | SEO landing + Actor Examples tab + AI-readable `.md` variant |
| Visitor “Try” | Copies task to visitor account; does **not** burn owner CU |
| Input section on Publication | Display-only subset; run still uses full saved input |
| `isSecret: true` fields | Auto-masked on landing |

## API: create vs publish

### Create / update task (OK)

- `POST /v2/actor-tasks` — create (`actId`, `name`, `title`, `input`, `options`, …)
- `PUT /v2/actor-tasks/{actorTaskId}` — update input/title/options
- `GET /v2/actor-tasks/{actorTaskId}` — read; after publish includes `publicConfig`

Describe before coding:

```bash
apify api --describe actor-tasks
apify api --describe "actor-tasks/{actorTaskId}"
```

### Publish / publicConfig (fragile)

Observed failure when PUT-ing `publicConfig` (including “writable-only” fields):

```text
schema-validation: publicConfig.renderableAt is not allowed by the schema
```

**Canonical publish path:** Console Publication UI (Chrome).

After Console publish, GET returns e.g.:

```json
{
  "publicConfig": {
    "publishedAt": "2026-07-29T10:00:03.187Z",
    "renderableAt": "2026-07-29T10:00:03.187Z",
    "seoTitle": "...",
    "seoDescription": "...",
    "inputSchemaFields": ["fieldA", "fieldB"],
    "datasetView": "overview",
    "datasetName": null
  }
}
```

`datasetView` is the **view key** from Actor `dataset_schema.views` (e.g. `overview`,
`ads_library_overview`), not the human label alone.

## Console automation gotchas

1. **Two Publish clicks** — `Publish task` opens “Before you publish”; must click
   confirm **Publish** (exact label, not only the first button).
2. **Dataset schema tab** — view dropdown is under the **Dataset schema** tab;
   not visible on Display-only scroll. Open tab → combobox → choose view → Save.
3. **“Select all” inputs** — OK as fallback; prefer design pack
   `visibleInputFields` for cleaner landings.
4. **Saving… stuck** — wait for `Task changes saved`; reload Publication URL if hung.
5. **Already Public** — UI shows `Unpublish task` / `View public page`; skip re-publish.
6. **Same Chrome profile** — serialize publishes; don’t parallelize two Console
   writers on one window.
7. **curl 403 on examples** — common WAF; verify with Chrome / `publicConfig`.

Suggested Console flow (JS sketch; adapt selectors):

1. Fill `#seoTitle` / `#seoDescription` (React controlled: native value setter + input/change).
2. Save → Input tab field selection → Save.
3. Dataset schema tab → `[role=combobox]` → `[role=option]` matching label → Save.
4. Click button text `Publish task` → wait → click button text `Publish`.
5. Assert body contains `Unpublish task`.

Bridge: `~/.cursor/skills/use-my-browser/scripts/chrome_js_bridge.py`.

## Design templates

### Scenario brainstorm dimensions

Pick distinct cells across:

- Geography / market
- Vertical / category / query
- Workflow (monitor, compare, export, enrich, lead-gen)
- Time window / sort / filter the Actor supports
- Output angle (table for analysts vs creative swipe file)

### SEO title formula

`{Action} {target} {qualifier}`

Examples: Find / Track / Compare / Export / Monitor + noun + location|industry|period.

### SEO description formula

`{Outcome}. {Who/why}. {What fields or format}.` ≈ 140–160 chars.

### Design JSON array (default 10)

```json
[
  {
    "slug": "example-slug-one",
    "title": "Human Console title",
    "seoTitle": "Search-oriented title",
    "seoDescription": "Outcome-focused meta description under ~160 chars.",
    "datasetView": "overview",
    "visibleInputFields": ["query", "country", "maxItems"],
    "input": {},
    "options": { "memoryMbytes": 1024, "timeoutSecs": 3600 },
    "priority": 1,
    "notes": "why this landing; which Actor mode"
  }
]
```

Ship file: `/tmp/<actorName>_publish_tasks_design.json` and
`/tmp/<actorName>_tasks_created.json` after API create.

## Verification checklist

Per task:

- [ ] `publicConfig.publishedAt` present
- [ ] `seoTitle` / `seoDescription` match design
- [ ] `datasetView` matches mode
- [ ] `inputSchemaFields` not dumping irrelevant secrets
- [ ] Chrome landing H1 ≈ seoTitle
- [ ] Actor Store page HTML/Examples lists slug

Batch OK only when **all N** (default 10) pass or failures listed with next fix.

## Related platform features

Not part of Publish Task, but often asked:

| Need | Use |
| --- | --- |
| Run A then B with dataset id | [Actor-to-Actor integrations](https://docs.apify.com/integrations/actors) on Actor/Task **Integrations** tab |
| Cron multiple tasks | [Schedules](https://docs.apify.com/actors/running/schedules) (`RUN_ACTOR_TASK` actions) |
| Complex DAG | Make / n8n / Kestra / orchestrator Actor |

Task = single-Actor preset; Integrations = chain.

## Exemplar (tiktok-ads-top-ads-actor, 2026-07-29)

Published 5 first (skill default is now **10** for new Actors):

| Slug | View |
| --- | --- |
| `us-beauty-top-ads-30d` | `overview` |
| `fr-shopify-ads-library` | `ads_library_overview` |
| `uk-competitor-long-running-ads` | `ads_library_overview` |
| `japan-market-entry-top-ads` | `overview` |
| `us-beauty-conversions-vs-traffic` | `overview` |

Pattern: Creative Center → `overview`; Ads Library/CCL → `ads_library_*`.

## Subagent prompt snippets

**Research subagent:** given Actor README + input_schema path, return ≥15 use
cases with slug/title/seo/mode/input sketch; mark top 10.

**Create subagent:** given design JSON + actId, POST missing tasks; write
created.json; never print tokens.

**Publish subagent:** given created.json, drive Chrome Publication for each id;
two-step Publish; return public/private per row.

Parent merges verify + Mem0 handoff.
