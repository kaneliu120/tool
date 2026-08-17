# reverse-skill 快路由表

源仓权威：`/Users/kane/Projects/reverse-skill/skills/MASTER-ROUTING.md`  
路径均相对 `.../skills/`。输出格式：`PRIMARY=<dir> · 依据=<一句话>`。

## 优先级（高 → 低）

| ID | 条件 | PRIMARY |
|----|------|---------|
| R1 | APK / smali / jadx / apktool | `apk-reverse/` |
| R2 | IPA / iOS / Objection / MobSF | `mobile-reverse/` |
| R3 | JS 签名 / 前端加密 / jshook / CDP / captchaBody | `js-reverse/` |
| R4 | DSL VM / 自定义 opcode / fireye 式解释器 | `reverse-engineering/dsl-vm-reverse/` |
| R5 | .NET / dnSpy / de4dot | `dotnet-reverse/` |
| R9 | 恶意样本 / YARA / 沙箱 | `malware-analysis/` |
| R6 | IDA 深挖 | `ida-reverse/` |
| R7 | radare2 / r2 | `radare2/` |
| R8 | 固件 / binwalk / EMBA | `firmware-pentest/` |
| R21 | 协议 / Protobuf / PCAP 帧 | `protocol-reverse/` |
| R19 | 浏览器/桌面自动化（非真 Chrome 调研） | `browser-automation/` |
| R22 | Ghidra | `ghidra-reverse/` |
| R30 | 浏览器扩展 MV3 | `browser-extension-reverse/` |
| R33 | Go / Rust 二进制 | `go-rust-reverse/` |
| R12 | API / GraphQL / BOLA / JWT | `api-security/` |
| R11 | Nmap / Nuclei / SQLMap 工具链 | `pentest-tools/` |
| R10 | 完整攻击链 / 红队编排 | `attack-chain/` |
| R20 | 报告 / writeup | `docs-generator/` |
| R0 | 通用逆向 / OLLVM / 未知二进制 | `reverse-engineering/` |

未命中强关键词 → `R0`，并打开源仓 `routing.md` 三轴表。

## Kane 常用组合

| 场景 | 组合 |
|------|------|
| Shop SC 加密提交 | R3 →（VM 特征）R4；产物=解密/复现 captchaBody |
| Temu 滑块算法 | R3 + 页面观察；施力/过墙归 worker PoC |
| 真 Chrome 结构调研 | **不要**当本包 PRIMARY → `use-my-browser` / `website-page-research` |
| 授权抓包还原私有 RPC | R21；客户端算法回 R3/R6 |

## CTF

多类型 CTF 编排 → 源仓 `../CTF-Sandbox-Orchestrator/`（非本路由默认）。

## 边界

- 纯业务爬虫/Cloud Run 接线 → Apify/worker skill，不走攻击链模块  
- 未授权目标 / 生产盲打 → 停止  
- 安装外部 skill/MCP → 源仓 `ops/skill-supply-chain.md`
