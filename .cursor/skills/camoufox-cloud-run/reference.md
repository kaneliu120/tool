# Camoufox Cloud Run — research notes & apartments-com proof

## Proof (2026-07-24)

| Step | Result |
| --- | --- |
| Patchright + RESIDENTIAL on Cloud Run | Akamai `Access Denied` |
| Camoufox on Cloud Run **gen1** after HOME/Xvfb | `Uncaught signal: 11` → `TargetClosedError` |
| Bright Data Unlocker / Scraping Browser (shopee zone) | Still blocked / extra cost — abandoned |
| Camoufox + **gen2** + HOME=/tmp seed + external Xvfb + `headless=True` | **OK** — Austin SRP `items≥2` |
| Thin Actor → worker canary | Run `U5C0rfxCHeT9zOzS7` SUCCEEDED, 3 dataset rows |

Worker URL pattern: `https://apartments-com-977720205770.us-central1.run.app`

## Why Apify CU worked but Cloud Run gen1 failed

Apify Actor images run Camoufox under a different sandbox/display story (`xvfb-run` in Actor Dockerfile is OK there because Apify is not Cloud Run's PORT probe model). Cloud Run **gen1** uses a restrictive execution environment where Firefox/Camoufox child processes often die with **signal 11**. Switching to **gen2** was decisive after filesystem/Xvfb hardening alone was not enough.

## Camoufox 0.5.x cache layout

```text
~/.cache/camoufox/
  browsers/official/<version>-<hash>/
    camoufox-bin
  …
```

Older docs/examples assume a flat `~/.cache/camoufox/camoufox-bin`. Seed and `hasBin` checks must recurse.

## Community issue map

| Issue | Takeaway used |
| --- | --- |
| [camoufox#572](https://github.com/daijro/camoufox/issues/572) | Cloud Run/Lambda: create `~/.camoufox`; writable fontconfig; ignore misleading GPU/glxtest noise |
| [camoufox#372](https://github.com/daijro/camoufox/issues/372) | Linux Docker `TargetClosedError` on `new_page` |
| [camoufox#44](https://github.com/daijro/camoufox/issues/44) | Need `libgtk-3-0`, `libx11-xcb1`, `libasound2` |
| [camoufox#288](https://github.com/daijro/camoufox/issues/288) | `playwright install-deps` before fetch; avoid runtime re-download |
| [openlegion#156](https://github.com/openlegion-ai/openlegion/pull/156) | External Xvfb + `headless=True` instead of `virtual` in Docker |
| [camoufox-js#68](https://github.com/apify/camoufox-js/issues/68) | `HOME=/tmp` + copy browser into writable cache |

## Optional escalate (only after checklist fails)

1. Re-check gen2 annotation: `run.googleapis.com/execution-environment=gen2`
2. Memory ≥4Gi, concurrency=1
3. strace / logs for EROFS on `~/.camoufox`
4. Patchright failover **only if** site accepts Chrome
5. Bright Data / unlockers — last resort, separate cost path ([bright-data-riskbypass](../bright-data-riskbypass/SKILL.md))
