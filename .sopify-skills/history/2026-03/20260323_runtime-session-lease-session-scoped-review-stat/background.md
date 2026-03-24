# 变更提案: runtime 并发 review 隔离与 soft ownership（`runtime-session-lease-session-scoped-review-stat`）

## 需求背景

当前 runtime 的 review / planning 状态以工作区级单例文件为中心：

- `.sopify-skills/state/current_plan.json`
- `.sopify-skills/state/current_run.json`
- `.sopify-skills/state/current_handoff.json`
- `.sopify-skills/state/current_clarification.json`
- `.sopify-skills/state/current_decision.json`

这套设计在单宿主串行使用时足够简单，但在同一仓库下同时开多个 Codex / Claude 会话，并行跑 `plan_only` / review 时会出现具体且高频的问题：

1. 不同会话的 `plan_only` / review 会互相覆盖 `current_plan`
2. 一个会话的 pending clarification / decision 会污染另一个会话的恢复上下文
3. `~go finalize` 只认全局 active plan，导致“方案本身已可收口，但当前会话无法 finalize 自己正在评审的 plan”
4. 问题根因在 review state 共用单例文件，而不是 execution 本身需要多 owner 并发控制

因此这轮的目标不是引入完整 lease 体系，而是先用最小改动把状态拆成两层：

- 会话内评审态：允许并行 review / planning
- 全局执行态：继续保持单一 machine truth，并补一个 soft ownership 标记用于观测

## 目标

1. 支持同一 workspace 下多个宿主并行评审不同 plan，而不互相覆盖 review state
2. 保持“全局只有一个 active execution truth”的约束，不放开多执行主线
3. 在 global execution truth 写入时记录 `owner_session_id`，用于告警与观测，而不是立即阻断
4. 保持现有宿主与历史状态的兼容性，优先渐进演进

## 非目标

1. 不引入多个 plan 并发执行
2. 不让 `plan registry` 直接切换 `current_plan`
3. 本轮不实现 heartbeat / expiry / takeover / 强制 owner 校验
4. 本轮不重写 finalize 语义，不把所有根状态文件立即迁移到全新目录结构
5. 不试图解决多个会话同时改同一业务代码文件的 git/worktree 冲突

## 变更内容

1. 为 runtime gate / engine / state 主链增加 `session_id`
2. 增加 `state/sessions/<session_id>/` 下的 session-scoped review state
3. 保留根级 `current_*` 作为 global execution truth，先不改 `~go finalize` 入口语义
4. 在 global execution truth 写入时带上 `owner_session_id` 等 soft ownership 信息，仅 warn 不阻断
5. 更新 manifest / host 文档，明确 review 并行、execution 单线的宿主契约
6. 明确 session review state 提升到 global execution truth 的时机与边界

## 影响范围

- 模块:
  - `scripts/runtime_gate.py`
  - `runtime/gate.py`
  - `runtime/state.py`
  - `runtime/engine.py`
  - `runtime/router.py`
  - `runtime/clarification_bridge.py`
  - `runtime/decision_bridge.py`
- 文件:
  - `.sopify-runtime/manifest.json`
  - `README.md`
  - 宿主接入文档 / blueprint 相关说明
  - runtime tests / smoke tests

## 风险评估

- 风险: review state 按 session 落盘后，宿主如果没有稳定回传 `session_id`，可能退回 legacy 行为
  - 缓解: gate 在未传入时自动生成 `session_id` 并通过 receipt/stdout 返回
- 风险: `Router` 如果完全只看 session state，会漏掉 global execution pending 的恢复
  - 缓解: 只为少量 global execution 路由额外读取根级 global state，不重写整套恢复模型
- 风险: session review state 拆走后，“继续执行”如果没有显式 promotion，会出现当前 session 看到 plan、global finalize/execute 却看不到 plan 的断层
  - 缓解: 在 execution confirm 入口增加显式 Session -> Global Promotion，把 session 里的 `current_plan/current_run/current_handoff` 提升为 global execution truth
- 风险: 宿主未传 `session_id` 时出现行为回退不一致
  - 缓解: 第一阶段保留 legacy fallback，并补无 `session_id` 的兼容测试
- 风险: session 目录可能长期堆积
  - 缓解: gate 启动时惰性清理 7 天前未更新的 session 目录，优先读取 `last_route.json.updated_at`，缺失时回退文件 mtime
- 风险: `quick_fix` 虽走 session state，但多个宿主仍可能改到同一业务文件
  - 缓解: 明确把业务代码文件级冲突排除在本方案范围外；本轮只解决 runtime state collision
