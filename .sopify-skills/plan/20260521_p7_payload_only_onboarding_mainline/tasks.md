---
plan_id: 20260521_p7_payload_only_onboarding_mainline
feature_key: p7_payload_only_onboarding_mainline
level: standard
lifecycle_state: active
---

# 任务清单

## 决策记录

| DR | 决策 | 约束 |
|----|------|------|
| DR-1 版本锚点 | `.sopify-skills/sopify.json`（极简，~5 字段） | 版本真值只在此文件，不重复 |
| DR-2 Prompt 分发 | 完整 prompt 留全局；repo 只放 host header pointer（managed block upsert） | pointer 不含绝对路径，header filename 由 host adapter 决定 |
| DR-3 Bootstrap 入口 | `python3 -m sopify_bootstrap` canonical，`curl\|bash` convenience | repo 产出 = sopify.json + host header pointer（Copilot 首实现 = AGENTS.md） |

**定性：** P7 不是从 0 到 1 的全局化。全局发动机已就位，P7 只替换 repo 内的 legacy 激活物（`.sopify-runtime/manifest.json` → 新两文件模型）。架构层宿主无关，验收层 Copilot-first。

## S1: 激活物迁移方案分析 + 新 marker/pointer 模型定义

- [x] 现状全链路走读：全局发动机 + repo thin stub 的消费者全景
- [x] `.sopify-runtime/manifest.json` thin stub 字段清单 + 6 个生产消费者映射
- [x] 版本锚点迁移方案评估 → DR-1 APPROVED: `.sopify-skills/sopify.json`
- [x] prompt 分发模型修订 → DR-2 APPROVED: 全局 prompt + repo 轻量 pointer
- [x] bootstrap 入口决策 → DR-3 APPROVED: `python3 -m sopify_bootstrap` canonical
- [x] P7 定性校正：不是 greenfield 全局化，而是 repo 激活物迁移
- [x] 决策拍板（DR-1/2/3 全部 APPROVED，含约束条件）

## S2: 激活物迁移实现

- [ ] `.sopify-skills/sopify.json` schema + 读写逻辑
- [ ] 6 个生产消费者检测路径迁移（`.sopify-runtime/manifest.json` → `sopify.json`）
- [ ] workspace detection 锚点切换（祖先扫描改为 `sopify.json`）
- [ ] repo-local host header pointer：managed block upsert（宿主无关机制，Copilot 首实现 = AGENTS.md）
- [ ] bootstrap 命令适配外部 repo（不依赖 deep installer mainline）
- [ ] 接续链路验证：handoff 消费 + state 写入 via canonical_writer

## S3: 首次体验 + diagnostics

- [ ] 外部 repo 首次 bootstrap 的 diagnostics 输出（缺什么报什么）
- [ ] 错误路径覆盖：未初始化 / 版本不匹配 / payload 缺失
- [ ] status 命令适配外部 repo 场景
- [ ] 约束：只做 happy path + 常见错误路径，不动 deep installer doctor 逻辑

## S4: 发布链 + example

- [ ] release asset 结构定义
- [ ] install/bootstrap 命令文档
- [ ] examples/ 包含至少 1 个可独立跟随的端到端 demo
- [ ] README 更新（含接入步骤 + 视觉资产）

## S5: Smoke test + 验收

- [ ] 机器 smoke test：bootstrap → state write → handoff consume（端到端）
- [ ] 至少 1 个非 Sopify repo 走通全链路
- [ ] receipt + 蓝图同步 + history 归档
