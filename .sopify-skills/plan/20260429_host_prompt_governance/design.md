# Design: Host Prompt Governance

> **定位**：`20260424_lightweight_pluggable_architecture` 总纲的独立治理包。
> **前置**：`20260428_action_proposal_boundary` P0 完成后暴露 4×510 行 prompt 的三层重复维护成本。
> **目标**：建立 prompt 作为 runtime contract 适配层的治理体系，瘦身至 350-400 行，沉淀工程原则。

---

## 痛点分析

P0-F 实施时发现当前 host prompt 存在三层重复：
1. **说明行**：每个机器契约字段在说明行展开一遍
2. **宿主接入约定**：同一契约在约定区再展开一遍
3. **快速参考**：又在参考区列出一遍

4×510 行（Claude CN/EN + Codex CN/EN）的同步维护成本已不可持续。

## 核心原则

> Prompt 是 runtime contract 的适配层，不是事实源。

6 条待沉淀工程原则：
1. prompt 不定义机器契约——引用 runtime 输出
2. prompt 不解释算法——声明能力和入口
3. prompt 不维护两份相同的路由表
4. prompt 修改必须通过准入脚本验证
5. prompt 行数有硬上限（目标 350-400 行）
6. prompt 变更必须与 runtime gate contract 保持一致

## 执行范围

### Phase 1: 审计与原则沉淀
- 重复规则审计：标注哪些区块是重复的、哪些是唯一事实源
- 沉淀工程原则至 `.sopify-skills/blueprint/prompt-governance.md`

### Phase 2: Prompt 架构分层
- 重构 prompt 为分层结构：
  1. 核心角色定义（~30 行）
  2. Gate 算法与入口（~60 行）
  3. Checkpoint 状态表（~80 行）
  4. 输出格式约束（~40 行）
  5. 资源索引（~40 行）
  6. 配置与品牌（~30 行）
- 目标：350-400 行/variant

### Phase 3: 准入脚本
- `check-prompt-governance.py`：
  - 行数上限检查
  - 必需区块存在性检查
  - 重复模式检测
  - 与 runtime gate contract 版本一致性检查

## 不做

- 不改 runtime gate / engine / router 逻辑
- 不改机器契约定义（只改 prompt 中的引用方式）
- 不合并到 legacy_feature_cleanup 包
