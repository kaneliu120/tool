# Job-board pack

Read after the core skill for jobs SERP/LDP and employer-intelligence sites (Glassdoor-class). Do **not** force sale/rent.

## Extra surfaces

| Extra | Open |
|---|---|
| Jobs SERP | keyword + location/remote |
| Job LDP / viewjob | **live SERP link only** |
| Company / employer overview | one known employer if the product has it |
| Reviews / Salaries / Interviews / Benefits | only if tabs exist |
| Easy Apply chrome | record presence and URL **shape**; never click |

Map from generic ontology: Search → Jobs SERP; Detail → job LDP; Entity → Company Overview; Reputation → Reviews/Interviews; Economics → Salaries/Benefits.

## Extra field groups

- Apply: Easy Apply / directApply / apply URL shape (presence only)
- Job type, seniority, remote, date posted, sponsored
- Employer rating crossed onto job cards
- Interview difficulty / outcome / questions (often login-gated)
- Salary source: employer-provided vs estimate; base vs total comp
- Benefits categories + employer-verified flags
- `contentDepth=public_preview|sign_in_gated|full` on every employer-intel surface

## Habits

- Two frontend **monos** are common (`job-search-next` vs `employer-profile-mono`) — treat as forks
- Indeed Mosaic: `script#mosaic-data` / `window.mosaic.providerData["mosaic-provider-jobcards"]` before generic Next
- Missing `__NEXT_DATA__` on App Router is normal; RSC concat may be the primary layer
- Login soft-gates: “Sign in to unlock…” — do not list locked salary/review bodies as 已确认
- Never click Apply / Easy Apply / create alert

## Probe EXTRA_KEYS

`mosaic-provider-jobcards`, `JobPosting`, `contentDepth`, `job-search-next`, `employer-profile-mono`
