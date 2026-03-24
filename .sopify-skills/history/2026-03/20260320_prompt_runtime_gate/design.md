# 技术设计: Prompt-Level Runtime Gate（`prompt-runtime-gate`）

## 设计目标

在不改变现有 runtime manifest / preload / handoff / checkpoint schema 的前提下，为 Sopify 新增一层统一的 prompt-level runtime gate：

1. Sopify 一旦被触发，必须先执行 gate
2. gate 统一执行 preflight / preload / runtime dispatch / handoff normalize
3. gate 输出 compact JSON contract，作为后续允许输出和允许行动的唯一依据
4. gate 对 `codex` / `claude` 共用，并为后续 Cursor 插件复用

## 总体设计

### 0. 产品定位

Layer 1 不替代 host bridge，而是把“prompt 规则”升级成“可执行协议”。

因此，本轮新增的是：

1. 统一 gate helper
2. 宿主提示层的入口协议
3. 最小可测 contract

而不是：

1. 宿主级 hook/launcher/app-server 接管
2. 第二套 runtime schema

### 1. 结构建议

建议新增：

```text
runtime/
└── gate.py

scripts/
└── runtime_gate.py
```

职责：

#### `runtime/gate.py`

负责核心 gate 逻辑：

1. workspace preflight / bootstrap
2. preferences preload
3. default runtime dispatch
4. handoff normalize
5. allowed response mode 计算
6. 轻量 receipt 组装

#### `scripts/runtime_gate.py`

负责对外 CLI 封装：

1. 接收原始请求
2. 调用 `runtime.gate`
3. 输出 compact JSON contract

## gate 入口协议

一旦 Sopify 被触发，宿主提示层的第一步固定为：

```bash
python3 scripts/runtime_gate.py enter --workspace-root <cwd> --request "<raw user request>"
```

后续行为规则：

1. 先看 gate contract
2. 再决定是否能进入 analyze / design / develop 或 checkpoint 响应
3. 未拿到 gate 通过证据前，不允许正常输出

### 2. 触发时机

以下场景都必须先过 gate：

1. 原始用户请求第一次触发 Sopify
2. 用户补充 clarification 信息后恢复流程
3. 用户在 decision checkpoint 中拍板后恢复流程
4. 用户确认执行后恢复流程
5. 宿主继续 active run 的任何新一轮 Sopify 回合

## gate 执行顺序

### Step 1: workspace preflight

优先顺序：

1. 检查当前 workspace 的 `.sopify-runtime/manifest.json`
2. 若缺失或不兼容，则尝试按现有 payload manifest 逻辑 bootstrap workspace
3. 允许 repo-local 开发态与宿主安装态共存

设计要求：

1. 优先复用已有 preflight 逻辑
2. 若现有实现散落在 `runtime/plan_orchestrator.py`，应抽成共享 helper，而不是复制

### Step 2: preferences preload

执行规则：

1. 从 manifest 读取 `limits.preferences_preload_entry`
2. 调用 preload helper
3. 仅在现有 contract 允许时注入 `injection_text`
4. `missing / invalid / read_error` 按现有规则 `fail-open with visibility`

### Step 3: default runtime dispatch

执行规则：

1. 优先调用现有默认 runtime 入口
2. 使用结构化结果，不依赖渲染文案作机器判断
3. 继续沿用现有 route / plan / handoff 写出逻辑

建议实现：

1. 通过现有 `run_runtime(...)` 内部 API 或 runtime CLI JSON 输出复用能力
2. 不再手工拼一套路由判断

### Step 4: handoff normalize

执行规则：

1. 读取 `.sopify-skills/state/current_handoff.json`
2. 读取其中的 `required_host_action`
3. 读取其中的 `artifacts.entry_guard`
4. 计算本轮允许的响应模式

收口决策：

1. `evidence.handoff_found` 只在 `current_handoff.json` 已落盘时才为 `true`
2. `runtime_result.handoff` 只作为 normalize fallback，避免 helper 在异常路径下完全丢失结构化上下文
3. 宿主若要声称“已严格进入 runtime”，仍必须以已落盘 handoff 为准，而不是以内存对象为准

### Step 5: gate result / receipt

gate 返回 compact JSON contract，并可选写出一个轻量 receipt 文件，供 smoke / debug / doctor 使用。

建议 receipt 路径：

```text
.sopify-skills/state/current_gate_receipt.json
```

receipt 不是新的主 machine contract，只是 Layer 1 的可见性增强。

收口决策：

1. 主 machine truth 仍是 `.sopify-skills/state/current_handoff.json`
2. `current_gate_receipt.json` 只用于 visibility / smoke / doctor，不参与宿主主链路判定
3. receipt 与 handoff 不一致时，应优先相信 handoff，再把 receipt 视为 drift 信号

## gate contract

建议 `scripts/runtime_gate.py enter` 返回：

```json
{
  "schema_version": "1",
  "status": "ready",
  "gate_passed": true,
  "workspace_root": "/abs/path",
  "preflight": {
    "action": "updated",
    "reason_code": "BOOTSTRAPPED"
  },
  "preferences": {
    "status": "loaded",
    "injected": true,
    "injection_text": "..."
  },
  "runtime": {
    "route_name": "workflow",
    "reason": "..."
  },
  "handoff": {
    "required_host_action": "confirm_decision",
    "entry_guard_reason_code": "entry_guard_decision_pending",
    "pending_fail_closed": true
  },
  "allowed_response_mode": "checkpoint_only",
  "evidence": {
    "manifest_found": true,
    "handoff_found": true,
    "strict_runtime_entry": true
  }
}
```

### 字段约束

#### 顶层

- `schema_version`
- `status`
- `gate_passed`
- `workspace_root`
- `allowed_response_mode`

#### `preflight`

- `action`
- `reason_code`
- `message`（可选）

#### `preferences`

- `status`
- `injected`
- `injection_text`（仅在可注入时出现）

#### `runtime`

- `route_name`
- `reason`

#### `handoff`

- `required_host_action`
- `entry_guard_reason_code`
- `pending_fail_closed`

#### `evidence`

- `manifest_found`
- `handoff_found`
- `strict_runtime_entry`

## allowed response modes

Layer 1 不直接决定业务内容，而是决定“当前允许哪种行为”。

建议最小模式集如下：

### 1. `normal_runtime_followup`

适用条件：

1. `gate_passed == true`
2. `handoff.required_host_action` 为普通继续主链动作

允许行为：

1. 进入 analyze / design / develop 后续链路
2. 继续正常 Sopify 输出

### 2. `checkpoint_only`

适用条件：

1. `required_host_action in {"answer_questions", "confirm_decision", "confirm_execute"}`

允许行为：

1. 只展示 checkpoint 摘要
2. 只等待用户补事实、拍板或执行确认

禁止行为：

1. 自行物化正式 plan
2. 直接进入 develop
3. 把 `~go exec` 当绕过入口

### 3. `error_visible_retry`

适用条件：

1. gate helper 执行失败
2. handoff 证据缺失
3. 结构化 contract 不完整

允许行为：

1. 输出短错误摘要
2. 明确提示重试或检查状态

禁止行为：

1. 假装已进入 runtime
2. 继续正常流程输出

## 输出守卫

一旦进入 Sopify gate，必须执行以下输出规则：

### 1. 未过 gate 前不得正常输出

禁止：

1. 直接生成方案
2. 直接开始代码修改
3. 自由追问
4. 手工伪造 handoff / decision / clarification 文件

### 2. 未拿到证据前不得声称“已进入 runtime”

最低证据要求：

1. `status == ready`
2. `gate_passed == true`
3. `evidence.handoff_found == true`
4. `evidence.strict_runtime_entry == true`

### 3. checkpoint pending 时只能进入 checkpoint 响应

如果 `required_host_action` 为：

1. `answer_questions`
2. `confirm_decision`
3. `confirm_execute`

则只允许：

1. 展示缺失事实
2. 展示选项与推荐项
3. 展示 execution summary
4. 等待用户继续

## 宿主提示层接入

本轮需要更新这些入口文档：

1. `Codex/Skills/CN/AGENTS.md`
2. `Codex/Skills/EN/AGENTS.md`
3. `Claude/Skills/CN/CLAUDE.md`
4. `Claude/Skills/EN/CLAUDE.md`

接入规则：

1. Sopify 被触发后，第一步必须执行 `runtime_gate.py enter`
2. gate 通过后再决定进入后续阶段
3. 所有普通阶段技能都变成 gate 后置阶段

说明：

1. 这不替代后续 host bridge
2. 后续 host bridge 应复用 `runtime/gate.py` 的 core 逻辑

## 与 Cursor 的关系

本轮不实现 Cursor 接入，但必须预留复用位：

1. Cursor 插件未来的 `beforeSubmitPrompt` hook 应直接调用同一个 gate helper
2. Cursor 不再重新发明一套 runtime ingress 流程
3. Cursor 只新增宿主分发层与 turn ingress adapter，继续复用 `runtime/gate.py` 与 manifest contract
4. Cursor 的 IDE-first 插件链路与 `codex` / `claude` 的 host bridge 一样，后续都应复用同一个 gate core

因此，Layer 1 的设计必须保持宿主无关，不与 `codex` / `claude` 安装器绑定。

## 测试与 smoke

### 1. 单元测试

建议新增：

```text
tests/test_runtime_gate.py
```

最小覆盖：

1. gate 正常返回 `normal_runtime_followup`
2. clarification pending 返回 `checkpoint_only`
3. decision pending 返回 `checkpoint_only`
4. execution confirm pending 返回 `checkpoint_only`
5. handoff 缺失时返回 `error_visible_retry`

### 2. 宿主提示层 smoke

建议新增：

```text
scripts/check-prompt-runtime-gate-smoke.py
```

最小覆盖：

1. 模拟 Sopify 被触发
2. 验证 gate helper 先执行
3. 验证未过 gate 时不会直接进入普通输出
4. 验证 pending checkpoint 不能被绕过

### 3. 可见性

若实现 `current_gate_receipt.json`，smoke 应验证：

1. receipt 已写出
2. receipt 中 `allowed_response_mode` 正确
3. receipt 中证据字段与 handoff 状态一致

范围说明：

1. `scripts/check-prompt-runtime-gate-smoke.py` 负责验证 Layer 1 gate contract 与 fail-closed 行为
2. `scripts/check-runtime-smoke.sh` 继续只验证 bundle/runtime 资产完整性，不证明宿主第一跳是否先执行 gate
3. 宿主 first-hop ingress proof 留给后续 host bridge doctor / smoke，不在本轮 Layer 1 收口范围内

## rollout 策略

### Phase 1

- 新增 `runtime/gate.py` 与 `scripts/runtime_gate.py`
- 先只打通 compact JSON contract

### Phase 2

- 更新 `AGENTS.md / CLAUDE.md`
- 把 gate 前置到 Sopify 入口协议

### Phase 3

- 增加 `checkpoint_only` fail-closed 与 smoke
- 补充可选 gate receipt

### Phase 4

- 让后续 `host bridge` 与 `Cursor plugin` 复用同一 gate core
- host bridge doctor / smoke 在下一层实现，不回灌到本轮 Layer 1 smoke

## 设计结论

Layer 1 的正确实现方式不是继续堆叠更强文案，而是引入一层极小但可执行、可验证、可复用的 runtime gate。

因此，本轮实现结论为：

1. 新增 `runtime/gate.py`
2. 新增 `scripts/runtime_gate.py`
3. gate 统一包装 preflight / preload / runtime dispatch / handoff normalize
4. 宿主提示层一旦触发 Sopify，必须先执行 gate
5. pending checkpoint 必须被收敛为 `checkpoint_only`
6. 后续 host bridge 与 Cursor plugin 复用这层 gate core
