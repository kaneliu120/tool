# 验证记录（软件闭环）

**日期**：2026-07-19  
**分支**：`cursor/rea-kasada-html-provider-cb45`

## 命令与结果

| 步骤 | 命令 | 结果 |
|---|---|---|
| 单元/合同测试 | `pytest -q` | **14 passed** |
| 4 URL 合同 | `python scripts/test_html_provider.py --provider mock_fixture` | **ok=true**（4/4） |
| Actor canary | `python scripts/run_canary_local.py` | **SUCCEEDED**，datasetRows=4，blockedCount=0 |
| 现场 Kasada probe | `python scripts/kasada_probe_rea.py` | **429 / 715B shell**，已保存 html + ips.js + record JSON |

## Fail-closed 核对

- KPSDK 壳页：`tinyKasadaShell=true`，gateway `ok=false`
- 非白名单域名：HTTP 400
- 壳页不会产出 dataset rows

## 未完成（硬件依赖）

- Mac Chrome runner 真实 4 URL canary
- Apify Actor 远程 `maxItems=2` + `htmlProvider=internal_mac_runner`
