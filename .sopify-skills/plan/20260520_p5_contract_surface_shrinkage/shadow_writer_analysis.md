# P5 S2.1: Shadow Writer Gap Analysis

> 分析 5 个 candidate-kernel writer 面，判断非 deep host 是否可产出等价 canonical state。
> 基于 runtime/handoff.py, runtime/state.py, runtime/decision.py, runtime/clarification.py 代码分析。

---

## 结论: B（部分可行）

非 deep host **不能**等价替代 builder 逻辑（~460 LOC），**可以**等价替代 IO/提交逻辑（~220 LOC）。

候选内核从 ~680 LOC 收缩至 **~210 LOC**（仅 StateStore）。

---

## 逐面分析

### 2.1 handoff.py — build_runtime_handoff (~230 LOC)

**函数签名**: `build_runtime_handoff(*, config, decision, run_id, resolved_context, current_plan, kb_artifact, skill_result, notes) -> RuntimeHandoff | None`

**依赖链**:
- `resolved_context` — engine 的单快照语义（禁止重读，防 split-brain）
- `_collect_handoff_artifacts()` — 从 entry_guard, deterministic_guard, action_projection, resolution_planner, sidecar_classifier, vnext_phase, develop_quality, archive_lifecycle 等 10+ 个 engine 子系统收集产物
- `_should_emit_handoff()` — 路由级 gate 策略
- `required_host_action` — 从 route + run state 推导

**Shadow Writer 可行性**: ❌ **不可行**
- 9 个输入参数中有 6 个只在 engine 执行上下文中存在
- artifact 收集涉及 10+ 个 engine 子系统，不可独立重建
- 单快照语义是 engine 的 consistency guarantee，shadow writer 无法保证

**P5 裁定更新**: ~~keep-candidate-kernel~~ → **keep-deep-only**

---

### 2.2 handoff.py — write_runtime_handoff (~10 LOC)

**函数签名**: `write_runtime_handoff(path: Path, handoff: RuntimeHandoff) -> None`

**行为**: 原子 JSON 写入（NamedTemporaryFile + replace）

**Shadow Writer 可行性**: ✅ IO 操作本身可复制
- 但它被 `set_host_facing_truth()` 包裹，该方法同时写 run + handoff 并盖 resolution_id
- 脱离 engine 调用此函数会破坏 paired write consistency

**P5 裁定更新**: ~~keep-candidate-kernel~~ → **keep-deep-only**（IO 可复制但 coordination 不可复制）

---

### 2.3 state.py — StateStore get/set/clear (~210 LOC)

**核心方法**:
- `set_current_run()` / `set_current_handoff()` / `set_current_decision()` / `set_current_clarification()` — 单文件原子写入
- `set_host_facing_truth()` — paired write（run + handoff + resolution_id stamping）
- `reset_active_flow()` — 多文件协调清理
- `set_current_decision_submission()` / `set_current_clarification_response()` — 用户响应合并

**一致性保障**:
- 单文件原子（temp + replace）
- paired truth 约束（resolution_id 必须匹配，truth kind 白名单）
- phase 校验（clarification 仅 analyze/develop，decision 仅 design/develop/execution_gate）
- provenance stamping（observability, owner_session_id, owner_run_id）

**Shadow Writer 可行性**: ⚠️ **部分可行**
- 单文件写入：可以（如果完全匹配 schema）
- 但失去：paired write 原子性、phase 校验、provenance 一致性、多文件协调
- 这是所有 writer 面中**最有提取价值的一块**——如果 P6 要做 extractable kernel，StateStore 就是核心

**P5 裁定更新**: **保持 keep-candidate-kernel**

---

### 2.4 decision.py — build_* 构建器 + submission writer (~180 LOC)

**构建器**:
- `build_decision_state(route, *, config)` — 从路由 + 策略匹配构建
- `build_execution_gate_decision_state(route, *, gate, current_plan, config)` — 执行门控决策
- `build_active_plan_binding_decision_state(route, *, current_plan, config)` — 活跃 plan 绑定决策

**依赖链**:
- `match_decision_policy(route)` — 策略匹配（engine 内部）
- `resolve_context_profile(...)` — 上下文 profile 解析
- `ExecutionGate` / `PlanArtifact` — engine 运行时产物
- 状态转换：pending → collecting → confirmed → consumed → stale（由 engine 编排）

**Shadow Writer 可行性**: ❌ **不可行**
- 3 个 builder 函数全部依赖 engine 内部产物
- execution_gate_decision 尤其脆弱——需要 gate reason + current plan + current run
- 策略匹配逻辑嵌入 engine 路由上下文

**P5 裁定更新**: ~~keep-candidate-kernel~~ → **keep-deep-only**

---

### 2.5 clarification.py — build_clarification_state + stale transition (~50 LOC)

**构建器**: `build_clarification_state(route, *, config) -> ClarificationState | None`

**依赖链**:
- `route.request_text` — 来自 engine 路由
- missing-facts 推断逻辑
- `resolve_context_profile(..., profile="clarification")` — engine 内部

**stale transition**: `stale_clarification(state) -> ClarificationState` — engine 在新请求覆盖旧 clarification 时调用

**Shadow Writer 可行性**: ⚠️ **技术上可行但无价值**
- 最简单的 builder，仅依赖 request_text + language + facts 推断
- 但实际场景中非 deep host 不需要主动创建 clarification——它只需要回答现有的

**P5 裁定更新**: ~~keep-candidate-kernel~~ → **keep-deep-only**（非 deep host 无创建需求）

---

## 汇总：5 面裁定更新

| 面 | 原裁定 | Shadow Writer | 更新裁定 | LOC |
|----|--------|--------------|---------|-----|
| 2.1 build_runtime_handoff | candidate-kernel | ❌ 不可行 | **keep-deep-only** | ~230 |
| 2.2 write_runtime_handoff | candidate-kernel | ✅ IO 可复制，coordination 不可 | **keep-deep-only** | ~10 |
| 2.3 StateStore get/set/clear | candidate-kernel | ⚠️ 部分可行 | **keep-candidate-kernel** | ~210 |
| 2.4 decision build_* + writer | candidate-kernel | ❌ 不可行 | **keep-deep-only** | ~180 |
| 2.5 clarification build + stale | candidate-kernel | ❌/⚠️ 技术可行但无需求 | **keep-deep-only** | ~50 |

**candidate-kernel 从 ~680 LOC → ~210 LOC**（仅 StateStore）

---

## Canonical Writer Authority 轴建模建议

### 结论：当前不需要独立建模

理由：
1. **写入需求分析**：非 deep host 的核心需求是**读取** canonical state（P4d 已验证），不是写入
2. **Builder 依赖**：4/5 writer 面的 builder 逻辑深度耦合 engine 内部，无法脱离 engine 独立运行
3. **提交路径已有机制**：用户对 decision/clarification 的响应通过 bridge scripts 提交，这是 deep host 的 CLI 交互层，不是 canonical state production
4. **覆盖方式**：当前 "deep_verified = full read+write, 其他 = read-only" 的隐式规则，可通过 protocol 声明式规则 + Validator 校验覆盖，不需要新的正交轴

### 如果 P6 需要 extractable kernel

唯一需要提取的是 **StateStore ~210 LOC**——它是 canonical state 的 IO 层。但提取它的前提是存在一个 "轻量 runtime"（lighter engine），而不是让非 deep host 直接写文件。

这意味着 canonical writer authority 不是 "谁能写" 的问题（答案始终是 "引擎"），而是 "哪个引擎" 的问题（full engine vs extracted kernel engine）。这是 P6 的设计决策，不是 P5 的建模需求。

---

## 对 S3 Provisional 裁定表的影响

需更新 provisional_adjudication.md：

1. §2 candidate-kernel 从 5 面缩减到 1 面（StateStore ~210 LOC）
2. §2 中 4 面降级到 §3 deep-only
3. §5 汇总表更新
4. §6a pending-shadow-writer 清单更新为 "evidence resolved"
5. 所有 pending-shadow-writer → ready（Shadow Writer = B，裁定已确定）
