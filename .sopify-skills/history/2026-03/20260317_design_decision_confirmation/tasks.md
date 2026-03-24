---
plan_id: 20260317_design_decision_confirmation
feature_key: design-decision-confirmation
level: standard
lifecycle_state: archived
knowledge_sync:
  project: review
  background: review
  design: review
  tasks: review
blueprint_obligation: review_required
archive_ready: true
---

# 任务清单: 决策确认能力通用化（兼容现有接入链路）

目录: `.sopify-skills/history/2026-03/20260317_design_decision_confirmation/`

当前建议执行顺序：

1. `7.x` richer templates 扩展
2. `13.2` compare facade 边界评估
3. 接入链路健壮性与宿主产品级桥接接入

## 0. 当前已落地基线

- [x] 0.1 runtime 已支持 `decision_pending / decision_resume`
- [x] 0.2 `.sopify-skills/state/current_decision.json` 已作为活跃决策状态文件落地
- [x] 0.3 `RuntimeHandoff.required_host_action` 已支持 `confirm_decision`
- [x] 0.4 `~decide status|choose|cancel` 已作为 debug / override 入口落地
- [x] 0.5 已确认决策可恢复 planning，并在需要时重新进入 execution gate
- [x] 0.6 execution gate 已可创建 follow-up decision checkpoint
- [x] 0.7 `ready_for_execution` 已作为内部 `RunState.stage` 落地
- [x] 0.8 `execution_confirm_pending` 已接在 gate ready 后，普通链路不会被 `~go exec` 绕过

## 1. 本轮文档收口

- [x] 1.1 将 `background.md` 改写为“当前真实状态 + 下一阶段目标”
- [x] 1.2 将 `design.md` 改写为“兼容现有接入链路的通用化方案”
- [x] 1.3 将 `tasks.md` 改写为“已落地基线 + 下一阶段 delta”
- [x] 1.4 明确当前主交互宿主是 CLI 型宿主，editor-side richer surface 不在当前实施范围
- [x] 1.5 明确一键接入、自动 bootstrap、manifest-first、默认 runtime 入口保持不变

## 2. 通用 Runtime Contract

- [x] 2.1 在 `runtime/models.py` 中为 decision 增加通用字段模型：`DecisionCondition`
- [x] 2.2 在 `runtime/models.py` 中补充通用字段模型：`DecisionValidation`
- [x] 2.3 在 `runtime/models.py` 中补充通用字段模型：`DecisionField`
- [x] 2.4 在 `runtime/models.py` 中补充推荐模型：`DecisionRecommendation`
- [x] 2.5 在 `runtime/models.py` 中补充通用 checkpoint 模型：`DecisionCheckpoint`
- [x] 2.6 在 `runtime/models.py` 中补充通用 submission 模型：`DecisionSubmission`
- [x] 2.7 明确 `when` 支持的最小操作集：`equals / not_equals / in / not_in`
- [x] 2.8 明确字段类型最小集合：`select / multi_select / confirm / input / textarea`
- [x] 2.9 为上述对象补齐 `to_dict / from_dict` 契约
- [x] 2.10 明确与当前窄版 `DecisionState` 的兼容策略

## 3. State 与兼容投影

- [x] 3.1 保持 `.sopify-skills/state/current_decision.json` 路径不变
- [x] 3.2 在现有 decision state 中增加 `checkpoint / submission / resume` 语义分层
- [x] 3.3 明确状态流转：`pending / collecting / confirmed / consumed / cancelled / timed_out / stale`
- [x] 3.4 保留单选场景的 legacy projection，兼容 `question / options / recommended_option_id`
- [x] 3.5 让宿主可回写结构化 submission，而不是只依赖自由文本解析
- [x] 3.6 保持 `reset_active_flow` 时同步清理 decision state

## 4. Handoff Contract 升级

- [x] 4.1 保持 `handoff_kind="decision"` 不变
- [x] 4.2 保持 `required_host_action="confirm_decision"` 不变
- [x] 4.3 在 `artifacts` 中新增完整 `decision_checkpoint`
- [x] 4.4 在 `artifacts` 中新增 submission 摘要或状态投影
- [x] 4.5 保留 `decision_file` 指针，供宿主兜底读取
- [x] 4.6 明确宿主优先读取 `artifacts.decision_checkpoint`，缺失时再回退到 `current_decision.json`

## 5. Runtime Flow 升级

- [x] 5.1 在 `runtime/engine.py` 中支持宿主写回 submission 后的恢复路径
- [x] 5.2 在 `runtime/router.py` 中让 pending decision 优先识别结构化 submission 状态
- [x] 5.3 保留 `1 / 2 / ...` 与 `~decide choose <option_id>` 的旧版单选输入兼容
- [x] 5.4 保持 `decision_resume` 仍是恢复决策后的统一入口
- [x] 5.5 明确通用 decision 不改变 `ready_for_execution -> execution_confirm_pending` 现有执行链路
- [x] 5.6 保持 `~go exec` 只作为恢复 / 调试入口，不作为通用 decision bypass

## 6. Trigger Policy 迁移

- [x] 6.1 明确当前 planning request 语义触发是基线，不在第一步推翻
- [x] 6.2 在 `runtime/decision_policy.py` 中抽出通用 decision policy
- [x] 6.3 第一阶段先复用现有 planning 语义触发接入通用 checkpoint contract
- [x] 6.4 第二阶段再评估 design-stage policy，让候选方案 tradeoff 复用同一套 checkpoint
- [x] 6.5 定义应触发条件：至少 2 个可执行候选方案，且关键 tradeoff 显著
- [x] 6.6 定义抑制条件：用户偏好已足够明确、只有单一明显优解、只是信息补全

## 7. 模板与最小能力

- [x] 7.1 新增 `runtime/decision_templates.py`
- [x] 7.2 第一版只实现 `strategy_pick`
- [x] 7.3 `strategy_pick` 至少提供 1 个 `select` 字段
- [x] 7.4 支持 `custom` 选项命中 `textarea` 或补充说明字段
- [x] 7.5 支持 `confirm` 或 `input` 类型字段表达额外约束
- [x] 7.6 模板字段总数控制在 3 个以内
- [x] 7.7 推荐项与推荐理由必须可稳定写入 replay 摘要

## 8. CLI Host Bridge

- [x] 8.1 CLI 型宿主当前默认提供内置 interactive renderer
- [x] 8.2 richer terminal UI 仅作为 CLI 宿主的实现细节，不进入 runtime machine contract
- [x] 8.3 当库依赖不可用时，CLI 宿主必须退化到纯文本桥接
- [x] 8.4 CLI 宿主仍应兼容 `1 / 2 / ~decide choose <option_id>` 的旧版单选路径
- [x] 8.5 CLI 宿主写回 submission 后，仍通过默认 runtime 入口恢复当前会话

## 9. 当前范围边界

- [x] 9.1 当前主交互宿主收口为 CLI 型宿主
- [x] 9.2 editor-side 或图形表单 UI 不纳入当前实施范围
- [x] 9.3 文档当前只记录 CLI bridge 的使用口径，不再并列描述 editor-side richer surface

## 10. 接入链路保护

- [x] 10.1 保持 `scripts/install-sopify.sh` / `scripts/install_sopify.py` 作为一键接入入口
- [x] 10.2 保持全局 payload + `bootstrap_workspace.py` 按需补齐 `.sopify-runtime/`
- [x] 10.3 保持 `.sopify-runtime/manifest.json` 为 workspace machine contract
- [x] 10.4 保持 `default_entry == scripts/sopify_runtime.py`
- [x] 10.5 保持 vendored 默认入口为 `.sopify-runtime/scripts/sopify_runtime.py`
- [x] 10.6 若新增 helper，仅能作为内部辅助，不得变成用户必须记忆的新主入口
- [x] 10.7 payload current 判定必须校验完整 bundle，避免旧 payload 因版本相同被误判为 current

## 11. Output / Replay / Plan Metadata

- [x] 11.1 output 中继续以“决策确认”呈现当前阶段，但不强制新增固定主 route
- [x] 11.2 output 优先渲染 checkpoint 摘要，而不是完整 schema dump
- [x] 11.3 replay 中记录 checkpoint 创建、推荐项、最终选择与关键约束摘要
- [x] 11.4 replay 默认不完整回放敏感自由输入
- [x] 11.5 plan metadata 对单选类 checkpoint 继续保留 `selected_option_id / status` 投影，兼容 execution gate

## 12. Manifest / Catalog / Docs / Tests

- [x] 12.1 manifest capability 仅表达能力增强，不改默认入口
- [ ] 12.2 builtin catalog 如需新增 facade，只能作为 runtime capability facade，不能改主链路
- [x] 12.3 README 与 AGENTS 文档需同步说明“接入方式不变，桥接能力增强”
- [x] 12.4 为 contract 增加序列化测试
- [x] 12.5 为 state 增加 submission 回写与恢复测试
- [x] 12.6 为 handoff 增加 `decision_checkpoint` artifacts 测试
- [x] 12.7 为 CLI bridge 补一组契约测试
- [x] 12.8 为旧版单选兼容路径补回归测试

## 13. 第二批预留

- [x] 13.1 让 design-stage policy 直接消费候选方案 tradeoff
- [x] 13.2 评估 `model-compare` 接入统一 checkpoint / submission 协议
- [x] 13.3 评估 `analyze` 阶段是否接入轻量 scope clarify 模板
- [x] 13.4 收口文档口径，明确 CLI 型宿主是当前主交互链路，editor-side richer surface 不在当前范围

说明：

- `13.1` 当前通过 `RouteDecision.artifacts.decision_candidates` 落地，policy 会优先消费结构化候选方案，并支持显式抑制标记。
- `13.2` 当前以 `current_handoff.json.artifacts.compare_decision_contract` facade 方式落地，保持 `~compare` 继续走原路由，不直接改写为主链路 `current_decision.json`。
- `13.3` 当前以 `clarification_form / clarification_submission_state` + `runtime/clarification_bridge.py` + `scripts/clarification_bridge_runtime.py` 保守落地，不改变 `answer_questions` 与默认 runtime 入口。
- `13.4` 当前已把文档口径收敛为“CLI 型宿主是当前主交互链路”；editor-side richer surface 不纳入本阶段实施范围。
