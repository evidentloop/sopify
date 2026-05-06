# Receipt: P1.5-C Plan Materialization Authorization Boundary

outcome: passed
date: 2026-05-05

## Summary

Plan 包物化从 route 隐式触发改为受 ActionProposal → Validator 授权约束。`plan_package_policy` 默认值从 `immediate` 改为 `authorized_only`，消除了分析/咨询类请求直接落盘生成 plan 包的问题。合入 main（PR #23, commit e07ba26, merge 0590baf）。

## Key Decisions

1. `PLAN_PACKAGE_POLICIES` 替换为 `("none", "immediate", "authorized_only")`，删除历史值 `confirm`（D1/D7）
2. `_plan_package_policy_for_route` 默认值改为 `authorized_only`（D1）
3. `_normalized_plan_package_policy` 去掉兜底 `immediate`，缺省/空返回 `"none"`（D2）
4. 未授权时降级到 consult surface，不触发写盘操作（D3）
5. `~go plan` 显式命令保持 `immediate`——本轮显式兼容例外，不上升为一般原则（D6）
6. Router `_ACTION_KEYWORDS` 移除单字"修"和"补"止血 consult 误判（D5）

## Verification

- 全量 pytest：597 tests passed, 46 subtests passed
- 无授权时不创建 plan 目录
- `~go plan` 命令不受影响
- "批判看下哪些必须修，等我确认" 不再命中 action keyword

## Known Debt

- resume path `plan_materialization_authorized=True` 写死（3 处）——当前上游保证安全，但 contract 本身没绑定 authorization provenance。留给 P1.5-B / P2 收敛。

## Impact on Blueprint

- tasks.md: P1.5-C 标记完成，B 前置条件已满足
- design.md: 无变更
- protocol.md: 无变更
