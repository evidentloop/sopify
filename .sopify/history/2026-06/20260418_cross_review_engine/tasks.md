---
plan_id: 20260418_cross_review_engine
feature_key: cross_review_engine
level: standard
lifecycle_state: deferred
archive_type: deferred_archive
archive_reason: "CrossReview 已独立为 evidentloop/CrossReview，核心洞察已沉淀到外部仓库，Sopify 侧集成工作不再推进"
knowledge_sync:
  project: skip
  background: skip
  design: skip
  tasks: skip
archive_ready: true
---

# 任务清单: CrossReview Sopify 集成

> 本方案聚焦 Sopify 侧集成任务。CrossReview 产品任务见 `evidentloop/CrossReview` 仓库蓝图。

## 已完成

- [x] 0.1 产品命名与定位决策（Q1-Q9）→ 已固化到 CrossReview 蓝图
- [x] 0.2 产品边界与仓库形态 → CrossReview 已独立（`evidentloop/CrossReview`）
- [x] 0.3 SKILL.md 创建（`.agents/skills/cross-review/SKILL.md`）
- [x] 0.4 首次 E2E dogfood（2026-05-31，host-integrated 路径）

## Phase 4a — Advisory 集成（当前）

- [x] SKILL.md host-integrated 流程就位
- [ ] 日常 dogfood 2 周+，收集可用性反馈
- [ ] 根据 dogfood 反馈优化 SKILL.md 流程
- [ ] 确认 f-002（符号纪律命名不一致）修复方案

## Phase 4b — Runtime Bridge（暂缓）

- [ ] bridge.py: CrossReview verdict → Sopify checkpoint proposal
- [ ] develop_quality 映射: CrossReview finding → spec_compliance / code_quality
- [ ] review.md 作为 plan asset: finalize 时写入 finding snapshot
- [ ] handoff 集成: `handoff.artifacts.cross_review_verdict` 字段

## 启动条件

Phase 4b 启动需满足：
1. Phase 4a dogfood 稳定 2 周+
2. CrossReview normalizer / adjudicator 无 silent drop bug
3. 用户确认 advisory → checkpoint 升级有价值

## 历史参考文档

以下文档完成了 CrossReview 产品孵化使命，核心洞察已吸收至 CrossReview 自身蓝图：

- `cross-project-insights.md` — 5 个外部项目（Hermes、HelloAgents、Spec-Kit、Superpowers、Graphify）的架构洞察，12 项高价值思想已分类归档
- `hermes-insights.md` — Hermes Agent 知识沉淀机制分析，SkillGuidedReviewer / FindingNormalizer / 全局 rubric 等概念已写入 CrossReview 蓝图 v1+ 设计预留
- `product-form-analysis.md` — CrossReview 独立产品形态分析（CLI / SDK / MCP / Skill / CI 五通道），产品边界已固化到 CrossReview 蓝图

这些文件保留为历史参考，不参与当前执行判断。
