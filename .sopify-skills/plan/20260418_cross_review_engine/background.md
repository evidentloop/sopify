# 变更提案: CrossReview Sopify 集成

## 需求背景

Sopify 的稳定性结构覆盖了预防层（runtime gate、checkpoint）和恢复层（handoff、plan/history），但在"发现错误"层缺少正式的一等能力。用户实践表明，生产会话与审查会话分离能显著提高问题发现率，核心机制是 **context isolation**。

CrossReview 已作为独立产品完成 v0 CLI（`evidentloop/CrossReview`，v0.1.0a3），提供隔离审查管道：ReviewPack → Reviewer → FindingNormalizer → Adjudicator → ReviewResult。

本方案聚焦 **Sopify 如何集成 CrossReview**。CrossReview 产品设计已迁移至其自身蓝图，不再在本方案中维护。

## Sopify 集成目标

1. develop 阶段完成后，通过 SKILL.md（`.agents/skills/cross-review/`）触发 advisory review
2. 审查结果作为 advisory signal 展示，不阻断主流程
3. 未来可升级为 checkpoint proposal（Phase 4b bridge）

## 当前状态

- CrossReview v0.1.0a3 已发布（PyPI + CLI）
- SKILL.md 已就位（`.agents/skills/cross-review/SKILL.md`）
- 首次 E2E dogfood 已完成（2026-05-31）
  - host-integrated 路径跑通：pack → render-prompt → isolated review → ingest
  - 发现 1 个真实 "caught by isolation" case（符号纪律命名不一致）
  - 发现 normalizer 解析 bug（已修复）

## 产品关系

| 维度 | 说明 |
|------|------|
| CrossReview | 独立产品，Sopify 是首个深度集成宿主 |
| Sopify 角色 | 消费方 + dogfood 用户 |
| 产品决策 | 归 CrossReview 仓库蓝图 |
| 本方案范围 | 仅 Sopify 侧集成逻辑 |

## 非目标

- 不在本方案中维护 CrossReview 产品设计
- 不在本方案中定义 ReviewPack/ReviewResult schema
- 不在本方案中管理 CrossReview 路线图
