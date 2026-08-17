# REA-Kasada 方案文档：审核与交叉验证报告

**审核对象**：`REA-Kasada 拦截问题：自研解封能力调研与建设方案`（2026-07-18）  
**审核日期**：2026-07-19  
**审核环境**：Cursor Cloud Agent（Linux，无 Mac GUI / 无住宅代理）

---

## 1. 审核结论摘要

| 维度 | 结论 |
|---|---|
| 总体可信度 | **高** — 核心判断与公开资料、现场探测一致 |
| 主线建议（Mac runner + Provider Gateway） | **采纳** |
| Apify 容器伪装主线 | **不采纳**（与外部证据一致） |
| Token 流作为第一闭环 | **不采纳**（文档自身也标注为研究线） |
| 需修正/标注的点 | 见第 4 节 |

一句话：文档对「瓶颈在 acquisition 环境指纹、不在 parser」的判断成立；本仓库按 Phase 0 + Gateway MVP 落地，形成可测试闭环。

---

## 2. 交叉验证矩阵

| 文档主张 | 验证方式 | 结果 | 证据 |
|---|---|---|---|
| REA 真数据在 `window.ArgonautExchange` → `urqlClientCache` | ScrapFly 教程 + scrapfly-scrapers 公开代码 | **通过** | ScrapFly blog 与 `realestate.py` 解析路径一致 |
| 现有 parser 不应重写，应换 HTML acquisition | 同上 + 架构合理性 | **通过** | 数据源稳定；失败形态是壳页而非 JSON 结构变化 |
| 典型响应为 ~771B KPSDK 壳页 | 本环境 `curl` 探测 | **通过（量级一致）** | 实测 `HTTP 429`，body **715–716B**，含 `window.KPSDK` + `ips.js` |
| Header/token：`x-kpsdk-ct`、`KP_UIDz`、`ips.js`、`/tl` | 现场响应头 + Hyper Solutions 文档 | **通过** | 响应含 `x-kpsdk-ct`、`KP_UIDz`/`KP_UIDz-ssn`、`ips.js?KP_UIDz=` |
| Docker/Xvfb/容器指纹易被 Kasada 拦 | SeleniumBase #4211 / #4226 | **通过（方向正确）** | Maintainer 明确：Docker 留指纹；property.com.au 本地可过、GHA/Docker 难过 |
| ScrapFly ASP / JS render 路线可行 | ScrapFly 教程与 scrapers 仓库 | **通过** | 公开示例使用 `asp=True` + render |
| Hyper Solutions 的 ct/cd/`/tl` 流程可作研究参考 | Hyper docs + examples repo | **通过** | Flow1/Flow2、`x-kpsdk-cd` 单次使用描述与文档一致 |
| Camoufox 不宜作 REA 主线 | 文档自称“当前报告已证明无效” | **部分验证** | 公开资料未独立复现该结论；本仓库**不反驳**，按文档不投入主线 |
| `callanjfox/realestate-scraping` + ScrapingBee 成功案例 | GitHub 检索 | **弱验证** | 未在公开检索中稳定定位到该仓库；成本数字仅作参考 |
| 本地 macOS Chrome + AU 住宅代理可过 | 文档内部实验主张 | **本环境无法复现** | Cloud Linux 无真实桌面 Chrome；标记为「依赖既有诊断，待 Mac runner canary」 |

---

## 3. 现场探测快照（2026-07-19）

```text
URL: https://www.realestate.com.au/buy/in-melbourne,+vic/list-1
HTTP: 429
bytes: 715–716
hasKpsdk: true
hasArgonaut: false
tinyKasadaShell: true
markers: window.KPSDK, ips.js, KP_UIDz, x-kpsdk-ct
```

壳页样本已固化到 `tests/fixtures/kpsdk_shell_live.html`，用于合同测试与分类器回归。

---

## 4. 文档修正与风险标注

1. **壳页字节数**：文档写「771B 左右」；实测约 **715B**。建议表述改为「亚 KB 级 KPSDK 壳页（通常 <5KB）」。
2. **SeleniumBase #4211**：支持「容器/非本地环境更易失败」，但目标站是 `property.com.au`，不是 REA 本体；类比成立，不宜写成 REA 直接证据。
3. **ScrapingBee 成本案例**：第三方成本波动大，文档已提示；审核同意仅作 benchmark，不作主线依据。
4. **合规风险**：文档第 12 节已提及 ToS/频率；实现侧必须默认 **fail closed**、白名单域名、鉴权，禁止任意 URL 抓取入口裸奔。
5. **本仓库边界**：`kaneliu120/tool` 原先为空仓；无法在此环境部署真实 Mac Chrome runner。MVP 交付的是 **协议层 + Gateway + 分类器 + recorder + 合同测试 + runner 适配接口**；真实解封成功率需在 Mac 硬件上跑 canary。

---

## 5. 对产品路线的审核意见

| 路线 | 审核意见 |
|---|---|
| P0 自研 HTML Provider Gateway | **立即做**（本 PR 完成） |
| P0 外部真实 Mac/Windows Chrome runner | **架构与接口先做**；Mac 部署为后续硬件步骤 |
| P1 Kasada token 流 | **只做 recorder/probe 骨架**，不接生产路径 |
| P2 Apify 容器深度伪装 | **不做主线**；止损规则保留在文档 |

---

## 6. 验收门禁（闭环定义）

本迭代「任务闭环」定义为软件可交付闭环，而非硬件 canary 闭环：

- [x] 审核报告产出
- [x] `FetchResult` / `HtmlProvider` 协议落地
- [x] `classify_html` 对壳页/Argonaut 夹具正确分类
- [x] Gateway `/v1/fetch-html` 可本地启动
- [x] 4 URL 合同测试在 fixture/mock provider 下通过
- [x] `kasada_recorder` 能记录现场壳页样本
- [ ] Mac runner 真实 4 URL canary（需桌面环境，标记为下一阶段）
- [ ] Apify Actor 远程 `maxItems=2`（需 Actor 仓库与凭证，标记为下一阶段）
