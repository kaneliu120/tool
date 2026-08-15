# Mem0 进化方案（可交付执行包）

状态：方案已写，**未改现网 Mem0 代码，未跑生产探针**。  
日期：2026-08-15  
作者会话：Cloud Agent `bc-6b19916e`  
读者：下一个 Cloud / Hermes / Cursor 会话（按工作包认领，不要一人做完全部）

---

## 0. 给执行 Agent 的一页纸

### 目标

让 agent 在任务中拿到的是 **当前仍然有效的事实** 和 **对当前环境可执行的程序草稿**，而不是「语义相似的旧记忆 + 整篇 SKILL.md」。

验收只认两类数字，不认「感觉更好」：

1. **陈旧事实错误率**（写入 X=A 再写入 X=B，问现在 X 是什么，答 A 或 A+B 算失败）。
2. **Skill 诱导回归率**（同一任务：无 skill 成功、加载错环境 skill 后失败 的比例）。

### 禁止

- 不要抄 Alloomi 的 LoRA / Engram / 教师蒸馏飞轮。那不是当前瓶颈。
- 不要热更 `current` 符号链接（mem0-extraction-worker 现网约定）。
- 不要 drop `agent_memories`，除非确认无读者。
- 不要把 Voyage `grounded_in` 边当出处。出处只认 sidecar `grounding.source_text==slice`。
- 不要在 lineage unit 仍 active 时 apply W3 `similar_to`。
- 不要恢复 Mac automation / `osascript`。
- 不要把一次失败总结成「永远这样跑」的整篇 wiki skill。
- 不要用官方 `mem0ai` 客户端打自托管栈；不要用 stdlib `urllib` 打 `mem0-mcp.opendata.best`。

### 两个仓库，不要混

| 仓库 | 谁跑 | 改什么 |
|---|---|---|
| **本仓库 `kaneliu120/tool`** | Cloud Agent / 任何克隆了 skills 的会话 | Skill 契约、加载器、探针脚本、AGENTS.md。**无 Atlas 写权限也能做阶段 0–2 的 skill 侧。** |
| **`mem0-extraction-worker`**（Kane VPS / Atlas，不在本 checkout） | Hermes / 有 Atlas 的会话 | 写路径 supersede、索引、W3、`rag_extract_skip` 进 current。**必须先看第 2 节门闩。** |

### 先读

- 本文件全文。
- Mem0 交接：`get 0e49bbda-feef-4acc-9fd8-1b5f1238be4d`（现网债，2026-08-13）。
- 方向交接：`get 0be2145d-0325-45fa-80b3-3894fe063451`（不要抄 Alloomi）。
- 论文地图：`/opt/cursor/artifacts/mem0_improve_paper_map.log`（若本机没有，用本文件第 8 节）。

---

## 1. 现网状态（执行前必须复核）

下列数字来自 **2026-08-13 11:09 UTC** 交接，以及 **2026-08-15** 本 Cloud 会话对 MCP 的实测。执行会话开始时用第 1.3 节命令刷新；**过期则改本表，不要沿用。**

### 1.1 已落地

| 项 | 证据 |
|---|---|
| 四域：`memories`（真源）/ `code_chunks` / `wiki_articles` / `rag_docs` | Kane 口述 + MCP `search` / `search_knowledge` |
| `mem0_unified.memories` 为会话记忆真源；`agent_memories` 已 `$out` 归档（约 19655），保留集合 | 2026-08-11 交接 |
| Sidecar grounding（`source_text==slice`），2026-08-11 后 sync_turn 走 Luna 100% grounded | gotcha `4f8f0763` |
| 读路径 G0/W1、索引闸门 | 2026-08-13 |
| MCP `search_knowledge`（wiki/rag/code）已接到 sidecar `172.18.0.1:8892` | 2026-08-13 11:15 交接；2026-08-15 Cloud 实测可召回 |
| `agent_memories` 卸向量索引 | 2026-08-13 决策 `433e7f23` |
| 公开 MCP `https://mem0-mcp.opendata.best` health=ok | 2026-08-15 `mem0ctl health` |
| Cloud skill 包在本仓库；`use-my-browser` 已是 stub | `.cursor/skills/use-my-browser/SKILL.md` |
| wiki/rag 用 `voyage-4-large`；code 用 `voyage-code-3`；wiki 不得拷进 code | gotcha `a99e22e0` |

### 1.2 未还清的债（优化方案必须让路，不能并行打架）

| 债 | 2026-08-13 快照 | 门闩 |
|---|---|---|
| lineage 仍在写假血缘 `grounded_in`，`similar_to=0` | remaining≈19122，0.743s/claim | **W3 禁止**直到 remaining≈0 且 lineage unit 停 |
| `rag_extract_skip` 未进 `current` | `feat/memories-indexes` 有未提交文件 | **不要热更 current**；下一版 current 再吃 |
| RAG 抽了缺读者 | lx_real=1090，skipped=1747，queued=4263（更早快照） | 先接读者再加大抽取 |
| code 无 AST / `code_symbols=0` | skip≈9257 | 不走 LangExtract 抽代码（幻觉高） |
| 双平面残留 | `agent_memories` 归档仍在 | 确认无读者再卸 |
| wiki `decision=0` | 路径带 decision 的是 skill 名不是 ADR | 不要当 ADR 检索 |
| Skill 无环境契约、无适用性门 | 本仓库 skills 只有散文 stub | **本方案主攻，可与 lineage 并行**（只改本仓库） |

### 1.3 执行会话开机复核（5 分钟）

在 **有 Atlas 的会话**：

```bash
# 伪代码：用现网 unit 面板，不要猜
# 记录：lineage remaining, units active, similar_to count, current symlink target
```

在 **仅有 MCP 的 Cloud 会话**（本仓库即可）：

```bash
python3 scripts/mem0ctl.py health
# MCP search_knowledge domain=wiki 任意查询，确认非空
# MCP search「mem0-extraction-worker lineage remaining」拿最新交接
```

若 lineage 仍 active：只做 **WP-A / WP-B / WP-C**（本仓库）。禁止 WP-D（写路径 supersede 全量）、禁止 W3。

---

## 2. 问题与论文对齐（方案依据，不是要复现论文）

两个失败类，对应两套改动：

| 失败 | 现场表现 | 论文抓手 | 本方案动作 |
|---|---|---|---|
| 检索 ≠ 当前为真 | 新旧事实一起召回，agent 当证据 | MemStrata：RAG 陈旧事实 15–40%；余弦几乎分不开新旧 | 写路径 `(entity, attr)` 槽 + `valid_to` / `superseded_by` |
| Skill 套用 | 语义命中 SKILL.md 就跑；Cloud 仍走 Mac 套路 | SkillAligner：5.8–17.9% 成功变失败；SkillsBench 16/84 题负增益 | Skill 当草稿：契约检查 → Primary/Checks/Avoid/Fallback |
| 环境漂了 skill 还在 | CLI/API/OS 变了文档没变 | SKILLGUARD：drift = 契约违约，不是 URL 变了 | frontmatter `env_contracts`，失败则拒绝加载 |

**明确后置（本方案不包含实现）：** ACE 整本 playbook 重写、Memory-R1 训 Manager、Engram/LoRA、He 图。ACE 的 helpful/harmful **计数**可以在 WP-E 用短条目，不要先堆厚文档。

---

## 3. 工作包与时机

```
现在就能做（不碰 Atlas 写路径 / 不碰 current）
  WP-A  陈旧事实探针（MCP，可回滚的 probe 记忆）
  WP-B  Skill 契约 + 加载器（本仓库）
  WP-C  Skill 成对回归评测（Cloud vs Mac）

必须等 lineage remaining≈0 且 lineage unit 停
  WP-D  memories 写路径 supersede（extraction-worker）
  旧债  W3 similar_to；current 吃 rag_extract_skip

WP-D 探针变绿之后
  WP-E  经验短条目（helpful/harmful），禁止整篇 skill 自生成入库

代码库域（独立文档，不插队 memories）
  见 docs/MEM0_CODE_DOMAIN_PLAN.md
  WP-K0  本仓库夹具探针（可与 WP-A/B/C 并行）
  WP-K1+ 符号切片 / 派生 wiki / 文件 hash 作废（extraction-worker；lineage 未停只许影子集合）
```

并行规则：WP-A/B/C 与 lineage **可以**同时进行。WP-D 与 lineage **不可以**同时 apply 索引/批量写边。WP-K0 与 WP-A/B/C **可以**同时进行。WP-K1+ 与 WP-D **可以**同时（不同集合），不可与 lineage 全量写边抢同一 indexer。

---

## 4. WP-A — 陈旧事实探针（先测量）

**仓库：** `kaneliu120/tool`  
**会话：** Cloud Agent，只需 `MEM0_API_KEY`  
**时机：** 立即  
**预估：** 小改动，数小时内可出基线数字  
**依赖：** 无

### 4.1 做什么

用 MCP `add` 写入可过期的探针记忆（`run_id=stale-probe-<date>`，`expires` 24h），不要污染长期记忆。

最小协议（MemStrata 无标记演化）：

1. `ADD`：「Mesh bastion 探针槽 = VALUE_A」（`meta.kind=probe`，`meta.slot=mesh.bastion`）。
2. `ADD`：「Mesh bastion 探针槽 = VALUE_B」（同一 slot，新值）。
3. `search "Mesh bastion 探针槽"`。
4. 判分：只出现 B → pass；出现 A 或 A+B → stale-fail。

重复 20 个互不相关的 slot（假数据，不要用真密钥）。记录 stale-fail / n。

### 4.2 交付物

- `scripts/probes/stale_fact_probe.py`：写入、检索、打分、删除/过期。
- 报告写入 `/opt/cursor/artifacts/stale_fact_baseline.json`（Cloud）或本仓库 `docs/probe-results/`（不要提交密钥）。

### 4.3 验收

- 脚本可重复跑；第二次跑先清同一 `run_id`。
- 基线数字进交接。不要求第一次就变绿；WP-D 之后再跑对比。

### 4.4 回滚

`expires` + 按 `run_id` 删除 probe 记忆。禁止对真实 gotcha 做 UPDATE。

---

## 5. WP-B — Skill 契约与加载器（本仓库主战场）

**仓库：** `kaneliu120/tool`  
**会话：** Cloud Agent  
**时机：** 与 WP-A 并行  
**预估：** 中等；先改 5 个最高风险 skill，不要一次改完全库

### 5.1 问题

Agent 读到 `SKILL.md` 就当法令。Cloud 没有 Keychain / Mac Chrome / `localhost:8888`，`use-my-browser` 已有 stub，但 **没有机械门**：模型仍可能忽略 stub 去 `osascript`。其他 skill（website-page-research、reverse-skill、apify 的 Mac 路径）同样。

### 5.2 规范（所有 skill 最终都要有，分批）

在 YAML frontmatter 增加（名称固定，方便机器读）：

```yaml
when_to_apply:
  - "用户要驱动本机 Chrome / 调用我的浏览器"
when_not_to_apply:
  - "Cursor Cloud Agent"
  - "无 macOS Chrome"
env_contracts:
  - id: macos-chrome
    role: obligation
    check: "os == darwin and chrome_applescript"
    on_fail: refuse   # refuse | adapt | warn
runtime: [macos]      # macos | linux-cloud | linux-vps | any
```

`on_fail`：

- `refuse`：不加载正文，只保留「不可用 + 替代路径」三行。
- `adapt`：加载 stub 段（如现有 use-my-browser）。
- `warn`：可加载，但必须先输出 Checks。

### 5.3 加载器行为（必须写进 AGENTS.md + `mem0-mandatory` 旁的短规则）

Agent 在 Read `SKILL.md` 之后、执行步骤之前：

1. 解析 frontmatter（无契约 = 视为 `warn`，并在本轮交接记一条债）。
2. 对每个 `obligation` 契约做 **非 LLM** 检查：OS、`MEM0_REST_URL` 是否可达、是否存在 `osascript`、是否 Cloud（`CURSOR_CLOUD` / 本机 `AGENTS.md` 已写的事实）。
3. 输出一张不超过 40 行的执行卡，**之后只准按这张卡跑，不准再把全文当 SOP**：

```
Primary: ...
Checks: ...
Avoid: ...
Fallback: ...
```

这是 SkillAligner 的最小移植，不引入他们的训练。

### 5.4 第一批必须改的文件

| 文件 | 契约 |
|---|---|
| `.cursor/skills/use-my-browser/SKILL.md` | `macos-chrome` → refuse on Cloud |
| `.cursor/skills/website-page-research/SKILL.md` | AppleScript Chrome → adapt to VM/Playwright |
| `.cursor/skills/mem0-selfhost/SKILL.md` | `localhost:8888` → refuse unless tunnel; MCP OK |
| `.cursor/skills/apify-actor-cloud-run-development/SKILL.md` | `~/Projects/google run worker` 不存在 → adapt |
| `.cursor/skills/reverse-skill/SKILL.md` | 完整 pack 不在 clone → refuse 越权逆向 |

新增：`.cursor/skills/_loader.md`（给 agent 的加载协议，短）。  
新增：`.cursor/rules/skill-env-contracts.mdc`（alwaysApply，10–20 行，不要长文）。

### 5.5 验收

- Cloud 会话接到「调用我的浏览器」时，**零次** `osascript` 尝试（看 transcript / shell history）。
- 每个改过的 skill 有 `when_not_to_apply` 含 `Cursor Cloud Agent`（若确实不能跑）。
- 规则文件被 alwaysApply 加载（下一次 Cloud Agent 需 **新开** 才能吃到 git 里的新 rules）。

### 5.6 回滚

Revert 上述 md/mdc。不改 Mem0 服务。

---

## 6. WP-C — Skill 成对回归评测

**仓库：** `kaneliu120/tool`  
**时机：** WP-B 合并前必须跑一轮基线；合并后再跑对比  
**依赖：** WP-B 的契约至少打在 `use-my-browser`

### 6.1 协议（SkillsBench 成对，不是平均成功率）

同一提示、同一模型档，三种条件：

| 条件 | 操作 |
|---|---|
| S0 无 skill | 系统里临时改名/移走目标 SKILL.md |
| S1 正确 skill | Cloud 用 stub |
| S2 错环境 skill | **故意**注入 Mac 版全文（osascript 步骤） |

每条件固定 5 个任务（例：打开本机 Chrome 查 Mem0、页面调研、Mac 钥匙串读密钥、打 localhost:8888、跑 Hermes 本机脚本）。

记录：成功 / 失败 / 是否调用违禁命令。

**主指标：** S0 成功且 S2 失败 的条数 / 5 = 诱导回归率。  
**改进目标：** WP-B 后门必须把 S2 的违禁命令次数打到 0；回归率下降。S0 基线不得明显变差。

### 6.2 交付物

- `docs/probe-results/skill_regression_<date>.md`（可提交，无密钥）。
- 可选：Cloud 会话 transcript 节选。

### 6.3 不要做

不要用模型自写 skill 当 S1（SkillsBench：自写平均 −1.3pp）。S1 只用人写 stub。

---

## 7. WP-D — 写路径 supersede（extraction-worker）

**仓库：** `mem0-extraction-worker`（本 Cloud checkout **没有** 这个仓库）  
**会话：** 有 Atlas 的 Hermes / 新 Cloud（需 Kane 把该 repo 加进环境）  
**时机：** **lineage remaining≈0 且 lineage unit inactive**  
**依赖：** WP-A 基线数字已存在

### 7.1 范围

只动 **`mem0_unified.memories`**。不要对 **一次性导入** 的 `code_chunks` / `wiki` / `rag` 做 supersede（静态语料）。tracked 仓的符号切片与 `wiki.derived` 作废见 [`MEM0_CODE_DOMAIN_PLAN.md`](MEM0_CODE_DOMAIN_PLAN.md)，不要写进本 WP-D PR。

### 7.2 数据模型（最小）

对可规范化的 fact（同一实体同一属性）：

```
slot_key: "<entity_id>|<attribute>"   # 例：env.mesh|bastion_host
value: "100.96.0.3"
valid_from: ISO-8601
valid_to: null | ISO-8601             # 半开区间 [from, to)
superseded_by: memory_id | null
source: user | tool | agent_infer     # 已有 sidecar 权威
grounding: {start,end,source_text}    # 已有，禁止删
```

写入规则（MemStrata，**读路径不跑 LLM 裁判**）：

1. 规范化出 `slot_key`。规范化失败 → 普通 ADD（现状），不要猜。
2. 若存在 `valid_to==null` 的同 key：
   - 值相同 → NOOP / 加强（不新增向量行）。
   - 值不同 → 旧行 `valid_to=now`，`superseded_by=新id`，新行 `valid_from=now`。
3. 默认检索：`valid_to==null`（当前为真）。需要历史时显式 `as_of`。

权威冲突（用户 vs agent_infer）：用户赢；同权威则标 `disputed` 不自动覆盖（MemTX 的精简版）。

### 7.3 实现落点（执行会话自己对照代码，以下为意图）

- Sidecar / `sync_turn` 抽取后、写 Mongo 前：跑 slot 规范化 + supersede。
- MCP `search`：默认过滤当前有效。需要加参数 `include_superseded=false`（默认 false）。
- **不要**用 embedding 相似度决定谁过期。

### 7.4 验收

- 重跑 WP-A 探针：stale-fail 相对基线显著下降（目标：接近 0，允许规范化失败的 slot 仍走旧路径）。
- 静态检索（未取代的 gotcha）召回分数不掉档（voyage-4-large 阈值仍按 search.yaml）。
- 不热更 `current`；跟 worker 版本走下一版 current。

### 7.5 回滚

功能开关 `SUPERSEDE_WRITE=0` 回到只 ADD。旧行 `valid_to` 可批量清空（保留备份）。

### 7.6 与旧债的排队

```
lineage 停
  → 可选：W3 similar_to（仍不要把 grounded_in 当出处）
  → 下一版 current：rag_extract_skip
  → WP-D supersede（可与 rag_extract_skip 同版本，但分 PR）
```

WP-D 不要和 W3 同一 PR。

---

## 8. WP-E — 经验短条目（后置）

**时机：** WP-B 门已上，且 WP-A 在 WP-D 后变绿  
**做什么：** 失败/成功写成 **短** `kind=experience` 条目：`when` / `what_worked` / `what_failed` / `env` / `helpful` / `harmful`。  
**不要：** 模型一次性生成整份 SKILL.md 入库（SkillsBench 负增益）。  
**修订：** 仅在有可重复 verifier（探针脚本退出码）时改 skill 正文（SkillRevise 的约束）。

---

## 9. 会话拆分（直接复制给新 Agent）

### 会话 1 — `tool` 仓库 / Cloud

```
你在 kaneliu120/tool。只做 docs/MEM0_EVOLUTION_PLAN.md 的 WP-A、WP-B、WP-C。
不要改 Mem0 服务，不要连 Atlas，不要热更 current。
WP-A：scripts/probes/stale_fact_probe.py，记忆必须 kind=probe 且 expires≤24h。
WP-B：skill frontmatter 契约 + _loader.md + skill-env-contracts.mdc；第一批 5 个 skill。
WP-C：5 个任务 × {无skill, stub, 故意Mac全文}，主指标是错环境违禁命令次数=0。
完成后：commit/push/PR；Mem0 handoff project=tool。
```

### 会话 2 — `mem0-extraction-worker` / 有 Atlas

```
先 get 0e49bbda；复核 lineage remaining。若 remaining>0 或 lineage unit active：停止 WP-D，只报告数字。
若已停：按 MEM0_EVOLUTION_PLAN.md WP-D 做 memories 写路径 supersede。
禁止：drop agent_memories；把 grounded_in 当出处；与 W3 同一 PR；热更 current。
验收：复跑会话 1 的 stale_fact_probe（或同等 20 slot）。
handoff project=mem0-extraction-worker。
```

### 会话 3 — 旧债（不要和 1/2 抢）

```
仅当 lineage remaining≈0：W3 similar_to。
下一版 current 才吃 rag_extract_skip。
code_symbols 走 tree-sitter，不要 LangExtract。完整排期见 docs/MEM0_CODE_DOMAIN_PLAN.md（WP-K0 在 tool 仓即可开工）。
```

### 会话 4 — 代码库域（不要和会话 2 的 WP-D 抢同一 PR）

```
先读 docs/MEM0_CODE_DOMAIN_PLAN.md。
无 Atlas：只做 WP-K0。
有 Atlas：lineage 未停则影子集合 + 仅 mem0-selfhost；禁止接 codewiki.google；禁止 LangExtract；禁止 drop 历史滑窗。
handoff project=mem0-extraction-worker 或 tool（看改了哪个仓）。
```

---

## 10. 论文与交接索引

| 用途 | 指针 |
|---|---|
| 陈旧事实 | arXiv:2606.26511 MemStrata |
| Skill 当草稿 | arXiv:2608.06880 SkillAligner |
| 成对评测 | arXiv:2602.12670 SkillsBench |
| 环境契约 | arXiv:2605.10990 SKILLGUARD |
| 适用性维度 | arXiv:2608.06891 SkillEval |
| 不要先做 | Alloomi SEA；ACE 整本重写；Memory-R1 训练 |
| 现网债 | memory `0e49bbda` |
| 方向 | memory `0be2145d`；gotcha `6434e754` |
| 代码库域形态 | `docs/MEM0_CODE_DOMAIN_PLAN.md`；决策 `b197ed86`；gotcha `a99e22e0` |

---

## 11. 完成定义（整案）

全部完成当且仅当：

1. WP-A 基线已记录，且 WP-D 后 stale-fail 下降并写入交接。
2. 第一批 5 个 skill 有契约；Cloud 上 S2 违禁命令为 0。
3. `search` 默认不返回已 `valid_to` 的事实（WP-D 后）。
4. 现网债仍按原门闩推进，没有被本方案插队搞坏 lineage / current。

未满足以上任一条，禁止在交接里写「已闭环」或「已上线」。
