---
plan_id: 20260521_p7_payload_only_onboarding_mainline
feature_key: p7_payload_only_onboarding_mainline
level: standard
lifecycle_state: active
---

# 任务清单

## 决策记录

（S1 分析后填充）

## S1: 接入路径分析 + 版本锚点归宿决策

- [ ] 当前 bootstrap 路径全链路走读：installer 入口 → payload manifest → `.sopify-runtime/` 落地逻辑
- [ ] `.sopify-runtime/manifest.json` thin stub 字段清单 + 各字段的消费者清单
- [ ] 版本锚点迁移方案评估：`.sopify-skills/sopify.json` vs `.sopify-skills/manifest.json` vs 保留 stub
- [ ] prompt asset 分发方案：AGENTS.md / CLAUDE.md 的位置 + 不碰 `.github/copilot-instructions.md` 的机制
- [ ] 外部 repo 最小结构定义（接入后 `.sopify-skills/` 里应该有什么）
- [ ] 决策记录填充

## S2: 接入路径实现

- [ ] 版本锚点迁移（按 S1 决策）
- [ ] bootstrap 命令适配外部 repo（不依赖 deep installer mainline）
- [ ] prompt asset 分发机制实现
- [ ] `.sopify-skills/` workspace 初始化最小脚手架
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
