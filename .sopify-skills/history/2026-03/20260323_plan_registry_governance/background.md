# 变更提案: plan registry 治理层（`plan-registry-governance`）

## 需求背景

当前 Sopify 已经支持在 `plan/` 下生成多个独立方案包，但 runtime 真正绑定的执行真相仍然只有一个 `current_plan`。

这带来三个现实问题：

1. 用户可以先通过 `plan` 模式生成多个需求方案包，但缺少统一的项目级治理视图
2. `blueprint/` 负责长期蓝图，不适合承载“多个当前 plan 的优先级与状态”
3. 如果后续要做“建议先看哪个 plan”或“确认后切换到某个 plan”，当前没有稳定的中间层

因此，本轮不引入自动消费，而是先补一层轻量的 `plan registry`：

1. 自动登记已有和新生成的 plan
2. 自动维护 plan 的结构化快照
3. 自动给出基于现有 plan 上下文的优先级建议
4. 把优先级最终确认权保留给用户
5. 为后续建议与确认式消费预留稳定边界

评分:
- 方案质量: 9.5/10
- 落地就绪: 9.0/10

评分理由:
- 优点: 把“系统建议优先级”和“用户最终优先级”拆开后，治理边界与解释链更完整，可在不破坏 `current_plan` 的前提下补齐多 plan 治理层
- 扣分: 第一版仍是最终一致模型，且建议优先级依赖启发式规则，短期内更像治理基础设施而不是强产品功能

## 变更内容
1. 在 `.sopify-skills/plan/` 下新增 `_registry.yaml` 作为多 plan 治理层
2. 定义 `plan`、`registry`、`current_plan` 三层职责与字段归属
3. 引入 create/finalize 事件同步与读取时 reconcile
4. 将优先级模型收敛为“系统给建议值，用户确认后生效”
5. 为后续只读建议与确认式消费保留阶段化演进路径

## 影响范围
- 模块: `runtime/plan_scaffold.py`、`runtime/finalize.py`、新增 `runtime/plan_registry.py`、可能扩展 `runtime/output.py`、测试与 README
- 文件: `runtime/*.py`、`.sopify-runtime/tests/test_runtime.py`、`README.md`

## 风险评估
- 风险: `registry` 与单个 `plan` 同时存在后，若字段边界不清晰，会演变成第二份 plan 真相
- 缓解: 仅把 `title/level/path/topic_key/lifecycle_state` 视为快照字段；把 `suggested_priority` 与 `priority` 明确分层；执行态仍只认 `current_plan`
