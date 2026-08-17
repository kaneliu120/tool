# Per-surface channel contract + worker one-pager

Copy into the Chinese report (section 九 / 给 worker 的一页纸). Fill only measured cells.

## Per-surface contract

```text
Surface: {ontology code + site name}
Final URL template: {/path/{id} — placeholders, not a pile of live ids}
Market / locale: {host or header/cookie name}

Render family: {Next Pages | App Router RSC | pcmall | Gatsby | …}
Primary data layer: {path.walked.to.keys}
Siblings: {other pageProps keys that hold business data}
Ready signal: {keys + approx bytes}
Negative signal: {pause title / verify path / EPS identify}

Identity keys: {…}
Pagination: {pattern} / HTML keys {…} / XHR keys {…} / JSON-LD pages? {yes/no}
Filter/sort encoding: {example after one real change}

Internal channels (observation):
- {METHOD path} fields={…} header names={…} status machine={…}

Gate: {guest | soft-gate | hard-block | unknown}
HTTP contrast: {3 UA statuses; listing-like? }
DOM anchors: {data-test* first}

Validation: {已验证 | 部分 | 未验证}
```

## Worker one-pager (required)

```text
## 给 worker 的一页纸
- Coverage matrix: opened cells vs 未验证
- Per surface: primary channel, ready signal, gate, identity keys
- Suggested ladder (measured this session only)
- Do not: {e.g. BFF 400 must not HTML-fallback; JSON-LD cannot page}
- Smoke: draw random inputs from the FULL opened matrix (not README prefills)
```

Paste-ready for worker README coverage / ladder drafts. Empty cells stay 未验证.

## Status labels

- **已验证** — path resolves with expected shape in this session
- **部分** — parent found, child incomplete, or error body only
- **未验证** — keyword / third-party docs / worker fixture, not this session

Unvalidated paths stay out of 已确认.
