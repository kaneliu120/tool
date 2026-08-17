# {Platform} 页面结构、字段体系与反爬限制调研报告

**调研日期：** {YYYY-MM-DD}（{时区}）  
**调研方式：** 用户本机 Google Chrome 真实会话 + AppleScript JS bridge；标准探针 `generic_page_probe.js`；三 UA HTTP 对照；可选 sitemap/Map 仅作 URL 发现（仅侧证）  
**覆盖页面（本体表，缺则写「本站无」）：**  
1. Home  
2. Search / SERP  
3. Taxonomy / Category（如有）  
4. Detail / LDP（活链派生）  
5. 子路由 / overlay / 闸门页（如出现）  
**市场：** {host / locale — 未打开的市场标未验证}  
**实测样本：** {keyword / region — 正文已脱敏}  
**对照代码：** {worker 路径，如有}

---

## 一、结论

### 已确认

1. …

### 仅侧证

1. …

### 未确认

1. …

---

## 二、实测验证记录

| 页面 | 最终 URL | 标题/H1 | bodyLen | Chrome 结果 | 闸门 |
|---|---|---|---:|---|---|
| Home | … | … | … | 正常 / 异常 | guest / soft-gate / hard-block |
| Search | … | … | … | … | … |
| Category | … | … | … | … | … |
| Detail | … | … | … | … | … |
| Verify/pause（如出现） | … | … | … | **第一类表面** | … |

Chrome：{window 数}，版本 `{version}`。探针串行；禁止并行标签。

---

## 三、表面本体映射

| 本体代号 | 本站对应 | 打开? | 说明 |
|---|---|---|---|
| Home | … | | |
| Search / SERP | … | | |
| Taxonomy / Category | … | | |
| Collection / Shelf | … | | |
| Entity list | … | | |
| Detail / LDP | … | | 活链派生 |
| Sub-route / overlay | … | | |
| Map / geo | … | | |
| Pager | … | | |
| Auth / verify / pause | … | | |
| Locale / market | … | | |

本站必须额外建模的独特面：

1. …

垂直对照（可选；不要把房产/招聘硬套过来）：见 `packs/`。

---

## 四、{Search 表面名}

按 [engineering-contract.md](../references/engineering-contract.md) 填：URL 模板、渲染家族、主数据层、兄弟 key、就绪/否定信号、字段组、分页、内部通道、闸门、HTTP 对照。

**选择器策略：** `data-test*` / JSON-LD / aria 优先；CSS hash 仅证据。

**字段组（勾选后填 key）**

| 组 | 有/空/锁 | keys |
|---|---|---|
| Identity | | |
| Economics | | |
| Pagination keys | | |
| Auth depth | | |

---

## 五、{Category / Collection …}

同契约。必须写清与 Search **是否同一通道、同一闸门**。

---

## 六、{Detail / overlay}

同契约。子路由单独一节。JSON-LD 是否仅为 SEO 地板。

---

## 七、反爬与访问限制

### 7.1 非浏览器 HTTP（按 URL 类分列）

| URL 类 | UA 类 | 状态 | bytes | listing-like / 水合 key | 备注 |
|---|---|---|---:|---|---|
| Search | python-requests-like | | | | |
| Search | curl | | | | |
| Search | Chrome UA | | | | |
| Detail | … | | | | |

### 7.2 浏览器内

Cookie **名**、脚本关键字、challenge iframe 有无、软登录文案。无 iframe ≠ 无防护。

---

## 八、数据架构总结

| 层 | 角色 | 验证状态 |
|---|---|---|
| JSON-LD | | |
| RSC / `__next_f` | | |
| `__NEXT_DATA__` / pageProps 兄弟 | | |
| 同域 BFF | 仅观察 | |
| Window globals | | |
| DOM `data-test*` | | |

---

## 九、工程决策输入（不做绕过）

1. **数据源优先级（按面）**
2. **采集通道：** 非浏览器 HTML 是否足够 / 是否必须真浏览器会话
3. **翻页：** 模式 + 哪一层在翻（HTML / XHR / JSON-LD 是否更新）
4. **多应用 / 微前端分叉**
5. **登录态 / contentDepth / 访客空洞字段**
6. **反爬症状（HTTP vs 浏览器，按面）**
7. **覆盖矩阵草稿**（国家/host × 类目 × 服务；空格=未验证）
8. **建议阶梯（本轮测量）：** 同域 JSON → TLS 伪装 HTTP → 真浏览器 → 托管浏览器（仅当已有生产证据）
9. **主键 / 去重键**
10. **水合就绪信号 + 否定信号**
11. **市场/host 行为分叉**
12. **Worker 已实现面 vs 本轮更冷面**（产品选项，不是过墙）

（不写 robots.txt / Terms / 合规边界。）

### 给 worker 的一页纸

- 覆盖矩阵：已打开 / 未打开
- 每面：主通道、就绪信号、闸门、主键
- 建议阶梯（已测量）
- 禁止事项：…
- 随机烟测应从哪些已打开面抽（禁止 README 预填城市）

---

## 十、字段清单附录

### A. 已验证
### B. 仅形状 / fixture（非本会话）
### C. 闸门页 JSON（如有）

---

## 十一、缺口与假设

1. …

### 下一步针对性探针（可选）

1. …
