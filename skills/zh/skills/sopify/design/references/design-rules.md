# Design 详细规则

## 目标

设计技术方案，拆分可执行任务，生成可回放的方案包。

## 总流程

1. 判定方案包级别（`light/standard/architecture`）。
2. 生成方案文件骨架。
3. 拆分任务并标注验证标准。
4. 输出摘要并等待宿主后续动作。

## 步骤 1：方案包级别判定

自动判定规则（`plan.level=auto`）：

- `light`：文件数 3-5，且无架构级变更，修改范围明确。
- `standard`：文件数 >5，或新功能开发，或跨模块改动。
- `architecture`：架构级变更、重大重构、新系统设计。

## 步骤 2：生成方案文件

- `light`：生成 `plan.md`。
- `standard`：生成 `plan.md + tasks.md`。
- `architecture`：生成 `plan.md + tasks.md + design.md`。
- 所有正式 plan 包都在 `plan.md` 中写入 `level` frontmatter、统一语义入口和评分区块。
- ADR、diagram、assets、receipts 仅在真实需要时创建，不是任何级别的空目录或必备文件。
- 方案摘要也必须显式输出：
  - `方案质量`
  - `落地就绪`
  - `评分理由`

模板来源统一使用 `assets/` 目录：

1. `assets/plan-template.md`
2. `assets/tasks-template.md`
3. `assets/design-template.md`
4. `assets/adr-template.md`（仅在确有架构决策时使用）

## 步骤 3：任务拆分

任务约束：

1. 每项建议 30 分钟内可完成。
2. 每项需具备可验证完成标准。
3. 依赖关系清晰，避免隐藏前置条件。

任务分类建议：

1. 核心功能实现
2. 辅助功能
3. 安全检查
4. 测试
5. 文档更新（`project.md / blueprint/*`）

任务状态符号：

- `[ ]` 待执行
- `[x]` 已完成
- `[-]` 已跳过
- `[!]` 阻塞中

## 阶段转换

- `workflow.mode=strict`：输出方案摘要后等待确认。
- `workflow.mode=adaptive`：
  - `~go` 触发：进入执行前确认或后续宿主链路。
  - `~go plan` 触发：只输出方案摘要并停止。
- 用户反馈修改意见：留在本阶段，更新文件后再次输出摘要。

## 协议入口边界

方案结构与任务拆分由本技能负责；协议状态写入（active_plan / current_handoff / receipts）统一走 `sopify_writer`，不在本技能直接写入。

## 命名规则

方案目录格式：`YYYYMMDD_feature_name`

示例：

- `20260115_user_auth`
- `20260115_fix_login_bug`
- `20260115_refactor_api`
