# Receipt: P2 Local Action Contracts — Admission Closure

outcome: passed
date: 2026-05-07

## Summary

P2 闭合局部动作 admission contract。在 P1 subject binding + P1.5 授权脊柱基础上，完成三层收口：

1. **Subject binding 泛化** — modify_files / checkpoint_response 纳入 bound-subject actions（缺 plan_subject → REJECT）；cancel_flow 条件性 binding
2. **side_effect_delta schema** — modify_files 可选携带 file-level 变更清单（workspace scoping by validator）
3. **Action-effect canonical pairing** — 每个 action_type 有且仅有一个合法 side_effect，不匹配 → REJECT

Gate schema 同步（canonical_for 映射）消除宿主侧 contract drift。合入 main（PR #28, merge commit 4174490）。

## Key Decisions

1. D9: 1:1 canonical pairing，mismatch → hard REJECT（不 downgrade）。防止 action_type 退化为纯标签
2. D10: side_effect_delta = [] 归一化为 None。空列表 ≠ "声明无变更"
3. D11: P2 scope = admission contract only。Execution routing 收敛属 P3a

## Verification

- 670 tests passed, 0 regression
- 11 新增测试（10 pairing + 1 schema canonical_for）
- 3 个假覆盖测试修复（原命中 bound_subject_missing 而非 pairing）
- 之前合法的危险组合（modify_files+none, checkpoint_response+execute_command, cancel_flow+write_files）全部 REJECT

## Impact on Blueprint

- protocol.md: §7 Applicability Matrix 增 canonical side_effect 列
- design.md: 新增 Action-Effect Canonical Pairing 段落 + P2 scope 边界声明
- tasks.md: P2 更新 + P3a execution routing 收敛护栏
