---
plan_id: 20260323_runtime-session-lease-session-scoped-review-stat
feature_key: runtime-session-lease-session-scoped-review-stat
level: standard
lifecycle_state: archived
knowledge_sync:
  project: review
  background: review
  design: review
  tasks: review
blueprint_obligation: review_required
archive_ready: true
---

# 任务清单: runtime 并发 review 隔离与 soft ownership（`runtime-session-lease-session-scoped-review-stat`）

## A. 已冻结决策

- [x] A.1 本轮先解决 runtime state collision，不再把问题继续下推给 `plan registry`
- [x] A.2 review state 按 session 隔离，execution truth 继续保持全局唯一
- [x] A.3 第一阶段不改 `~go finalize` 只认 global active plan 的语义
- [x] A.4 第一阶段保留根级 `current_*.json` 作为 global execution truth 的兼容形态
- [x] A.5 本轮不做完整 lease；global 写入只补 `owner_session_id` 等 soft ownership 信息
- [x] A.6 `plan registry` 继续 observe-only，不负责切换 `current_plan`
- [x] A.7 `StateStore` 保持现有接口形状，优先通过路径分叉而不是 scope 重构落地
- [x] A.8 `quick_fix` 的业务代码文件级冲突不在本轮范围；本轮只解决 runtime state collision
- [x] A.9 `cancel_active` 采用保守分流语义：优先取消 global execution truth，其次才取消当前 session review state

冻结标准：

- 文档中明确区分 `session review state / global execution truth / plan registry`
- 文档中不出现“registry 负责解决并发 active plan 覆盖”的表述
- 文档中明确 finalize 仍只消费 global active plan

## B. 任务 1 | session_id 透传 + StateStore 路径分叉

- [x] 1.1 为 `scripts/runtime_gate.py enter` 增加可选 `--session-id`
- [x] 1.2 gate 未收到 `session_id` 时自动生成并返回
- [x] 1.3 `run_runtime` / `StateStore` / observability 记录 `session_id`
- [x] 1.4 `StateStore(config, session_id=...)` 通过路径分叉把 review state 落到 `state/sessions/<session_id>/`
- [x] 1.5 无 `session_id` 的 direct runtime / legacy 调用保持 global 行为；gate 缺省时自动生成并返回 `session_id`
- [x] 1.6 gate 启动时惰性清理超过 7 天未更新的 session 目录（优先读 `last_route.updated_at`，缺失时回退 mtime）

验收标准：

- 宿主可以稳定复用同一个 `session_id`
- gate receipt / run / handoff 均可观测到 `session_id`
- review state 文件落到 session 目录
- 不传 `session_id` 的旧宿主不被破坏

## C. 任务 2 | review 路由切到 session scope

- [x] 2.1 `plan_only / workflow / light_iterate / clarification / decision / consult / replay / quick_fix` 默认读写 session state
- [x] 2.2 engine 内同时维护 `review_store` 与 `global_store`
- [x] 2.3 `Router` 默认基于 session state 做 pending 判断
- [x] 2.4 只为 `execution_confirm_pending / resume_active / exec_plan / finalize_active` 额外读取 global state
- [x] 2.5 “继续执行”时支持 Session -> Global Promotion：从 session review state 提升 `current_plan/current_run/current_handoff` 到根级 global state
- [x] 2.6 `cancel_active` 按当前活跃事实来源分流：global execution 优先，session review 次之
- [x] 2.7 `last_route` 同步切到 session state

验收标准：

- 两个 session 并发 `plan_only` 不会互相覆盖 `current_plan/current_run/current_handoff`
- session A 的 pending checkpoint 不会污染 session B
- session A `ready_for_execution` 后可把自己的 review plan promote 成 global execution truth
- `cancel_active` 不会误清其他 session 的 review state
- execution confirm / finalize 仍能看到 global active state

## D. 任务 3 | global execution soft ownership

- [x] 3.1 global `current_run/current_handoff` 写入时附带 `owner_session_id`
- [x] 3.2 记录 `owner_host / owner_run_id` 等最小 observability 字段
- [x] 3.3 当已有 owner 与当前 session 不一致时，只写 warning note / observability，不阻断
- [x] 3.4 `current_plan` 保持纯 `PlanArtifact` 语义，不混入 owner 元数据
- [x] 3.5 Session -> Global Promotion 时同步写入 soft ownership

验收标准：

- global execution truth 的来源 session 可观察
- 不会因为 soft ownership 引入新的阻断或锁死 workspace 的风险

## E. 任务 4 | 兼容测试

- [x] 4.1 新增“两个 session 并发 `plan_only` 不互相覆盖”的测试
- [x] 4.2 新增“session A clarification/decision 不污染 session B”的测试
- [x] 4.3 新增“无 `session_id` 时保持旧行为”的兼容测试
- [x] 4.4 新增“execution confirm / finalize 仍只读 global active state”的测试
- [x] 4.5 新增“soft ownership 只 warn 不阻断”的测试
- [x] 4.6 新增“session review -> global promotion”的测试
- [x] 4.7 新增“cancel_active 只清当前目标 scope”的测试
- [x] 4.8 新增“gate 惰性清理过期 session 目录”的测试

验收标准：

- review 并发、legacy fallback、global execution 可见性三类风险都有自动化覆盖

## F. 任务 5 | manifest / 文档更新

- [x] 5.1 在 manifest / helper 文档中加入 `session_id` 契约
- [x] 5.2 明确 gate 可自动生成并返回 `session_id`
- [x] 5.3 明确 review 并行、execution 单线的宿主接入规则
- [x] 5.4 README 补充并发会话下的推荐工作方式
- [x] 5.5 若状态分层落地，更新 blueprint design 中的 runtime state 说明
- [x] 5.6 明确 registry 继续 observe-only
- [x] 5.7 明确 `quick_fix` 的文件级冲突不在本方案范围内

验收标准：

- Codex / Claude 宿主都知道何时复用同一 session id
- 宿主不会再把 review state 当 execution truth

## G. 推荐实施顺序

1. 先做 `session_id` 透传与 `StateStore(config, session_id)`
2. 再切 review/global 路由的 store 使用与 `cancel_active` 分流
3. 然后补 Session -> Global Promotion
4. 再补 soft ownership 与 warning observability
5. 最后补 session 清理、兼容测试与 manifest / 文档

## H. 收口标准

- [x] H.1 review routes 已按 session 隔离
- [x] H.2 global execution truth 已带 soft ownership 观测字段
- [x] H.3 review state 可在需要时提升为 global execution truth，finalize 不再因其他 session 的 review 覆盖而误收/无法收口
- [x] H.4 宿主文档与 README 已说明并发会话边界
- [x] H.5 自动化测试覆盖并发 review、global visibility、legacy fallback
