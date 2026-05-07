# Tasks: P3a Contract-Aligned Surface Cleanup

## 执行切片顺序

```
A0: 文档矛盾收口（本次已完成）
 ↓
A: review_or_execute_plan 最终删除（9 py + 2 yaml + 3 schema.json = 14 runtime targets）
 ↓
B: Execution routing 收敛（validator AUTHORIZE → deterministic route）
 ↓
C: Runtime 减重（dead path pruning, 目标 26K→<20K）

D: knowledge_sync audit trail（独立尾项，不与 A/B/C 绑死）
```

## Phase A: `review_or_execute_plan` 最终删除

- [ ] A1: 逐文件删除 `review_or_execute_plan` 引用（9 py files + 2 yaml contracts + 3 schema.json），每文件确认语义替代已到位
- [ ] A2: 删除 `contracts/failure_recovery_table.yaml`、`contracts/decision_tables.yaml` 中对应 entry；删除 `contracts/failure_recovery_table.schema.json`、`contracts/decision_tables.schema.json`、`contracts/signal_priority_table.schema.json` 中 enum 值
- [ ] A3: 添加 fail-closed 测试：state 中残留 `review_or_execute_plan` → state_conflict / inspect-required
- [ ] A4: 删除或改写 tests 中仅验证 `review_or_execute_plan` 旧行为的 test cases（allowlist 外的引用全部清除）
- [ ] A5: 验证 grep 门：`runtime/` 和活跃 `.sopify-skills/blueprint/` 零引用；`tests/` 仅 allowlist 内 fail-closed / compatibility coverage 保留
- [ ] A6: 全量测试通过

## Phase B: Execution routing 收敛

- [ ] B1: 实现 `_derive_route_from_authorized_proposal()` in engine.py
- [ ] B2: 提取 `_estimate_complexity()` 为 router.py 公开函数（供 B1 消费）
- [ ] B3: engine.py L712-715 三路分支改写（proposal_override / derive / router.classify fallback）
- [ ] B4: 添加路由收敛测试（每个 action_type → 预期 route_name + 元数据；验证不依赖 Router.classify 做主判定）
- [ ] B5: 添加 modify_files complexity 回归测试（simple/medium/complex 三级，仅经 _estimate_complexity helper）
- [ ] B6: 添加 checkpoint_response 分流测试（clarification_resume / decision_resume 仅 active 状态；confirmed/cancelled/timed_out → REJECT）
- [ ] B7: 添加 propose_plan 端到端回归测试（断言最终 runtime result：plan_artifact.level 覆盖 full/standard/light + handoff 与旧行为一致；不依赖新 schema 字段）
- [ ] B8: 裸文本请求回归测试（确认 Router.classify 仍正常工作）
- [ ] B9: 全量测试通过

## Phase C: Runtime 减重

- [ ] C1: 基于 A/B 后的 dead code analysis，列出模块级删除清单
- [ ] C2: 执行删除（每模块单独确认测试通过）
- [ ] C3: decision_tables.py 裁剪旧 route/action entries
- [ ] C4: deterministic_guard.py 裁剪已删 surface 的 guard entries
- [ ] C5: context_snapshot.py 裁剪只服务已删 route 的逻辑
- [ ] C6: 验证 LOC < 20K
- [ ] C7: 全量测试通过

## Phase D: knowledge_sync audit trail（尾项）

- [ ] D1: 评估 archive finalize 路径是否允许零成本挂接
- [ ] D2: 如可行：追加 knowledge_sync_result 写入逻辑 + receipt 模板更新 + 测试
- [ ] D3: 如需重构 finalize 路径：defer 到 P3b，标记为 out-of-scope

## Blueprint 同步

- [ ] E1: design.md sunset 表标记 `review_or_execute_plan` 为 ✅ 已完成
- [ ] E2: tasks.md P3a 更新完成状态
- [ ] E3: protocol.md §7 如有 `review_or_execute_plan` 引用则清理

## 完成标准

- 全量测试通过（670+ tests, 0 regression）
- grep `review_or_execute_plan` 在 `runtime/` 和活跃 `.sopify-skills/blueprint/` = 0 hits（排除 history/ 和 CHANGELOG.md）
- grep `review_or_execute_plan` 在 `tests/` 仅限 fail-closed / compatibility coverage allowlist 内保留
- Authorized ActionProposal 不再依赖 Router.classify() 做主路由判定（modify_files 仅经提取后的 complexity helper）
- propose_plan 最终 runtime result 可观察行为与旧路径一致（plan_artifact.level + handoff），不只验证 derive 中间值
- checkpoint_response 正确分流到 clarification_resume / decision_resume（仅 active 状态 {"pending","collecting"} 可 resume；terminal 状态 → REJECT）
- runtime/*.py LOC < 20,000
- D（knowledge_sync）按实际成本决定是否进入本里程碑
