---
name: reverse-skill
description: >-
  Routes authorized reverse-engineering / security analysis via Kane's local
  reverse-skill pack (JS signatures, captchaBody/encrypt, DSL VM, protocol/PCAP,
  browser CDP, binary/APK). Use when the user mentions reverse-skill, 逆向,
  js-reverse, captchaBody, oec-captcha, 前端签名, 协议逆向, Frida, jadx, IDA,
  Ghidra, radare2, DSL VM, or when assembling unlock/crypto from live SDK traffic.
---

# reverse-skill（本地路由入口）

轻量 **Skill Router**：不把整仓方法论塞进上下文。先定 PRIMARY，再打开仓库里对应
`SKILL.md` 执行。源仓（只读权威）：

```text
/Users/kane/Projects/reverse-skill
```

**Cloud Agent：** 这台 Ubuntu VM **没有** 上述源仓，也没有 Frida/IDA/jadx。本文件只是路由+约束。未把源仓 checkout 进本环境前，不要假装能执行 PRIMARY `SKILL.md`；向 Kane 要 `repositoryDependencies` 或改在 Mac 上跑。

本包是 **路由 + Kane 约束**，不是分析引擎，也不是 Z3r0 式平台。

## ACTION REQUIRED（读完立刻做）

1. `NOW`：Mem0 `search`（`~/.cursor/skills/mem0-selfhost`）同类坑点/handoff  
2. `NOW`：用下方快路由或读 [routing-quick.md](routing-quick.md) → 输出 **PRIMARY 路径 + 一句话依据**  
3. `NOW`：`Read` 源仓 PRIMARY 的 `SKILL.md`，按其 ACTION / 工作流执行  
4. `NEXT`：需要本机工具路径时再读源仓 `skills/tool-index.md`（**禁止猜路径**）  
5. `ACT`：仅在授权/scope 明确后对目标动手；结论走 Evidence→Finding→Path  
6. 结束：业务项目用 Mem0 `handoff`（勿写 field-journal / 勿开 journal PR）

疑难全表：源仓 `skills/MASTER-ROUTING.md`、`skills/routing.md`。

## Kane 硬约束（覆盖源仓 README_AI / 部分 RULES）

| MUST / MUST NOT | 说明 |
|-----------------|------|
| MUST | 任务前 Mem0 search；非琐碎任务后 handoff |
| MUST | 先路由再动手；未授权不对真实目标 ACT |
| MUST NOT | 在生产机自动 `sudo` / Kali `quick-setup` / 盲跑 bootstrap |
| MUST NOT | 「跳过确认直接打」「全局注入危险 RULES」类强制句 — 本地已删，勿恢复 |
| MUST NOT | 把密钥、cookie、完整凭证写入 Mem0/git |
| SHOULD | macOS 优先 `skills/scripts/bootstrap-reverse.sh --list` / `refresh-tool-index.sh`，少用 PS1 |
| SHOULD | Scraping / Shop·Temu 墙：与 `bright-data-riskbypass`、`use-my-browser`、worker PoC **解耦**；逆向只负责算法/加密还原，不声称已上线解锁 |

## 快路由（Kane 高频）

| 信号 | PRIMARY（相对源仓 `skills/`） |
|------|------------------------------|
| 前端签名 / XHR 加密参数 / CDP Hook / jshook | `js-reverse/` |
| `captchaBody` / SDK 加密 blob / verifyV2 / oec-captcha | `js-reverse/` → 必要时 `reverse-engineering/dsl-vm-reverse/` |
| 自定义 opcode VM / fireye 式 IIFE+switch | `reverse-engineering/dsl-vm-reverse/` |
| Protobuf / gRPC / PCAP / 二进制帧 | `protocol-reverse/` |
| Playwright 观察 / 桌面自动化 | `browser-automation/`（真 Chrome 调研优先 `use-my-browser` / `website-page-research`） |
| APK / jadx / Frida Android | `apk-reverse/` 或 `mobile-reverse/` |
| IDA / Ghidra / r2 / 未知二进制 | `ida-reverse/` / `ghidra-reverse/` / `radare2/` / `reverse-engineering/` |
| 跨模块不清楚 | 源仓 `skills/SKILL.md` + `MASTER-ROUTING.md` |

完整表见 [routing-quick.md](routing-quick.md)。

## 推荐执行链（前端 / 验证码加密）

贴合当前 Shop/Temu 组装路径：

```text
Observe（网络：get/verify URL、body 形态）
  → Capture（运行时：加密前明文 / 密钥材料 / 调用栈）
  → Rebuild（Node 最小复现；禁止空想补 window）
  → 验收：本地算出与线上一致的 captchaBody 或明文 reply
  → 业务侧再接施力/会话（不在本 skill 宣称过墙）
```

已验证事实可先 Mem0 search：`api-verification.tiktokshop.com`、`captchaBody`、Gisnsl edata 不适用等。

## 工具与 MCP

- 源仓工具索引：`/Users/kane/Projects/reverse-skill/skills/tool-index.md`（gitignore 本地生成；缺则跑 `skills/scripts/refresh-tool-index.sh`）  
- 缺工具：`bash /Users/kane/Projects/reverse-skill/skills/scripts/bootstrap-reverse.sh --list` 后**按需**安装，勿全量自举  
- JS MCP：源仓 `js-reverse` 文档；无 MCP 时用 Patchright/CDP/`use-my-browser` 降级取证  
- Mem0：始终走 `~/.cursor/skills/mem0-selfhost`（源仓已无 `skills/mem0-memory/`；以本地 mem0-selfhost skill 为准）

## case / 证据（可选）

需要正式 scope 时在源仓下建 case（PowerShell 脚本；无 PS 可手写等价文件）：

```text
/Users/kane/Projects/reverse-skill/work/<case>/scope.md
```

契约：源仓 `skills/ops/scope-contract.md`、`ops/evidence-finding-path.md`。  
`auth` 未 granted → **禁止**对目标 ACT。

## 阶段结束：下一步菜单

每个分析阶段结束后给用户 **3–6 个编号选项**（含「导出报告」与「暂停」），不要无确认跨阶段狂奔。

## 相关本地 skill

| Skill | 何时并用 |
|-------|----------|
| `mem0-selfhost` | 记忆 search/handoff |
| `use-my-browser` / `website-page-research` | 真 Chrome 页面调研（非红队） |
| `bright-data-riskbypass` | 解锁/代理引擎（与逆向还原分开） |
| `apify-actor-cloud-run-development` | 还原结果接入 worker/Actor 时 |

## 源仓读序

```text
本 SKILL.md
  → routing-quick.md 或 源仓 MASTER-ROUTING.md
  → 源仓 skills/<PRIMARY>/SKILL.md
  → （按需）references/、tool-index、ops/
  → Mem0 handoff
```
