---
plan_id: 20260320_prompt_runtime_gate
feature_key: prompt-runtime-gate
level: standard
lifecycle_state: archived
blueprint_obligation: review_required
archive_ready: true
---

# 任务清单: Prompt-Level Runtime Gate（`prompt-runtime-gate`）

## A. 已冻结决策

- [x] A.1 新增 `prompt-level runtime gate`
- [x] A.2 gate 不替代 `host bridge`，而是其前置层
- [x] A.3 gate 继续复用现有 runtime manifest / preload / handoff / checkpoint 契约
- [x] A.4 gate 约束流程与输出，不宣称控制模型隐藏思考
- [x] A.5 gate 优先服务当前 `codex/claude` 场景
- [x] A.6 后续 Cursor 插件复用同一 gate core
- [x] A.7 host bridge 后续应复用 gate core，而不是实现平行逻辑

冻结标准：

- 方案文档明确 Layer 1 / Layer 2 的分层关系
- 方案文档不把 gate 描述成宿主硬拦截
- 方案文档明确 gate 只包装现有 runtime 协议

## B. 待实施任务

### 1. shared gate core

- [x] 1.1 新增 `runtime/gate.py`
- [x] 1.2 抽取或复用现有 workspace preflight / bootstrap 逻辑
- [x] 1.3 在 gate core 中串联 preload -> runtime dispatch -> handoff normalize
- [x] 1.4 计算 `allowed_response_mode`

验收标准：

- gate core 不复制现有 runtime 路由逻辑
- gate core 直接消费现有 handoff / entry_guard contract
- gate core 宿主无关，可供未来 host bridge / Cursor plugin 复用

### 2. gate CLI helper

- [x] 2.1 新增 `scripts/runtime_gate.py`
- [x] 2.2 提供 `enter` 入口
- [x] 2.3 输出 compact JSON contract
- [x] 2.4 视需要写出 `current_gate_receipt.json`

验收标准：

- helper 能接收 raw request 与 workspace root
- 输出包含 `status / gate_passed / handoff / allowed_response_mode / evidence`
- 出错时返回结构化错误，而不是自由文本

### 3. 宿主提示层协议改造

- [x] 3.1 更新 `Codex/Skills/CN/AGENTS.md`
- [x] 3.2 更新 `Codex/Skills/EN/AGENTS.md`
- [x] 3.3 更新 `Claude/Skills/CN/CLAUDE.md`
- [x] 3.4 更新 `Claude/Skills/EN/CLAUDE.md`

验收标准：

- Sopify 一旦被触发，第一步必须先执行 gate helper
- analyze / design / develop 全部变成 gate 后置阶段
- 宿主提示层不再仅凭文案声称“先走 runtime”

### 4. fail-closed 行为收紧

- [x] 4.1 `answer_questions` 映射为 `checkpoint_only`
- [x] 4.2 `confirm_decision` 映射为 `checkpoint_only`
- [x] 4.3 `confirm_execute` 映射为 `checkpoint_only`
- [x] 4.4 gate 未通过时统一进入 `error_visible_retry`

验收标准：

- pending checkpoint 不能被普通输出或普通开发流绕过
- 未过 gate 时不能直接给方案、直接改代码、自由追问
- 未拿到证据时不能口头声称“已进入 runtime”

### 5. 测试与 smoke

- [x] 5.1 新增 `tests/test_runtime_gate.py`
- [x] 5.2 覆盖 `normal_runtime_followup`
- [x] 5.3 覆盖三类 `checkpoint_only`
- [x] 5.4 覆盖 handoff 缺失 / contract 不完整时的 fail-closed
- [x] 5.5 新增 `scripts/check-prompt-runtime-gate-smoke.py`

验收标准：

- gate contract 可单测
- prompt-level 入口行为可 smoke
- 结果可证明“已先过 gate，再进入后续流程”

### 6. 文档与后续集成

- [x] 6.1 在文档中说明 gate 与 host bridge 的层次关系
- [x] 6.2 在文档中说明 gate 与 Cursor 插件的复用关系
- [x] 6.3 说明 gate receipt 是否为正式 machine evidence 还是仅作 visibility
- [x] 6.4 说明 host bridge 后续如何复用 gate core

验收标准：

- 不会与 `default_host_bridge_install` 方案打架
- 不会与 `cursor-plugin-install` 方案打架
- 读者能清楚理解 Layer 1 是当前优先级最高的稳定层

## C. 推荐实施顺序

1. 先做 `runtime/gate.py` 和 `scripts/runtime_gate.py`
2. 再把 `allowed_response_mode` 和 fail-closed 定死
3. 然后更新 `AGENTS.md / CLAUDE.md`
4. 再补 gate unit tests 与 smoke
5. 最后补文档，说明它和 host bridge / Cursor plugin 的关系
