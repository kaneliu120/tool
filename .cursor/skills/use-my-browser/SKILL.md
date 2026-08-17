---
name: use-my-browser
description: >-
  Drive the user's real Google Chrome session on macOS via AppleScript.
  On Cloud Agents this skill is unavailable (no Mac Chrome). Use the VM
  desktop / Playwright instead. Trigger words: 调用我的浏览器, use my Chrome.
---

# use-my-browser — Cloud Agent stub

This skill requires Kane's **macOS Chrome + AppleScript**. It does **not** run on Cursor Cloud Agent Ubuntu VMs.

On Cloud Agents:

1. Do **not** call `osascript` or probe `/Users/kane`.
2. Use the VM desktop (computer use) or Playwright/Patchright already on the snapshot.
3. For REA/Kasada live HTML, follow repo README: Mac Chrome runner is the product default; Linux is experiment-only (`REA_ALLOW_LINUX_RUNNER=1`).
4. For Mem0 / page recon, use HTTP MCP and `website-page-research` without the Chrome bridge.
