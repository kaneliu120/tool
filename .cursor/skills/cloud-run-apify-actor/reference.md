# Cloud Run + Apify Actor 开发标准

> 版本：2026-07-23  
> 目的：按同一模式开发「Cloud Run 采集 worker + Apify 薄 Actor」  
> Skill：`~/.cursor/skills/cloud-run-apify-actor/`  
> 引擎评估：[engines.md](engines.md)

---

## 1. 架构总览

### 1.1 分工

| 层 | 职责 | 不负责 |
| --- | --- | --- |
| **Cloud Run Worker** | 采集引擎、proxy、解析、过滤、分页、详情、failover、OpenAPI、**对 scrape API 鉴权** | Apify Dataset、Store SEO、PPE |
| **Apify Actor** | Input、**HTTPS + API key** 调 worker、`push_data`、KV、README/SEO、PPE、Standby Live View；创建 RESIDENTIAL → `proxyUrl` | Worker 已存在时在 Actor 内跑浏览器采集 |

```
┌─────────────────────┐   HTTPS + API key    ┌──────────────────────────┐
│  Apify Actor (thin) │ ───────────────────► │  Cloud Run Worker        │
│  OpenAPI 客户端联调  │                      │  OpenAPI 服务端          │
│  dataset + PPE      │ ◄─────────────────── │  /v1/search|/listings    │
└─────────────────────┘        items[]       │  scrape engine + parse   │
                                             └──────────────────────────┘
```

### 1.2 目录约定

| 类型 | 推荐路径 |
| --- | --- |
| Worker | `/Users/kane/Projects/google run worker/<worker-name>/` |
| Actor | `/Users/kane/Projects/Apify Actors/<actor-name>/` |
| Skill | `~/.cursor/skills/cloud-run-apify-actor/` |
| 可读副本 | `Apify Actors/docs/` 与 `google run worker/docs/` |

参考实现：Worker `zillow-com` + Actor `zillow-scraper`。  
GCP 项目：`woker-260722`（以现状为准）。  
**Cloud Run `--region`：按采集网站所属地区选择**（见 §3.4），禁止所有 worker 无脑部署到同一区域。

---

## 1A. 采集引擎策略（强制顺序）

详见 [engines.md](engines.md)。

1. **先评估**：按 worker 需求，用历史 Actor（A）、GitHub（B）、公开/X 调研（C）分析引擎与效率。  
2. **再默认继承**源 Actor 的引擎与功能面（warm-up、分页、通道、enrich、代理模式）。  
3. 仅在有阻断证据时沿阶梯上移：原生 API → `curl_cffi`+住宅代理 → camoufox/patchright → hybrid。  
4. 决策写入 worker README 后再实现。

---

## 1B. Actor ↔ Worker：OpenAPI 联调 + 加密鉴权（强制）

Worker 与 Actor **必须**按 OpenAPI 契约对接，并用加密与鉴权保护通信。

### 加密（Encryption）

- 生产 `WORKER_BASE_URL` **必须**为 `https://`（Cloud Run 终止 TLS）。
- Actor `worker_client` 禁止对生产 scrape API 使用明文 `http://`。
- 日志中不要打印完整 `proxyUrl` / API key。

### 鉴权（Authentication）

- Worker 环境变量 **`WORKER_API_KEY`（必填，生产）**：一个或多个 key（逗号分隔）。
- Scrape 路由（至少 `/v1/categories`、`/v1/search`、`/v1/listings`）**必须**校验：
  - `Authorization: Bearer <key>`，或
  - `X-Api-Key: <key>`
- 使用恒定时间比较（如 `hmac.compare_digest`）。
- 缺少/错误 key → **401**。
- Actor 侧 env **`WORKER_API_KEY` 必填**，`worker_client` 每次请求带上上述头。
- `/health`、`/openapi.json`、`/openapi.yaml`、`/docs` 可保持公开（运维/契约发现）；**不得**把 scrape 路由做成生产无鉴权。

### OpenAPI 契约与联调

1. Worker 仓库维护 `openapi/openapi.yaml`（OpenAPI 3.x），声明 `securitySchemes`：

```yaml
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-Api-Key
    BearerAuth:
      type: http
      scheme: bearer
security:
  - ApiKeyAuth: []
  - BearerAuth: []
```

2. 运行时暴露：`GET /openapi.json`、`/openapi.yaml`、`/docs`（Swagger）。  
3. Actor 按该契约实现客户端；联调步骤：
   - 拉 OpenAPI，确认路径/schema/security  
   - 无 key 调 `/v1/search` → 期望 401  
   - 正确 key 小流量 search → 200 + envelope  
   - Actor `apify run` / cloud call 使用同一 key 端到端通过  
4. 密钥只放 Secret Manager / Cloud Run env / Apify Actor secret env，**禁止**写入 git、README、OpenAPI example 明文。

---

## 2. 功能边界

### 2.1 Worker（In）

1. 与源 Actor 对齐的通道/过滤/`detailUrls`/`enrichDetails`。  
2. API：`/health`、OpenAPI/docs、`/v1/categories|search|listings`。  
3. 同引擎重试 / sticky 轮换 → 可选 stealth browser。  
4. 统一 envelope + `schemaVersion`；可选 `fields` / `ndjson` / `webhookUrl`。  
5. **生产 scrape API 鉴权（见 1B）**。

### 2.2 Worker（Out）

- 超出源 Actor 的站点/国家（除非用户要求）。  
- 把 worker 改成 Apify Actor 托管形态。  
- 无验证的 Kasada/CapSolver 豪赌。  
- Store / PPE（Actor 侧，需用户明示）。

### 2.3 Actor（In）

1. Input → worker payload（含 `provider`、`proxyUrl`）。  
2. **HTTPS + API key** 调用 worker；`push_data`。  
3. 预览字段：`name`, `type`, `status`, `country`, `authority`。  
4. KV：`INPUT_ECHO`、`RUN_SUMMARY`、`ERROR_SUMMARY`。  
5. Standby Live View OpenAPI。  
6. README/SEO/PPE（用户要求时）。

### 2.4 Actor（Out）

- 与 worker 重复的浏览器采集。  
- 薄镜像再装 Chrome（浏览器只在 worker，且评估需要时）。

---

## 3. Worker API 合同

### 3.1 Envelope

```json
{
  "status": "ok | partial | failed | blocked",
  "items": [],
  "diagnostics": {},
  "provider": "curl",
  "warnings": [],
  "worker": "<worker-name>",
  "schemaVersion": "YYYY-MM-DD.N"
}
```

`provider` 反映实际引擎：`curl` / `camoufox` / `patchright` / `httpx` 等。

### 3.2 Listing 行

- 预览：`name`, `type`, `status`, `country`, `authority`  
- 核心：`listingId`, `listingType`/`channel`, address 字段, `priceDisplay`, beds/baths, `listingUrl`, `imageUrl`, …

### 3.3 OpenAPI

- 仓库：`openapi/openapi.yaml`  
- 运行时：`/openapi.json`、`/openapi.yaml`、`/docs`  
- 镜像必须 `COPY openapi/`；声明 securitySchemes（见 1B）

### 3.4 Cloud Run 部署基线

#### 区域选择（强制：跟网站所属地区）

Worker 部署 region **对齐目标站主市场地理位置**（降低出站延迟、减少跨境异常；与住宅代理出口策略也更易一致）。按 **TLD + 主市场** 推断，而不是固定某个默认 region。

| 网站所属地区 / 示例 | 推荐 `--region` |
| --- | --- |
| 美国（Zillow、Glassdoor 等） | `us-central1` 或 `us-east1` |
| 澳大利亚（realestate.com.au、Seek AU） | `australia-southeast1` |
| 西欧 / 中欧（Funda NL、Otodom PL、StepStone、Booli…） | `europe-west1` 或 `europe-west4` |
| 土耳其（Hepsiemlak） | `europe-west1` / `europe-west3` |
| 中东 / MENA（Bayt 等） | 优先 `me-west1`（若项目可用），否则 `europe-west1` |

约束：

- Cloud Run **服务区域不可原地修改**；换区 = 在新区重新 `deploy` / Copy，再更新 Actor 的 `WORKER_BASE_URL`，确认后再删旧区服务。  
- README / 部署记录必须写明：`region` + 对应站点国家/市场。  
- **不要**把非澳站 worker 一律打到 `australia-southeast1`。

```bash
gcloud run deploy <service> \
  --project=<gcp-project> \
  --region=<region-matched-to-site-geography> \
  --source=. \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=900 \
  --concurrency=1 \
  --min-instances=0 \
  --max-instances=2 \
  --env-vars-file=/tmp/<service>-env.yaml
```

说明：

- Cloud Run 可 `--allow-unauthenticated`（入口公开），**应用层**仍必须用 `WORKER_API_KEY` 保护 scrape 路由。  
- 含逗号的 env（proxy / 多 key）用 `--env-vars-file`。  
- env 至少包含：`SCRAPE_PROVIDER`、`WORKER_API_KEY`；curl 类引擎另需 `PROXY_URL` 或依赖请求 `proxyUrl`。

### 3.5 Worker 环境变量

| 变量 | 用途 |
| --- | --- |
| `SCRAPE_PROVIDER` | 继承自 Actor 的默认引擎（常见 `curl`） |
| `PROXY_URL` | 自持引擎部署兜底；优先请求 `proxyUrl` |
| `WORKER_API_KEY` | **生产必填**；Bearer / X-Api-Key |
| `PORT` | Cloud Run 注入（默认 8080） |

---

## 4. Actor 实现标准

### 4.1 结构

```
<actor>/
  .actor/actor.json, openapi.json, dataset_schema.json, ...
  input_schema.json
  Dockerfile            # slim
  requirements.txt      # apify, pydantic, requests
  README.md
  src/
    main.py
    worker_client.py    # HTTPS + API key + OpenAPI 路径
    input_model.py
    standby.py
    __main__.py
```

### 4.2 `worker_client.py`

- `WORKER_BASE_URL` 必须 `https://`（生产）。  
- **`WORKER_API_KEY` 必填**；同时设置 `Authorization: Bearer` 与 `X-Api-Key`。  
- Timeout 600–850s。  
- `detailUrls` → `/v1/listings`，否则 `/v1/search`。  
- 401 → 明确鉴权错误；空 items → `NoRowsCollectedError`。

### 4.3 Standby

- `usesStandbyMode` + `webServerSchema: ./openapi.json`  
- `CMD ["python", "-m", "src"]`（禁止只跑 `src.main`）

### 4.4 Input

- 与 worker 对齐字段；`proxyConfiguration` 运行时启用 → `proxyUrl`（curl/camoufox/patchright）。

### 4.5 PPE / README

- PPE 仅用户明确要求时配置（见既有 PAY_PER_EVENT 约定）。  
- README 遵循 Apify marketing playbook。

---

## 5. 开发 Checklist

### Phase A — Worker

1. [ ] `move_agent_to_root` → worker  
2. [ ] **引擎评估**（engines.md）：A/B/C → 默认继承源 Actor  
3. [ ] README 写明 provider / proxy  
4. [ ] 实现 API + OpenAPI（含 securitySchemes）  
5. [ ] 配置 `WORKER_API_KEY`；scrape 路由强制鉴权  
6. [ ] Deploy HTTPS Cloud Run（`--region` 已按网站所属地区选定）  
7. [ ] 联调：OpenAPI → 401（无 key）→ 200（有 key）小流量 search  

### Phase B — Actor

1. [ ] `move_agent_to_root` → Actor  
2. [ ] `worker_client`：HTTPS + API key + OpenAPI 路径  
3. [ ] 瘦镜像 + Standby OpenAPI  
4. [ ] README / SEO；（可选）PPE  
5. [ ] `apify push` + 端到端 DQ  

### Phase C — DQ 硬门槛

- SUCCEEDED、`records > 0`、预览字段、域名、`country`、通道一致、无重复 `listingId`

---

## 6. 反模式（禁止）

1. 跳过引擎评估直接换栈。  
2. Actor / Worker 长期双轨解析。  
3. 生产 scrape API 无鉴权或使用明文 HTTP。  
4. API key / proxy 密码写入 git 或 README。  
5. Standby 声明了端点但入口不是 `python -m src`。  
6. 未要求就发布 Store / 乱改 PPE。  
7. 不 `move_agent_to_root` 就改项目。

---

## 7. 验收命令速查

```bash
# OpenAPI + auth 联调
curl -sS "$WORKER_URL/health"
curl -sS "$WORKER_URL/openapi.json" | head
# expect 401
curl -sS -o /dev/null -w "%{http_code}\n" -X POST "$WORKER_URL/v1/search" \
  -H 'content-type: application/json' \
  -d '{"location":"<city>","maxResults":1}'
# expect 200
curl -sS -X POST "$WORKER_URL/v1/search" \
  -H "Authorization: Bearer $WORKER_API_KEY" \
  -H "X-Api-Key: $WORKER_API_KEY" \
  -H 'content-type: application/json' \
  -d '{"location":"<city>","listingType":"sale","maxResults":3,"maxPages":1}'

# Actor
apify run --purge
apify push
apify call -i '{"location":"<city>","listingType":"sale","maxResults":3}' --timeout 300
```

---

## 8. 新站点最短路径

1. 引擎评估（engines.md）→ 继承源 Actor。  
2. 复制 `zillow-com` worker → 改解析/categories；加上 OpenAPI security + `WORKER_API_KEY`。  
3. 复制 `zillow-scraper` Actor → HTTPS client + 同一 API key + `proxyUrl`。  
4. OpenAPI 鉴权联调 → push → DQ →（可选）PPE/SEO。  

主线：**Actor 薄、Worker 厚；先评估引擎再继承 Actor；OpenAPI + HTTPS + API key 保障 Actor↔Worker 安全。**
