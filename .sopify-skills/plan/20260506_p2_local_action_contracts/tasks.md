# 执行清单: P2 Local Action Contracts on Bound Subjects

## Slice A: 蓝图 Spec（串行前置）

- [ ] A1: protocol.md:250 修正 — "side-effecting" → "bound-subject side-effecting"
- [ ] A2: protocol.md:272-298 Subject Binding 段扩展 — 从 execute_existing_plan 扩到所有 bound-subject actions + cancel_flow 条件性
- [ ] A3: protocol.md 新增 Action Applicability Matrix（或引用 design.md 定义）
- [ ] A4: design.md 补充 side_effect_delta schema 定义（仅 modify_files 消费；与标量 side_effect 的关系、默认、scoping 规则）
- [ ] A5: design.md 补充 P2 → P3a 衔接说明（替代 contract 已落地，P3a 执行清理）

## Slice B: Runtime 最小实现（依赖 Slice A）

- [ ] B1: action_intent.py — 定义 BOUND_SUBJECT_ACTIONS / SUBJECT_CAPABLE_ACTIONS / DELTA_CAPABLE_ACTIONS 常量 + 放宽 parser plan_subject 约束
- [ ] B2: action_intent.py — 新增 side_effect_delta 解析（枚举、字段、to_dict / from_dict）；parser 只做 shape + enum，不做 workspace scoping
- [ ] B3: action_intent.py — _validate_plan_subject 泛化：BOUND_SUBJECT_ACTIONS → REJECT on missing；cancel_flow → validate if present, no reject if absent
- [ ] B4: action_intent.py — 新增 _validate_side_effect_delta（workspace scoping：no absolute path, no ..）；仅对 DELTA_CAPABLE_ACTIONS 调用
- [ ] B5: action_intent.py — validate() 主路径集成 bound-subject admission + delta workspace scoping
- [ ] B6: tests — BOUND_SUBJECT_ACTION × plan_subject 状态 parametrized tests + cancel_flow 条件性 binding tests
- [ ] B7: tests — side_effect_delta parser（shape/enum/wrong action_type） + validator（workspace scoping）tests
- [ ] B8: 全量回归 — 632 tests 无 regression

## 验收标准

- BOUND_SUBJECT_ACTIONS（execute_existing_plan / modify_files / checkpoint_response）缺 plan_subject 时 validator 返回 REJECT
- cancel_flow 缺 plan_subject 时不 REJECT；提供时走全套 admission check
- plan_subject 的全部 admission 检查（绝对路径 / 穿越 / 前缀 / 存在性 / digest）对所有 subject-capable actions 生效
- side_effect_delta 的 workspace scoping 对 modify_files 的 delta 生效（validator 层）
- 非 DELTA_CAPABLE_ACTIONS 的 action 携带 delta → parser 拒绝
- Legacy actions（consult_readonly / propose_plan / archive_plan）不受影响
- 632+ tests 通过，无 regression
