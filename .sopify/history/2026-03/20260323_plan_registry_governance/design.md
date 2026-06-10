# 技术设计: plan registry 治理层（`plan-registry-governance`）

## 设计目标

在不破坏现有 `current_plan` 单执行真相的前提下，为 `plan/` 下多个并存方案包补齐一层项目级治理能力：

1. 自动登记 plan，而不是要求用户手工维护总表
2. 自动对齐 plan 的结构化快照，而不是复制正文内容
3. 优先级由系统给出建议值，但最终由用户确认
4. `registry` 可以参与观察、建议和候选排序，但不能越权替代 runtime 执行态

## 名词与边界

### 1. `plan` 包

表示单个需求的方案内容与固有元数据。

由 plan 自身负责的字段：

- `plan_id`
- `title`
- `level`
- `path`
- `topic_key`
- `created_at`
- `lifecycle_state`

### 2. `plan registry`

表示多 plan 的治理层，不是项目蓝图，也不是执行真相。

职责：

- 聚合多个 plan 的结构化快照
- 保存跨 plan 的治理信息
- 作为后续建议和确认式消费的候选来源

### 3. `current_plan`

表示 runtime 当前绑定的执行对象。

约束：

- 仍然是唯一 machine-active plan
- 任何真正的切换都必须通过 runtime 发生
- registry 不能直接写执行态

## 为什么不放进 blueprint

`blueprint/` 负责项目长期蓝图，例如目标、约束、架构边界、长期任务。

本设计中的 registry 负责的是：

- 当前有哪些 plan
- 哪些 plan 还在活动池
- 每个 plan 的治理状态与优先级

因此它必须留在 `plan/` 层，而不是落入 `blueprint/`。

## 文件位置与结构

固定位置：

```text
.sopify-skills/plan/_registry.yaml
```

建议结构：

```yaml
version: 1
mode: observe_only
selection_policy: explicit_only
priority_policy: heuristic_v1
priority_fallback: p2

plans:
  - plan_id: 20260323_plan_registry_governance

    snapshot:
      path: .sopify-skills/plan/20260323_plan_registry_governance
      title: plan registry 治理层
      level: standard
      topic_key: plan-registry-governance
      lifecycle_state: active
      created_at: 2026-03-23T09:45:00+08:00

    governance:
      priority: null
      priority_source: null
      priority_confirmed_at: null
      status: todo
      note: ""

    advice:
      suggested_priority: p2
      suggested_source: heuristic_v1
      suggested_reason:
        - 当前 active plan 未完成
        - 新 plan 未出现明确紧急信号
      suggested_at: 2026-03-23T09:45:00+08:00

    meta:
      source: runtime_auto
      updated_at: 2026-03-23T09:45:00+08:00
```

## 字段归属

### 1. plan 真相字段

这些字段来自 plan 创建或 plan 文档元数据：

- `plan_id`
- `snapshot.title`
- `snapshot.level`
- `snapshot.path`
- `snapshot.topic_key`
- `snapshot.lifecycle_state`
- `snapshot.created_at`

### 2. registry 治理字段

这些字段只在 registry 里维护，且以用户确认值为准：

- `governance.priority`
- `governance.priority_source`
- `governance.priority_confirmed_at`
- `governance.status`
- `governance.note`

### 3. registry 建议字段

这些字段表示系统生成的只读建议，可刷新但不直接等于最终真相：

- `advice.suggested_priority`
- `advice.suggested_source`
- `advice.suggested_reason`
- `advice.suggested_at`

### 4. 执行态字段

以下不进入 registry 真相：

- `current_plan`
- handoff / checkpoint / execution gate 状态

## 同步模型

本设计使用“事件同步 + 懒校准”的最终一致模型，而不是强实时双写。

### 1. create 事件

触发点：`create_plan_scaffold(...)` 成功返回 `PlanArtifact` 后。

动作：

1. 若 `_registry.yaml` 不存在，则先创建最小骨架
2. 按 `plan_id` 执行 `upsert`
3. 写入 `snapshot.*`
4. 写入初始治理字段：
   - `priority = null`
   - `priority_source = null`
   - `priority_confirmed_at = null`
   - `status = todo`
5. 根据已有 plan、`current_plan` 与请求信号计算建议优先级：
   - `suggested_priority`
   - `suggested_source = heuristic_v1`
   - `suggested_reason`
   - `suggested_at`

约束：

- 不自动切换 `current_plan`
- 不自动推断依赖关系

### 2. finalize 事件

触发点：`finalize_plan(...)` 成功后。

动作建议：

1. 把对应条目标记为 `snapshot.lifecycle_state = archived`
2. 更新 `snapshot.path` 为 `history/` 下的新路径
3. 默认把条目从活动池中移除，或保留到独立归档区

第一版建议：

- 直接从 `plans` 活动列表移除，避免活动池长期堆积
- 归档事实仍由 `history/` 与 plan 本身承担

### 3. 读取时 reconcile

触发点：

- 读取 registry
- 输出建议
- 进入确认式消费前

动作：

1. 读取对应 plan 文档
2. 对齐以下确定性字段：
   - `snapshot.title`
   - `snapshot.level`
   - `snapshot.path`
   - `snapshot.topic_key`
   - `snapshot.lifecycle_state`
3. 生成读时 `drift_notice`

约束：

- 不能覆盖任何 `governance.*`
- `advice.*` 可以按启发式刷新
- `drift_notice` 只作为读时诊断结果，不建议持久化为主数据

## priority 模型

### 1. 建议优先级

第一版不把系统输出直接当作最终优先级，而是先生成建议优先级。

写入字段：

- `advice.suggested_priority`
- `advice.suggested_source = heuristic_v1`
- `advice.suggested_reason`
- `advice.suggested_at`

建议优先级依据：

- 当前是否已有 `current_plan`
- 当前已有 plan 的数量与状态
- 用户当前请求中是否存在明显紧急信号，例如“紧急 / 阻塞 / 先做 / 必须今天”
- 是否与已有 plan 明显重复

回退策略：

- 若启发式无法给出强信号，则回退到 `priority_fallback = p2`

### 2. 用户确认

一旦用户确认或修改某个 plan 的优先级：

- 更新 `governance.priority`
- 更新 `governance.priority_source = user_confirmed`
- 更新 `governance.priority_confirmed_at`

约束：

- 后续 reconcile 不能覆盖已确认的优先级
- 后续排序阶段，`user_confirmed` 权重高于未确认建议值

### 3. 为什么不自动决定业务优先级

因为第一版并没有稳定的业务价值、依赖关系、时效性输入源。

如果直接自动决定业务优先级，会让系统在缺少事实的情况下越权。

因此本设计把优先级收敛为：

- 系统给建议值
- 用户拥有最终确认权
- registry 负责持久化最终结果

## 建议与消费的阶段演进

### Phase 0 | Schema & Ownership

- 定义 registry schema
- 固定字段归属与覆盖规则

### Phase 1 | Event Sync

- 接入 create/finalize 事件
- 完成自动 upsert/remove
- 支持 registry 缺失时 backfill

### Phase 2 | Reconcile & Drift Visibility

- 增加读取时 reconcile
- 增加 `drift_notice`

### Phase 3 | Suggestion With Reasons

根据：

- `governance.priority`
- `governance.priority_source`
- `advice.suggested_priority`
- `status`
- `current_plan`

输出只读建议，例如：

- 已确认高优先级且未阻塞，建议先看
- 当前 active plan 未完成，不建议切换
- 尚未确认时，先按 `suggested_priority` 排序
- 已确认优先级高于建议优先级

约束：

- 只输出候选与理由
- 不直接改 registry
- 不直接切执行态

### Phase 4 | Confirmed Routing

registry 只负责：

- 提供候选
- 提供排序
- 提供解释理由

runtime 负责：

- 用户确认后的真正执行切换
- 更新 `current_plan`
- 保持 handoff / execution gate 契约

## inspect-only 宿主消费约定

第一版宿主接入只要求消费 `inspect` 摘要，不要求默认暴露 `_registry.yaml` 原文。

默认约定：

- 宿主通过 `plan_registry_runtime.py inspect` 读取摘要 contract
- 默认展示字段仅限：
  - `current_plan`
  - `selected_plan`
  - `recommendations`
  - `drift_notice`
  - `execution_truth`
- 默认挂载场景仅限 review，不进入 develop / execute 主链
- `_registry.yaml` 原文默认仅高级用户可访问

推荐交互：

- `确认建议`
- `改成 P1`
- `改成 P2`
- `改成 P3`
- `暂不确认`

交互约束：

- 只有用户显式动作后，宿主才允许调用 `confirm-priority`
- `note` 为可选字段
- 成功后刷新当前卡片并保持 review 上下文
- 不自动执行
- 不自动切换 `current_plan`

失败与降级：

- `inspect` 失败时允许隐藏该治理卡片，不阻断主 review 流程
- `confirm-priority` 失败时只提示可重试错误，不进入执行切换

## 非目标

本轮明确不做：

- 不把 registry 变成第二份 plan 文档
- 不把 `background/design/tasks` 正文写进 registry
- 不自动切换 `current_plan`
- 不在第一版引入 `depends_on / blocked_by / risk_score`
- 不把 registry 放进 `blueprint/`

## 实现切片建议

### Slice 1

- 新增 `runtime/plan_registry.py`
- 支持 load / save / upsert / remove / ensure / backfill

### Slice 2

- 在 plan scaffold 成功路径后自动 upsert
- 在 finalize 成功路径后自动 remove 或 archive

### Slice 3

- 实现 registry 读取时 reconcile
- 生成 `drift_notice`

### Slice 4

- 增加建议优先级与用户确认路径
- 在输出摘要中提示 `suggested_priority = ... (待用户确认)`

### Slice 5

- 增加只读建议能力
- 后续再接确认式消费
