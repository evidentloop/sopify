# 变更提案: 从 HelloAGENTS / Superpowers 对比收口 Sopify 的学习路径与实施顺序

## 需求背景

当前仓库已经通过多轮对比得到较稳定的判断：

1. Sopify 的真正差异化资产是 `runtime gate -> handoff -> checkpoint` 的机器契约，以及 `registry -> active -> finalize -> history -> blueprint` 的 plan 生命周期，而不是“支持多少宿主”或“有多少命令面”。
2. 当前可见活跃计划更偏向 installer、README、plan 管理与 runtime 自身收口，存在“复杂度向内生长”的风险；最直接影响用户写代码体验的缺口，反而在 `develop` 执行质量、验证闭环和用户可观测性。
3. 本次任务不是立刻实现所有借鉴点，而是把“该学什么、先做什么、先不做什么”收口成后续可执行顺序，避免再新增一个只管理 Sopify 自己的 meta plan。

评分:
- 方案质量: 8.5/10
- 落地就绪: 8/10

评分理由:
- 已有对比结论、现有活跃 plan、以及 `future_directions.md` 足以支撑路线选择；
- 但本轮本质上是 steering plan，直接进入开发实施会过宽，后续仍需拆成 2-4 个窄实现 plan。

## 变更内容

1. 固定学习优先级：开发态执行质量 > 用户可观测性 > gate 渐进降级 > 分发。
2. 明确哪些能力值得借鉴，哪些只保留为延后项。
3. 收口当前活跃 plan 的优先级与边界，避免继续把精力投到 plan 元系统扩张。
4. 给出“Sopify 如何成为更好的帮用户写代码的工具”的实施顺序和成功标准。

## 影响范围

- 模块:
  - `runtime/`
  - `installer/`
  - `Codex/Skills/*/sopify/develop/`
  - `.sopify-skills/plan/`
  - `README.md`
  - `README_EN.md`
- 计划:
  - `20260320_helloagents_integration_enhancements`
  - `20260323_unified_plan_history_index`
  - `20260323_readme-gate-changelog`
  - 后续新增的 `develop-quality-loop / runtime-gate-degradation / distribution` 独立 plan

## 风险评估

- 风险: 把“战略收口”和“直接编码实现”混在同一个 composite plan 里，会导致 execution gate 长期 blocked。
  - 缓解: 把本 plan 定位为 steering plan；执行层只允许落到窄范围 follow-up plan。

- 风险: 过度照搬 HelloAGENTS / Superpowers 的实现形式，会稀释 Sopify 现有机器契约优势。
  - 缓解: 只学习“用户可见结果”和“执行纪律”，不把 `manifest-first + handoff-first + checkpoint_request` 主链改成 prompt-only 或 hook-first 系统。

- 风险: 继续优先做多宿主、子智能体平台、plan 管理增强，会延迟真正的用户价值交付。
  - 缓解: 先冻结新增 meta-system 扩张，把下一轮重心转到 `develop` 体验与 `status/doctor`。

## 实施前最终收口

为避免本轮再次滑回“讨论方向正确，但执行入口仍然发散”的状态，先固定三条约束：

1. 本 plan 是路线收口 plan，不建议直接进入 `develop` 执行；后续实现必须拆成更窄的 implementation plan。
2. 当前已存在的 `helloagents-integration-enhancements` 应收窄为 `registry + status/doctor + README matrix`，不继续外扩宿主或命令面。
3. 下一条最值得新建的实现 plan 不是子智能体编排，也不是分发，而是 `develop-quality-loop`。

## Steering Plan 收口条件

本 plan 不是通过“代码已完成”来收口，而是通过“后续实现入口已清晰”来收口：

1. `helloagents-integration-enhancements` 已被收窄到当前真实范围；
2. `develop-quality-loop` 已形成独立 plan 包；
3. 规划顺序与实施顺序已被明确写入文件，不再依赖聊天上下文解释。
