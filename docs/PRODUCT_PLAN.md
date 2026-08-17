# 产品任务计划：REA HTML 解封能力闭环

## 目标

在不外包黑盒托管 API 的前提下，沉淀可复用的自研 acquisition 资产：

1. Provider Gateway（统一 `fetch(url) -> FetchResult`）
2. Kasada/Argonaut 分类与合同测试
3. Runner 适配层（优先 `internal_mac_runner`）
4. Challenge recorder（为后续 token 研究留样本）

## 阶段划分

### Phase 0 — 冻结边界（本 PR）

- 冻结 parser 路径（ArgonautExchange）
- 定义 `FetchResult` / `HtmlProvider`
- `classify_html` + 单元测试
- REA target profile
- fail-closed 规则

### Phase 1 — Gateway MVP（本 PR）

- FastAPI `/v1/fetch-html`
- Provider 注册与优先级
- Mock provider（测试）+ Remote runner client（生产适配）
- `scripts/test_html_provider.py`
- `scripts/kasada_probe_rea.py` / recorder
- Actor 侧适配模块（可复制进 Apify Actor）

### Phase 2 — Mac runner 生产化（后续）

- 真实 Mac Chrome + Patchright
- Redis 队列、profile 池、quarantine
- Apify canary `maxItems=2`

### Phase 3 — Token 研究（后续）

- 基于 Hyper 做可观测验证
- 仅 recorder/probe，通过合同测试前不进生产

## Provider 优先级

```text
1. internal_mac_runner
2. internal_windows_runner
3. internal_token_flow_probe（合同测试通过后）
4. internal_linux_browser_pool（低防目标）
5. external_*（备用，非主线）
6. fail closed
```

**禁止**：Apify Linux/Xvfb 作为 REA 默认 fallback。

## 合同测试（TC）

| ID | 类型 | 要求 |
|---|---|---|
| TC-REA-SALE-SRP | sale Melbourne | bytes>100KB, hasArgonaut, listingCount>=1 |
| TC-REA-RENT-SRP | rent Melbourne | bytes>100KB, hasArgonaut, listingCount>=1 |
| TC-REA-SALE-LDP | sale detail | bytes>30KB, hasArgonaut, detail.id |
| TC-REA-RENT-LDP | rent detail | bytes>30KB, hasArgonaut, detail.id |

## 本环境交付边界

Cloud Agent 无 Mac GUI，故本 PR 以 **协议 + 服务 + 测试夹具 + 现场壳页记录** 完成软件闭环；硬件 canary 列为 Phase 2 入口条件。
