# 技术设计: runtime 并发 review 隔离与 soft ownership（`runtime-session-lease-session-scoped-review-stat`）

## 设计目标

在不放弃“单一 execution truth”的前提下，用最小改动解决同一 workspace 中多个宿主会话并行 review / planning 时的互踩问题：

1. review state 按 session 隔离
2. execution state 保持全局唯一
3. global execution truth 写入时带 soft ownership 标记，但不阻断
4. 老宿主可以渐进兼容，不需要一次性升级全部桥接代码

## 关键名词

### 1. Session Review State

表示某个宿主会话在当前 workspace 内的评审态机器真相，包括：

- `current_run`
- `current_plan`
- `current_handoff`
- `current_clarification`
- `current_decision`
- `last_route`

它服务于 `plan_only / workflow / clarification / decision` 等 review 阶段，不等于全局 execution truth。

### 2. Global Execution Truth

表示整个 workspace 当前真正处于执行主线的 plan 与 handoff。

第一阶段为了兼容现状，继续使用根级 `.sopify-skills/state/current_*.json` 表达，不立即迁移目录。

### 3. Soft Ownership

表示某次 global execution truth 写入是由哪个 session 触发的观测信息，不参与阻断，也不引入锁。

### 4. Plan Registry

继续是 observe-only 的治理层，用于候选观察与优先级确认；不负责 execution truth 切换。

## 不变式

1. 同一时刻允许存在多个 session review state
2. 同一时刻只允许存在一个 global execution truth
3. `~go finalize` 继续只消费 global active plan
4. 本轮不新增 blocking ownership 机制
5. execution / finalize 的恢复与写入继续以根级 global state 为准

## 状态布局

### Phase 1 布局

```text
.sopify-skills/state/
├── current_plan.json              # global execution truth（保留兼容）
├── current_run.json               # global execution truth（保留兼容）
├── current_handoff.json           # global execution truth（保留兼容）
├── current_clarification.json     # 仅 legacy/global fallback 使用
├── current_decision.json          # 仅 legacy/global fallback 使用
└── sessions/
    └── <session_id>/
        ├── current_plan.json
        ├── current_run.json
        ├── current_handoff.json
        ├── current_clarification.json
        ├── current_decision.json
        └── last_route.json
```

### 兼容策略

- 无 `session_id` 的旧宿主继续走 legacy/global 路径
- 传入 `session_id` 的新宿主，review 路由优先读写 `sessions/<session_id>/`
- global execution 相关路由继续使用根级 `current_*`

## 路由归属规则

核心规则收敛为两类：

### Session Review Routes

默认全部走 session state，包括：

- `plan_only`
- `workflow`
- `light_iterate`
- `clarification_pending`
- `clarification_resume`
- `decision_pending`
- `decision_resume`
- `consult`
- `replay`
- `quick_fix`

### Global Execution Routes

只有少量真正依赖 global execution truth 的路由继续走根级状态：

- `execution_confirm_pending`
- `resume_active`
- `exec_plan`
- `finalize_active`

实现建议：

- 用一个 `GLOBAL_EXECUTION_ROUTES` 集合表达，不为每个路由单独设计状态模型
- `Router` 主要基于 session state 做 pending 判断
- 只在 execution confirm / resume / finalize 相关分支额外读取 global state
- `quick_fix` 仍放在 session review 侧；它触发的宿主代码修改冲突不在本方案范围内

## `session_id` 透传

### 输入来源

- 宿主可显式传入 `--session-id <id>`
- 若宿主未传入，gate 自动生成一个新的 `session_id`
- gate 通过 stdout contract 与 session receipt 回传 `session_id`
- 宿主在同一窗口/会话续轮时复用该 `session_id`

### 透传链路

`runtime_gate.py -> runtime.gate.enter_runtime_gate -> run_runtime -> StateStore / Router / Handoff observability`

### 记录要求

- gate receipt 记录 `session_id`
- `current_run.observability`
- `current_handoff.observability`
- decision / clarification state

## StateStore 设计

不引入 `scope` 参数，保持接口尽量不变，只改路径解析：

```text
StateStore(config)                    # global root
StateStore(config, session_id="...") # review root
```

建议行为：

1. `session_id is None` 时，所有路径保持当前根级行为
2. `session_id` 存在时：
   - review state 文件读写 `state/sessions/<session_id>/`
   - global execution truth 仍通过单独的 global store 访问
3. 对外 API 尽量保持现有 `get/set/clear/reset` 形状，避免全链路大改

这样 engine 内部只需要同时维护两个 store：

- `review_store = StateStore(config, session_id=session_id)`
- `global_store = StateStore(config)`

## `cancel_active` 语义

`cancel_active` 不再简单归类为“总是 session”或“总是 global”，而是按当前活跃事实来源分流：

1. 若 global store 中存在 execution 主线（如 `ready_for_execution / execution_confirm_pending / develop_pending / executing / finalize_active` 相关状态），`cancel_active` 清 global execution truth
2. 否则若当前 session review store 中存在 pending clarification / decision / plan review 状态，则只清该 session 的 review state
3. 两侧都存在时，优先清 global，并在 note 中明确“global execution cancelled; session review state preserved”

这样可以兼容两种意图：

- “取消我这个窗口里的 review”
- “取消当前已经进入执行确认/执行中的全局 plan”

## Context Recovery 设计

这里不重写 `recover_context()` 的主体逻辑。

原因：

- `recover_context()` 本身只是消费传入的 `state_store`
- 只要 engine 在调用时传入正确的 store，恢复结果就天然隔离

因此最小改法是：

- review routes 调 `recover_context(..., state_store=review_store)`
- global execution routes 调 `recover_context(..., state_store=global_store)`

需要单独补的不是 `recover_context()` 本体，而是 engine / router 选择哪一个 store 的逻辑。

## Soft Ownership 设计

### 目标

在不引入阻断机制的前提下，让 global execution truth 写入具备可观察的 owner 信息。

### 建议字段

- `current_run.owner_session_id`
- `current_run.owner_host`
- `current_run.owner_run_id`
- `current_handoff.observability.owner_session_id`

说明：

- 不建议把 `owner_session_id` 塞进 `PlanArtifact`
- `current_plan` 继续保持 plan artifact 语义，不混入执行 owner 元数据

### 行为

1. session 写入 global execution truth 时，带上自己的 `owner_session_id`
2. 如果已有 global owner 且与当前不同，记录 warning note / observability
3. 不阻断，不抢占，不引入 heartbeat / expiry / takeover

## Session -> Global Promotion

这是 Phase 1 最关键的一步：review state 已经按 session 隔离，但 execution / finalize 仍只认 global state，因此在“继续执行”时必须显式提升。

### 触发条件

- 同一 session 的 review state 已有 `current_plan`
- 且 `current_run.stage` 已进入 `ready_for_execution` 或 `execution_confirm_pending`
- 用户在该 session 中给出“继续 / next / 开始 / 执行”之类的 execution confirm 意图

### Promote 动作

1. 先从 `review_store` 读取 `current_plan/current_run/current_handoff`
2. 将 `current_plan` 写入 `global_store.current_plan`
3. 将 execution-confirm 对应的 `current_run` 写入 `global_store.current_run`
4. 将 execution-confirm 对应的 `current_handoff` 写入 `global_store.current_handoff`
5. 在第 3/4 步写入时补齐 `owner_session_id / owner_host / owner_run_id`
6. `review_store` 中原有 plan/review state 默认保留，便于该 session 继续做 review 追溯；后续 execution / finalize 一律以 global store 为准

### Promote 后的行为

- 当前会话后续进入 `execution_confirm_pending / resume_active / finalize_active` 时，读取 global store
- 其他会话仍可保有自己的 session review state，但不会再通过覆盖根级 `current_plan` 抢走 execution truth
- 若 promote 时发现 global 已有不同 `owner_session_id`，只记 warning，不阻断

### 端到端示例

1. session A 执行 `plan_only`，plan 产物落到 `state/sessions/A/`
2. session B 执行另一个 `plan_only`，只写 `state/sessions/B/`，不影响 A
3. 用户在 session A 回复“继续执行”
4. runtime 先把 A 的 `current_plan/current_run/current_handoff` promote 到根级 global state
5. handoff 切到 `confirm_execute`
6. 用户确认后，execution / finalize 全部继续消费 global state
7. session B 的 review state 仍保留在自己的 session 目录，不影响 A 的执行主线

## execution / finalize 语义

- review 完成后，global execution 仍通过显式 plan 引用或执行确认进入
- `~go finalize` 继续只认 global active plan
- 本轮不新增 takeover decision，也不改变现有 confirm_execute 语义
- `quick_fix` 的宿主侧文件修改若与其他会话冲突，继续交给 git/worktree 处理，不纳入 runtime state 方案

## Manifest / Host 契约

需要补充：

1. `runtime_gate` 支持 `session_id`
2. gate 未收到 `session_id` 时自动生成并返回
3. 宿主在同一会话续轮时应复用相同 `session_id`
4. host bridge 文档明确：
   - review 并行是允许的
   - execution / finalize 继续走 global 单线
   - registry 不是 execution truth

## Session 清理策略

第一版采用惰性清理，不引入后台任务：

1. gate 启动时扫描 `state/sessions/`
2. 优先读取各 session `last_route.json.updated_at`
3. 若缺失则回退到 `last_route.json` 或 session 目录的 mtime
4. 超过 7 天未更新的 session 目录直接清理

目标是避免 `state/sessions/` 无限增长，而不是做精确生命周期管理

## 测试策略

### 并发 review

- session A `plan_only` 不覆盖 session B 的 `current_plan`
- session A 的 pending clarification / decision 不污染 session B

### 兼容性

- 无 `session_id` 时保持旧行为
- 老的 `~go finalize` 仍只认 global active plan

### 恢复

- review route 读取 session state
- execution route 读取 global state
- global state cleared 后，不影响其他 session 的 review 文档存在

### promotion / cancel

- session A `ready_for_execution` 后，回复“继续执行”会先 promote 到 global state
- promote 后 `~go finalize` / execution confirm 仍只认 global active state
- `cancel_active` 在仅有 review state 时只清当前 session
- `cancel_active` 在已有 global execution truth 时只清 global，并保留其他 session review state

### soft ownership

- global write 时记录 `owner_session_id`
- owner 不一致时产生 warning，但不阻断

### session cleanup

- gate 启动时会惰性清理超过 7 天未更新的 session 目录
- 清理不会误删根级 global execution truth

## 推荐实现顺序

1. `session_id` 透传与 `StateStore(config, session_id)`
2. review state session 隔离 + `cancel_active` 分流语义
3. Session -> Global Promotion + global route 继续读根级状态
4. soft ownership 写入与 warning observability
5. gate 惰性清理 + manifest / host docs / 兼容测试
