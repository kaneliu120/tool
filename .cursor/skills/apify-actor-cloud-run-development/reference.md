# Cloud Run + Apify Actor 开发标准

> 版本：2026-08-14  
> 目的：按同一模式开发「Cloud Run 采集 worker + Apify 薄 Actor」  
> **源文件：** `~/.agents/skills/apify-actor-cloud-run-development/`（与 `~/.cursor/skills/` 同步）。本文件是镜像，不要三处手改。  
> Skill：`~/.cursor/skills/apify-actor-cloud-run-development/`  
> 引擎评估：[engines.md](engines.md) · 出站控制：[egress-control.md](egress-control.md) · 坑表：[pitfalls.md](pitfalls.md)

---

## 1. 架构总览

### 1.1 分工

| 层 | 职责 | 不负责 |
| --- | --- | --- |
| **egress-control** | 舰队代理/解锁凭证与 per-worker 策略（`https://worker.opendata.best`） | 采集业务逻辑；Actor I/O；PPE |
| **Cloud Run Worker** | 采集引擎、`apply_runtime_env`、解析、过滤、分页、详情、failover、OpenAPI、**对 scrape API 鉴权** | Apify Dataset、Store SEO、PPE；egress admin key |
| **Apify Actor** | Input、**HTTPS + API key** 调 worker、`push_data`、KV、README/SEO、PPE、Standby；**默认 `WORKER_PROVIDES_PROXY=1`** | Worker 已存在时在 Actor 内跑浏览器/解锁；调用 egress-control |

```
┌─────────────────────┐   HTTPS + API key    ┌──────────────────────────┐
│  Apify Actor (thin) │ ───────────────────► │  Cloud Run Worker        │
│  OpenAPI 客户端联调  │                      │  OpenAPI 服务端          │
│  dataset + PPE      │ ◄─────────────────── │  /v1/search|/listings    │
│  WORKER_PROVIDES_   │        items[]       │  scrape + apply_runtime  │
│  PROXY=1            │                      └───────────┬──────────────┘
└─────────────────────┘                                  │ runtime-config
                                                         ▼
                                              ┌──────────────────────┐
                                              │ egress-control (OVH)  │
                                              │ worker.opendata.best │
                                              └──────────────────────┘
```

### 1.2 目录约定

| 类型 | 推荐路径 |
| --- | --- |
| Worker | `/Users/kane/Projects/google run worker/<worker-name>/` |
| Actor | `/Users/kane/Projects/Apify Actors/<actor-name>/` |
| Skill | `~/.cursor/skills/apify-actor-cloud-run-development/` |
| 可读副本 | `Apify Actors/docs/` 与 `google run worker/docs/` |

参考实现：Worker `zillow-com` + Actor `zillow-scraper`。  
GCP 项目：`woker-260722`（以现状为准）。  
**Cloud Run `--region`：按采集网站所属地区选择**（见 §3.4），禁止所有 worker 无脑部署到同一区域。

---

## 1A. 采集引擎策略（强制顺序）

详见 [engines.md](engines.md)。

0. **调研契约**（[templates/worker-contract.md](templates/worker-contract.md) / `website-page-research` 一页纸）：每面主通道、闸门、就绪/否定信号。无合同不得写 parse。  
1. **先评估**：按 worker 需求，用历史 Actor（A）、GitHub 分型（B）、公开/X 调研（C）分析引擎与效率。星数压不过已测量的 BFF。  
2. **再默认继承**源 Actor 的引擎与功能面作为**地板**（warm-up、分页、通道、enrich、代理模式）。源 Actor 没做的市场仍须进覆盖矩阵。  
3. 仅在有阻断证据时沿阶梯上移：同域 JSON → `curl_cffi`+住宅代理 → camoufox/patchright → **orch CDP** → Unlocker 最后一档（已验证才留）。  
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
- Actor 侧 env **`WORKER_AUTH` 必填**（Apify secret；兼容回退 `WORKER_API_KEY`），`worker_client` 每次请求带上上述头。
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

- ~~超出源 Actor 的站点/国家~~（已废止：源 Actor 只是下限；须覆盖目标站全部国家/地区、品类、服务，见 SKILL §1b）。  
- 把「单市场 / 单品类 MVP」当交付完成（除非 Kane 书面 waiver）。  
- 把 worker 改成 Apify Actor 托管形态。  
- 无验证的 Kasada/CapSolver 豪赌。  
- Store / PPE（Actor 侧，需用户明示）。

### 2.3 Actor（In）

1. Input → worker payload（含 `provider`；默认**不传** `proxyUrl`）；**暴露全覆盖矩阵**（国家/地区、品类、服务枚举）。  
2. **HTTPS + API key** 调用 worker；`push_data`。  
3. 预览字段：`name`, `type`, `status`, `country`, `authority`。  
4. KV：`INPUT_ECHO`、`RUN_SUMMARY`、`ERROR_SUMMARY`。  
5. Standby Live View OpenAPI。  
6. README/SEO/PPE（用户要求时）；README 含 coverage matrix 勾选表。  
7. Free-tier（Store 向默认）：限额代码 + schema/README 说明。

### 2.4 Actor（Out）

- 与 worker 重复的浏览器采集。  
- 薄镜像再装 Chrome（浏览器只在 worker，且评估需要时）。  
- 仅实现源 Actor / 竞品子集的国家或品类却宣称完成。

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
- env 至少包含：`SCRAPE_PROVIDER`、`WORKER_API_KEY`、`EGRESS_CONTROL_BASE_URL`、`EGRESS_CONTROL_API_KEY`、`EGRESS_CONTROL_WORKER_ID`；保留可选 `PROXY_URL`（及 vendor key）作 **fallback**。  
- **禁止**裸 `--set-env-vars`（会整表擦掉 `EGRESS_CONTROL_*`）。仅追加用 `--update-env-vars`；逗号值只能 `--env-vars-file`。  
- 部署前：`bash scripts/assert_cwd.sh worker` 与 `scripts/print_deploy_plan.sh`。控制面先 `scripts/register_egress_worker.sh`。详见 [egress-control.md](egress-control.md) · [pitfalls.md](pitfalls.md)。

### 3.5 Worker 环境变量

| 变量 | 用途 |
| --- | --- |
| `EGRESS_CONTROL_BASE_URL` | `https://worker.opendata.best`（新 worker 必填） |
| `EGRESS_CONTROL_API_KEY` | 控制面 **runtime** key（非 admin） |
| `EGRESS_CONTROL_WORKER_ID` | 与 Cloud Run 服务名一致 |
| `SCRAPE_PROVIDER` | 继承自 Actor 的默认引擎（常见 `curl`） |
| `PROXY_URL` | 本地/降级兜底；通常由 `apply_runtime_env` 注入 |
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

### 4.4 Input / proxy

- 与 worker 对齐字段。  
- **新 Actor 默认：** `WORKER_PROVIDES_PROXY=1`，不 mint、不传 `proxyUrl`（出站由 worker + egress-control）。  
- 仅遗留/调试例外才启用 Actor `proxyConfiguration` → `proxyUrl`。
- **Schema：** 每个 REQUIRED 字段必须有 `default`（与 `prefill` 同值），或改为 optional。平台自动测试吃 `default` 不是 `prefill`。空 input `{}` 必须 **SUCCEEDED**（不要 `Actor.fail()`）。Kane 云验收仍用随机 `--input-file`，不用这个 default。

### 4.5 PPE / README

- PPE 仅用户明确要求时配置（见既有 PAY_PER_EVENT 约定）。  
- README 遵循 Apify marketing playbook。

### 4.6 Thin Actor 运行成本（`defaultRunOptions`）

- 薄 Actor 墙钟≈等 worker；**CU ∝ 内存 × 时间**，加内存几乎不加速。  
- 默认：`memoryMbytes: 1024`，`minMemoryMbytes: 512`；禁止无证据默认 2048/4096。  
- PPE `apify-actor-start`：**每 GB 一次**（2GB = 2× start）；平台用量开发者付时 CU 直接吃毛利。  
- **仅改内存可不重新部署**：`PUT acts/{id}` 更新 `defaultRunOptions`；同步本地 `actor.json` / `configure_store.py` 防下次 push 回滚。  
- 验收勿强行 `-m 2048`。全文：[actor-compute-cost.md](actor-compute-cost.md)。

---

## 5. 开发 Checklist

### Phase A — Worker

1. [ ] `move_agent_to_root` → worker；`bash scripts/assert_cwd.sh worker`  
2. [ ] **Phase 0 合同**（templates/worker-contract.md）+ 覆盖矩阵；空格标 未验证  
3. [ ] **引擎评估**（engines.md）：调研通道 → A/B/C → 默认继承源 Actor（地板）  
4. [ ] README 写明 provider / proxy / egress `workerId`  
5. [ ] `_shared/sync_shared.sh` + `egress_control_client.apply_runtime_env`  
6. [ ] 实现 API + OpenAPI（含 securitySchemes）；站点 parse 只改差量文件  
7. [ ] `scripts/register_egress_worker.sh`；配置 `WORKER_API_KEY` + `EGRESS_CONTROL_*`（runtime key）  
8. [ ] `scripts/print_deploy_plan.sh` → Deploy HTTPS Cloud Run（`--region` 已按网站所属地区选定）；禁止 `--set-env-vars`  
9. [ ] `scripts/worker_triple_smoke.sh`：health 200 → 401（无 key）→ 授权 rows≥1  

### Phase B — Actor

1. [ ] `move_agent_to_root` → Actor；`bash scripts/assert_cwd.sh actor`  
2. [ ] `worker_client`：HTTPS + API key + OpenAPI 路径（工厂层勿改鉴权）  
3. [ ] 瘦镜像 + Standby OpenAPI；**`WORKER_PROVIDES_PROXY=1`**  
4. [ ] **compute：** `defaultRunOptions.memoryMbytes=1024`（非 2048/4096）；min 512  
5. [ ] Schema REQUIRED+default；空 `{}` SUCCEEDED  
6. [ ] README / SEO；（可选）PPE — 过夜运行不要改价/上架  
7. [ ] `apify push` + 随机 `--input-file` DQ  

### Phase C — DQ 硬门槛

- SUCCEEDED、`records > 0`、预览字段、域名、`country`、通道一致、无重复 `listingId`
- 随机 input JSON 附在验收记录；禁止 README/`<city>`/Austin TX

---

## 6. 反模式（禁止）

1. 跳过 Phase 0 调研契约 / 跳过引擎评估直接换栈。  
2. Actor / Worker 长期双轨解析。  
3. 生产 scrape API 无鉴权或使用明文 HTTP。  
4. API key / proxy 密码写入 git 或 README。  
5. Standby 声明了端点但入口不是 `python -m src`。  
6. 未要求就发布 Store / 乱改 PPE。  
7. 不 `move_agent_to_root` / 不跑 `assert_cwd.sh` 就改项目或 deploy。  
8. 新 worker 不接 egress-control、不登记 workerId / 新 Actor 默认 mint Apify `proxyUrl`。  
9. 把 Bright Data / RiskByPass / CapSolver 密钥或解锁栈放进薄 Actor。  
10. 从 Actor 目录 `gcloud run deploy --source=.`。  
11. 裸 `--set-env-vars`；逗号 env 走 `--update-env-vars`。  
12. Cloud Run 放 admin / 舰队 master key。  
13. 云验收抄 README / schema prefill / 固定城市。  
14. 把 Scrapling / Firecrawl / Crawlee 当 worker 运行时。  
15. 把 orch `/v1/unlock` 写成「去 Bright Data」。  

完整坑表：[pitfalls.md](pitfalls.md)。复制/重写：[templates/copy-vs-rewrite.md](templates/copy-vs-rewrite.md)。

---

## 7. 验收命令速查

禁止用 README / schema prefill / 固定 `<city>`。从已打开矩阵格子抽样。

```bash
SKILL="$HOME/.cursor/skills/apify-actor-cloud-run-development"
# 或 ~/.agents/skills/apify-actor-cloud-run-development

# 身份
bash "$SKILL/scripts/assert_cwd.sh" worker
bash "$SKILL/scripts/print_deploy_plan.sh" --region <geo> --env-file /tmp/<service>-env.yaml

# 随机 input（禁止 Austin, TX / README）
python3 "$SKILL/scripts/random_smoke_input.py" --matrix ./coverage-matrix.json --out /tmp/accept.json

# Worker 三连
WORKER_URL="https://<service>-….run.app" WORKER_API_KEY="…" SEARCH_JSON=/tmp/accept.json \
  bash "$SKILL/scripts/worker_triple_smoke.sh"

# Actor（-m 1024，不要 2048）
apify run --purge
apify push
apify call "<user>/<actor>" -b latest -f /tmp/accept.json -m 1024 -t 900
```

## 8. 新站点最短路径

1. Phase 0：调研一页纸 → `docs/worker-contract.md` + 覆盖矩阵（空格=未验证）。  
2. `scripts/scaffold_worker.sh <peer> <dest>` → 只重写 parse/markets（见 copy-vs-rewrite）。  
3. `scripts/scaffold_actor.sh <peer-actor> <dest-actor>` → 只改 input 字段与 SEO。  
4. `_shared/sync_shared` + `register_egress_worker.sh` + runtime key（非 admin）。  
5. `assert_cwd` → Cloud Run（禁止 `--set-env-vars`）→ 三连烟测 → 随机 `--input-file` DQ。  
6. 交接：Actor ID、worker URL+region、矩阵、随机 JSON、Unlocker 是否仍开、未打开市场。PPE/上架留给 Kane。

主线：**调研合同开工证；Actor 薄工厂、Worker 站点差量；出站收口 egress-control；脚本门禁不可口头勾选。**
