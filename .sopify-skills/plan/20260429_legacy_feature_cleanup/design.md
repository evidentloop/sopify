# Design: Legacy Feature Cleanup

> **定位**：`20260424_lightweight_pluggable_architecture` 总纲的独立清理包。
> **前置**：`20260428_action_proposal_boundary` P0 thin slice 已完成，ActionProposal validator 作为正式保护层替代了 legacy keyword classifier。
> **目标**：清除被 ActionProposal 替代的 legacy 代码路径和已废弃的 `~compare` 功能模块，降低维护面。

---

## 范围

### 1. `explain_only_override` 删除

**现状**：
- 两个 callsite：
  - `router.py` classify chain（`_classify_explain_only_override`）
  - `engine.py` plan materialization bypass（`plan_package_policy == "confirm"` 时跳过物化）
- 5 个测试：3 in `test_runtime_router.py`、2 in `test_runtime_sample_invariant_gate.py`
- ActionProposal pre-route interceptor 在 `explain_only_override` 之前就已拦截 `consult_readonly` 请求，使其成为 dead code（对新 host）

**删除策略**：
1. 删除 `router.py` 中 `_classify_explain_only_override` 函数及其在 classify chain 的调用
2. 删除 `engine.py` 中对应的 plan materialization bypass 分支
3. 删除 5 个关联测试
4. 确认不影响 `analysis_only_no_write_brake`（保留，作为信号层）

**风险**：中等。engine.py callsite 有独立刹车逻辑（`plan_package_policy == "confirm"`），删除前需确认该分支仅服务于 explain_only_override 路由。

### 2. `~compare` 模块移除

**现状**：
- `scripts/model_compare_runtime.py`：~1015 行
- `runtime/compare_decision.py`：~179 行
- router.py 中 13 处引用、engine.py 中 10 处引用、gate.py 1 处引用
- 提示层（Codex/SKILL.md 等）中的 `~compare` 命令定义
- cross-review 已作为独立验证/对比方案替代 `~compare` 的核心场景

**删除策略**：
1. 删除 `scripts/model_compare_runtime.py` 和 `runtime/compare_decision.py`
2. 清理 router.py / engine.py / gate.py 中所有 `~compare` 路由和引用
3. 清理提示层中 `~compare` 命令定义和文档
4. 清理 `sopify.config.yaml` 模板中 `multi_model.*` 配置项
5. 删除关联测试

**风险**：低-中。删除面广（~1200 行 + 引用），但都是独立模块，无共享依赖。

---

## 执行顺序

1. `explain_only_override` 先行（blast radius 更小，验证删除流程）
2. `~compare` 后续（文件量大但逻辑独立）
3. 每步后跑全量测试确认无回归

## 不做

- 不删除 `analysis_only_no_write_brake`（保留作为信号层）
- 不动 `_is_consultation()` 或其他共享 helper
- 不做 prompt governance（独立方案包）
