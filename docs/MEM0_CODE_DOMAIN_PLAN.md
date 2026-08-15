# Mem0 代码库域优化方案（可交付执行包）

状态：方案已写，**未改现网 indexer / Atlas，未切 search_knowledge**。  
日期：2026-08-15  
作者会话：Cloud Agent `bc-6b19916e`  
读者：下一个有 `mem0-extraction-worker` 的 Hermes / Cloud 会话（按工作包认领）  
父方案：[`docs/MEM0_EVOLUTION_PLAN.md`](MEM0_EVOLUTION_PLAN.md)（WP-A/B/C/D/E 不动）  
形态来源：Code Wiki 评估（决策 `b197ed86`，评估文件 `/opt/cursor/artifacts/codewiki_google_mem0_eval.md`）——**只搬形态，不接 `codewiki.google` / DeepWiki**。

---

## 0. 给执行 Agent 的一页纸

### 目标

让 agent 问代码时拿到的是 **当前 commit 上、带行号的符号切片**，以及 **能点回这些切片的短派生卡**；而不是「约 3k 字滑窗 + 无 cite 的 LLM 综述」。

验收只认三类数字，不认「wiki 看起来更全」：

1. **符号命中**：用已知函数名检索，返回的当前行必须覆盖该符号的 `path:start-end`，而不是同文件随机窗。
2. **过期切片错误率**：改一个函数后，旧 `commit_sha` / 旧文件 hash 的 chunk 与派生卡不得再作为 `valid_to==null` 返回。
3. **cite 完整率**：每张 `wiki.derived` 卡的所有专有名词/API 名必须出现在其 `cites[].source_text` 里；无 cite 的展开 = 失败（DeepWiki PTOS 类错误）。

### 禁止

- 不要接 `codewiki.google`、DeepWiki、或任何「整仓 Gemini/Devin 综述」当导入源。
- 不要用 LangExtract / LLM 把代码写成散文再写入 `code_chunks`（现网债：`code_symbols=0`，skip≈9257；幻觉高）。
- 不要把 wiki/rag 的 `voyage-4-large` 向量写入 `code_chunks`（gotcha `a99e22e0`）。
- 不要把测试、`DESIGN.md`、风格指南、i18n README、PPT 模板当 code。
- 不要把图（Mermaid/Archify HTML）embed 进向量。图继续用 Archify **渲染**，检索仍走文+符号。
- 不要把派生 wiki 写入 `memories`；gotcha/决策仍只在 `memories`。
- 不要热更 `current`；不要在 lineage unit 仍写边时做全量重切。
- 不要一次重切全部历史仓（open-design 等一次性导入保持冻结）。
- 不要学 Code Wiki「禁止人工改 wiki」——隐性知识不进派生卡。

### 两个仓库，不要混

| 仓库 | 谁跑 | 改什么 |
|---|---|---|
| **本仓库 `kaneliu120/tool`** | Cloud Agent | 卡片 schema、夹具探针、本文件。无 Atlas 也能做 WP-K0。 |
| **`mem0-extraction-worker`**（不在本 checkout） | 有 Atlas 的会话 | tree-sitter 入库、文件 hash 作废、`search_knowledge` 过滤 `valid_to`。**必须先看第 1.3 节门闩。** |

### 先读

- 本文件全文。
- [`MEM0_EVOLUTION_PLAN.md`](MEM0_EVOLUTION_PLAN.md) 第 1、7 节（WP-D 只动 `memories`；本方案动 code / **派生** wiki）。
- 决策 `b197ed86`（Code Wiki 形态）；gotcha `a99e22e0`（wiki 禁入 code）。
- 现网债：`get 0e49bbda`（数字过期则刷新，不要沿用 19122）。

---

## 1. 现网状态（执行前必须复核）

下列来自 **2026-08-13** 交接 / 方案表，以及 **2026-08-15** 本会话 `search_knowledge domain=code`。执行时刷新；过期则改本表。

### 1.1 已落地

| 项 | 证据 |
|---|---|
| 四域分离；code 用 `voyage-code-3`（1024） | gotcha `a99e22e0`；决策 `e9d70e93` |
| MCP `search_knowledge` 能召回 code | 2026-08-15 实测：`mem0-selfhost/mcp/server.py` 等 |
| 外仓 markdown 进 rag/wiki，不进 code | 决策 `e9d70e93`；教程仓默认 0 code（如 `079329fc`） |
| `code_chunks` 原则上留给自己的产品仓 | 记忆 `9eaa8570`（外仓 GitHub 默认 rag/wiki） |

### 1.2 形态病（本方案要改的）

| 现象 | 2026-08-15 实测 / 快照 | 后果 |
|---|---|---|
| 切片是 ~2970–2999 字滑窗 | `search_knowledge` hits `chars≈2977`，`title=null`，`structured=[]` | 问函数名经常拿到半截文件，不是符号 |
| `code_symbols=0` | 2026-08-13 方案表 skip≈9257 | 没有 AST 层，无法按符号作废 |
| 无 `commit_sha` / 文件 hash 在检索结果里 | MCP 返回只有 `repo`+`path`+excerpt | 代码改了，旧窗仍像「当前」 |
| wiki 域把 README/i18n/PPT 当架构 | 同日 wiki 搜 architecture 命中 open-design PPT 与三份 i18n README | 不是派生 wiki，是 markdown 再切一刀 |
| 产品仓与一次性导入混在同一检索 | 同查询打到 `mem0-selfhost` 和 `jobseek` | 没有 tracked vs frozen |

WP-D 原文「不对 wiki/code/rag 做 supersede」：**对外仓一次性导入仍然成立**。对本方案的 **tracked 仓派生卡** 不成立（决策 `b197ed86`）。

### 1.3 门闩

| 条件 | 允许 | 禁止 |
|---|---|---|
| 仅有 MCP、无 Atlas | WP-K0 | 任何写 `code_chunks` |
| lineage remaining>0 或 lineage unit active | WP-K0；可选 **影子集合** 试点 | 全量重切、改 `search_knowledge` 默认、动 `current` |
| lineage 已停 | WP-K1 起，仍先影子/单仓 | 与 W3 / WP-D 同一 PR |
| WP-D 进行中 | 本方案可并行（不同集合） | 不要改 WP-D 的 `memories` 槽模型 |

---

## 2. 目标形态（从 Code Wiki 拆出来的，可实现）

两层投影，**代码文件是唯一真源**。

### 2.1 L1 — `code_chunks`（`voyage-code-3`）

只存源码原文，禁止 LLM 改写。

```
kind: code.symbol | code.file_slice
repo: "mem0-selfhost"
path: "mcp/server.py"
commit_sha: "<40 hex>"
start: 120
end: 186
sha256: "<file hash>"
symbol_name: "handoff"          # file_slice 可空
symbol_kind: function | class | method | module
language: py
text: <精确源码，含该 span>
valid_from: ISO-8601
valid_to: null | ISO-8601
superseded_by: chunk_id | null
embed_model: voyage-code-3
```

`code.symbol`：tree-sitter / 语言 AST 切出的函数、类、方法（优先）。  
`code.file_slice`：无法解析的语言或超大生成文件的保底窗，必须仍带 `commit_sha`+`sha256`+行号。  
测试路径、`node_modules`、venv、锁文件：不入库（已有「测试不进 code」）。

### 2.2 L2 — `wiki_articles` 中的派生卡（`voyage-4-large`）

短说明，不是第二真源。

```
kind: wiki.derived
layer: overview | module | flow
repo + commit_sha
cites: [{path, start, end, sha256, source_text}]
text: ≤800 字。每个 API/类型/文件名必须出现在某一 cite.source_text
valid_to: 任一 cite 的文件 sha256 变化则为 now
embed_model: voyage-4-large
```

生成器可以是小模型，但 **入库闸门是机械的**：cite 对不上就拒绝写入（SKILLGUARD 同款：违约不是「看起来像」）。

`layer`：

- `overview`：本仓怎么拆目录，cite 到 README 入口 + 顶层包（仍要原文）。
- `module`：一个目录/服务做什么，cite 到该模块公开符号。
- `flow`：一条请求路径（如 MCP `handoff` → sidecar），cite 到实际函数 span。

### 2.3 明确不存

| 内容 | 去哪 |
|---|---|
| 运行事实、gotcha、决策 | `memories` |
| 技能/SOP/方法论 | `rag_docs` |
| 架构图二进制 | 不进向量；需要时 Archify 现画 |
| LLM 无 cite 综述 | 丢弃 |

### 2.4 作废规则（读路径不跑 LLM）

对 **tracked** 仓，每次 ingest 某 `path`：

1. 算文件 `sha256`。与当前 `valid_to==null` 且同 `repo+path` 的 L1 比较。
2. hash 相同 → NOOP。
3. hash 不同 → 旧 L1 `valid_to=now`；插入新符号切片；所有 cite 了该 path 的 L2 `valid_to=now`，再按闸门重生成（或留空直到生成成功）。
4. 默认 `search_knowledge`：`valid_to==null`。历史用显式 `as_of=commit`。

**不要**用 embedding 相似度决定谁过期。

---

## 3. 工作包与时机

```
现在就能做（本仓库，不碰 Atlas）
  WP-K0  卡片 schema + 夹具探针（tree-sitter 本地，断言 cite）

lineage 仍在写：最多影子集合 / 单仓试点，禁止切默认检索
  WP-K1  单仓 L1 符号切片入库（试点：mem0-selfhost）
  WP-K2  同仓 L2 派生卡 + cite 闸门

L1/L2 在影子检索上探针变绿之后
  WP-K3  文件 hash 作废接到 ingest
  WP-K4  search_knowledge 默认 valid_to==null；滑窗降权
  WP-K5  tracked 仓名单；历史一次性导入冻结
```

与父方案并行：WP-K0 ∥ WP-A/B/C。WP-K1+ 与 WP-D **可以**同时（不同集合），**不可以**和 lineage 全量写边抢同一 indexer 进程。

---

## 4. WP-K0 — schema 与夹具探针（先测量）

**仓库：** `kaneliu120/tool`  
**会话：** Cloud Agent，无 Atlas  
**时机：** 立即  
**依赖：** 无

### 4.1 做什么

1. 把第 2 节 schema 落成 `docs/schemas/code_l1_chunk.json` 与 `docs/schemas/wiki_derived_card.json`（JSON Schema，可校验）。
2. 夹具：本仓库放一个 ≤3 文件的假包 `fixtures/code-domain-mini/`（两个 `.py` 函数 + 一次改写的第二版）。
3. 脚本 `scripts/probes/code_domain_probe.py`：
   - 用 tree-sitter（或 Python `ast` 作为 py-only 保底）切 L1；
   - 用固定模板生成 1 张 L2（**允许**模板/小模型，但必须过 cite 闸门）；
   - 故意写一张无 cite 的「PTOS 扩写」卡，断言被拒绝；
   - 切换到夹具第二版后，断言旧 span `valid_to` 非空、新 span 当前。

不写 Mongo。输出 JSON 到 `/opt/cursor/artifacts/code_domain_probe.json` 或 `docs/probe-results/`。

### 4.2 验收

- 夹具函数改名后：旧 `symbol_name` 不得出现在 current 集。
- 无 cite 卡拒绝率 = 100%。
- 脚本第二次跑可重复（纯本地）。

### 4.3 回滚

删夹具与脚本。零服务影响。

---

## 5. WP-K1 — 单仓 L1 符号切片

**仓库：** `mem0-extraction-worker`  
**时机：** 优先等 lineage 停；若必须并行，写入 **影子集合**（例如 `code_chunks_v2`），禁止改现网默认索引  
**试点仓：** `mem0-selfhost`（本会话检索已证明在 code 域；体积小于 open-design）  
**依赖：** WP-K0 闸门脚本可跑

### 5.1 做什么

- ingest 该仓 `HEAD`：tree-sitter 切 `code.symbol`，`voyage-code-3`，字段按 2.1。
- 不删除现有滑窗行；用 `kind` / 集合名区分。
- 跳过测试、生成物、锁文件。
- 不跑 LangExtract。

### 5.2 验收

- `code_symbols`（或等价计数）对试点仓 > 0。
- 用 MCP（或影子查询）搜 `handoff`：命中 `mcp/` 下带 `symbol_name` 的行，且 `start/end` 覆盖定义。
- `embed_model` 仍是 `voyage-code-3`。

### 5.3 回滚

丢影子集合。现网滑窗检索不变。

---

## 6. WP-K2 — 同仓 L2 派生卡

**仓库：** `mem0-extraction-worker` + 生成器（可另仓，但写入走同一闸门）  
**时机：** WP-K1 试点仓 L1 已有  
**依赖：** WP-K0 的 cite 拒绝逻辑必须复用，禁止「生成后再人工看一眼」

### 6.1 做什么

- 为试点仓生成 `overview` 1 张 + 每个顶层模块 1 张 `module` + 1–3 张 `flow`（例如 MCP handoff、search、search_knowledge）。
- 写入 `wiki_articles` 时带 `kind=wiki.derived`；或先影子 wiki 集合。
- 生成失败（cite 不足）→ 该层缺卡，**禁止**用无 cite 散文顶上。

### 6.2 验收

- 抽 10 个卡内专有名词，10/10 能在 `cites.source_text` 找到。
- `search_knowledge domain=wiki` 对「MCP handoff」能返回 `kind=wiki.derived`，且卡上有 `mcp/server.py` 的 span。
- 不得把这些卡的向量写入 `code_chunks`。

### 6.3 回滚

按 `kind=wiki.derived` + `repo=mem0-selfhost` 删除。

---

## 7. WP-K3 — 文件 hash 作废

**时机：** 影子上 K1+K2 探针绿  
**做什么：** ingest 流水线在写 L1 前执行 2.4。L2 只重生成 **cite 了变更 path** 的卡，禁止整仓 Gemini 重写。  
**验收：** 试点仓改一个函数、再 ingest：旧 L1/L2 不再出现在默认检索；新符号可检索。记录前后各 1 次查询 JSON。  
**回滚：** 开关 `CODE_INVALIDATE=0` 回到只追加滑窗。

---

## 8. WP-K4 — 读路径切默认

**时机：** K3 在试点仓连续两次 ingest 正确  
**做什么：** `search_knowledge domain=code` 默认 `valid_to==null` 且优先 `kind=code.symbol`；滑窗 `kind` 缺失的历史行降权或仅 `include_legacy_windows=true`。  
**验收：** 同一查询「handoff」：符号行排在滑窗前；分数阈值仍按现网 code 索引（刷新，不要抄旧 YAML）。  
**禁止：** 本步删除历史滑窗。先降权，WP-K5 再决定冻/删。

---

## 9. WP-K5 — tracked 名单与冻结

**tracked（持续 ingest + 作废）：** 先白名单，Kane 确认后再加。

建议首批（执行时再核对 Atlas 里实际 `repo` 字段）：

- `mem0-selfhost`
- `mem0-extraction-worker`
- `kaneliu120/tool`（若已作为产品仓进 code；否则本仓 skill 仍走 rag）

**frozen（一次性导入，不作废、不重切）：** `open-design` 及类似外仓代码快照。检索可加 `repo=` 过滤，避免和 tracked 混排。

**默认不进 code：** 教程/课仓、换肤客户端、venv 提交仓（已有决策 `079329fc`、`efe1d8ae`）。

本步才允许讨论「是否删滑窗」。未白名单确认，禁止 `drop`。

---

## 10. 会话拆分（直接复制给新 Agent）

### 会话 K0 — `tool` / Cloud

```
你在 kaneliu120/tool。只做 docs/MEM0_CODE_DOMAIN_PLAN.md 的 WP-K0。
不要连 Atlas，不要接 codewiki.google / DeepWiki，不要 LangExtract。
交付：docs/schemas/code_l1_chunk.json、wiki_derived_card.json、
fixtures/code-domain-mini/、scripts/probes/code_domain_probe.py、探针 JSON。
验收：无 cite 卡 100% 拒绝；夹具改函数后旧 span 不在 current。
完成后 commit/push/PR；Mem0 handoff project=tool。
```

### 会话 K1 — `mem0-extraction-worker` / 有 Atlas

```
先 get 0e49bbda，刷新 lineage remaining。若 remaining>0：只允许影子集合，禁止改 search_knowledge 默认。
试点仓仅 mem0-selfhost。按 MEM0_CODE_DOMAIN_PLAN.md WP-K1→K2。
禁止：voyage-4-large 写入 code_chunks；热更 current；与 W3/WP-D 同一 PR；全量重切 open-design。
验收：符号命中 handoff；派生卡 10/10 cite 完整。
handoff project=mem0-extraction-worker。
```

### 会话 K2 — 作废与切读路径

```
仅当 K1 影子探针绿。做 WP-K3 然后 WP-K4。
作废只按文件 sha256，不用向量相似度。
滑窗先降权不删除。WP-K5 白名单需 Kane 确认后再冻/删。
```

---

## 11. 完成定义（本域）

全部完成当且仅当：

1. WP-K0 探针绿并写入交接。
2. 至少一个 tracked 仓 L1 符号切片可经 MCP 查到，且改文件后旧切片默认不可见。
3. 该仓 L2 派生卡 cite 完整率抽检 10/10。
4. `search_knowledge` 默认不把 `valid_to!=null` 当当前代码。
5. 现网滑窗与一次性导入未被擅自 drop；lineage / `current` / WP-D 未被插队。

未满足以上任一条，禁止写「已闭环」或「已上线」。

---

## 12. 索引

| 用途 | 指针 |
|---|---|
| 父方案（事实/skill） | `docs/MEM0_EVOLUTION_PLAN.md` |
| 形态决策 | memory `b197ed86` |
| wiki 禁入 code | gotcha `a99e22e0` |
| 现网债 | memory `0e49bbda` |
| Code Wiki 评估 | `/opt/cursor/artifacts/codewiki_google_mem0_eval.md` |
| 不要做 | 接 Google 产品；LangExtract 抽代码；图进向量；整仓无 cite 综述 |
