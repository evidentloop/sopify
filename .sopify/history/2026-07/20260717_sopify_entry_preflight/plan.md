---
title: Sopify 会话入口状态预检
plan_id: 20260717_sopify_entry_preflight
status: completed
lifecycle_state: archived
level: standard
created: 2026-07-17
updated: 2026-07-17
archive_ready: true
---

# Sopify 会话入口状态预检

## Plan Snapshot

- **Goal**: 让宿主在 managed plan 操作前用有限状态检查判断是否可继续，同时保证普通问答不被陈旧状态劫持。
- **Status**: 5 个 Wave、双视角独立审计与最小修复均已完成并验证。
- **Next**: 无活动接续；后续多宿主持久 MCP 注册或 EvidentLoop 审计闭环按 blueprint 独立开包。
- **Task**: 7/7。

## Context / Why

P8 已规定宿主先识别用户意图，再决定是否读取 `active_plan → plan.md → current_handoff → receipts`。当前规则仍缺少有限状态矩阵和防重复追问约束，`workspace_status_lite` 也只返回目录及文件是否存在，无法稳定区分缺失、失配和可继续状态。

真实目标不是建设诊断平台，而是避免两类失败：陈旧状态抢占用户问题；managed plan 遇到状态异常时重复检查、重复询问，却没有推进或收口。

## Scope

- 明确 consult、quick fix、new plan、continue、finalize 和协议写入的预检边界。
- 给现有 `workspace_status_lite` 补充 plan 与 handoff 的必要客观事实，不新增 MCP tool。
- 将“正常静默、非阻断提示、阻断一次”落实到中英文宿主 prompt、协议和测试。
- 用自动化状态矩阵和一次 Codex 上下文隔离回放验证“先回答用户”。
- 实施完成后同步长期文档并按现有生命周期收口。

## Approach

1. 宿主先分类用户意图；consult 和 unmanaged quick fix 不进入状态接续链。
2. managed plan 操作只消费现有两文件状态模型及 plan/receipt 事实；处理优先序固定为本轮用户意图、活动方案有效性与主体绑定、匹配该方案的 handoff/checkpoint。
3. 4 步文件协议是规范路径；`workspace_status_lite` 可用时只合并读取客观事实，不可用时直接按文件协议继续，也不返回工作流 `next_action`。
4. 可唯一判断的情况直接继续；只有可能改变有效方案意图时才询问，并且同一轮只询问一次。
5. 用户已明确发起的合法操作可通过 canonical writer 自然替换陈旧提示，不追加“是否清理”的二次确认。
6. checkpoint 首次出现时展示一次；用户正在回答该 checkpoint 时先消费回答，不重复展示原问题。
7. `active_plan` 保持 workspace 级纯指针，Wave 留在方案进度中；显式审计其他方案只绑定目标主体并写方案级证据，不切换 active plan。
8. 多会话只做来源追踪和写前复核；不同 session 标识本身不构成并发冲突，只有约定的三类并行推进信号才停止当前写入。

## Waves / Steps

1. 收紧协议状态矩阵与防循环规则。
2. 扩充 lite 状态事实，并保持现有工具与两文件状态模型不变。
3. 同步中英文宿主 prompt 和公开工作流文档。
4. 补状态矩阵、安装资产静态检查和一次 Codex 上下文隔离回放。
5. 同步 blueprint、验证后按现有 finalize 流程归档。

## Key Decisions

- 健康状态静默通过；consult 和 quick fix 不展示无关状态异常。
- 不自动修复 machine truth。只有用户已明确发起新建、接续或写入动作时，canonical writer 才按该授权执行正常状态写入。
- 无效旧 `active_plan` 遇到明确 new plan 时直接切到新方案；有效旧方案仍需确认切换、合并或暂停。
- 无效旧 `active_plan` 遇到明确且有效的 continue 目标时，直接激活该方案并继续，不追加清理确认。
- `plan.md` 是语义真相源；handoff 失配只提示一次并继续，下一次正常 handoff 写入自然替换旧提示。
- 只有与有效 active plan 匹配的 handoff/checkpoint 才可消费；consult 不消费 checkpoint，new plan 只处理自身的一次方案切换仲裁。
- checkpoint response 先绑定当前 plan 与匹配 checkpoint，再通过 writer 更新一次；不得先把同一 checkpoint 重新问给用户。
- MCP 是可选加速层，不是宿主进入 managed plan 的硬依赖。
- `active_plan` 只保存 `plan_id`；Wave 和任务进度继续以 `plan.md` / `tasks.md` 为准。
- 显式审计非 active plan 时，审计器只读目标并返回 `verdict / evidence / source`；宿主重新校验目标 `plan.md` 后，仅通过 `sopify_writer` 写目标方案既有的 `verify_NNN` receipt，不切换 active plan 或 handoff；同名 receipt 已存在时 writer 必须拒绝覆盖。
- session 标识仅作追踪，不单独触发阻断。仅当用户明确要求同时开发、宿主确认另一任务仍在运行，或写入前发现非本轮已知写入导致的目标 digest / 匹配 handoff 变化时，才停止当前有副作用的开发。
- 发现并行推进信号时只提示一次；用户确认其他开发已停止后，重读最新方案状态再继续。
- 验收范围为状态矩阵自动测试、宿主 prompt 静态校验和一次 Codex 上下文隔离回放；Codex 是本次代表宿主，不扩展为多宿主实测矩阵。

## Constraints / Not-in-scope

- 不新增 state 文件、持久诊断记录、MCP tool、全量能力注册表或统一诊断平台。
- 不做自动清理、自动迁移 legacy plan、并发锁、无限重试或异常自愈框架。
- 不把 persistent MCP、doctor、依赖供给或多宿主自动注册纳入本方案。
- 不接入 CrossReview / EvidentLoop；其反馈闭环稳定后再作为方案审计环节接入。
- 只保留一张入口架构 SVG 解释总链路；精确状态规则仍以协议和矩阵为准，不制作第二张图。

## Status / Progress

- [x] 用户确认正常静默、异常不自动修复、无关异常不阻断当前请求。
- [x] 用户确认无效旧指针的新方案切换边界和最小验收范围。
- [x] 独立产品评审完成并吸收一轮最小修正。
- [x] 使用 Fireworks 生成并校验单张入口架构 SVG，嵌入技术设计。
- [x] 独立复审图文一致性、蓝图符合度和整体闭环；结论为 `approve_with_minor_changes`。
- [x] 局部收口 checkpoint response、明确 continue 目标、静态语义断言与多会话最小边界。
- [x] 用户确认 active plan 纯指针、审计旁路和并行推进信号下的简洁交互边界。
- [x] 独立复审本轮局部补齐；结论为 `approve_with_minor_changes`，无 P1、无新增产品决策。
- [x] 最小收口审计写责、并发信号与静态语义断言；未扩展 review wire、EvidentLoop 或并发基础设施。
- [x] 复用现有 MCP 防覆盖语义，将同名 receipt 拒绝写入及单测局部纳入任务 1.1。
- [x] 用户审计并确认方案。
- [x] 用户确认方案后进入开发。
- [x] 5 个 Wave 均完成自验；全量测试、三场景 protocol check 和代表宿主回放通过。
- [x] 产品交付与架构实现双视角独立审计完成；原子防覆盖、确认后重读和证据元数据三项最小修复已闭环，最终 P1 / P2 / P3 均为 0。

## Next

方案已完成并归档，无活动接续；后续工作按 blueprint 独立开包。
