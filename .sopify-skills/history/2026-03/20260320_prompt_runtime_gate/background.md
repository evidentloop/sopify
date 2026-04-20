# 变更提案: Prompt-Level Runtime Gate（`prompt-runtime-gate`）

## 需求背景

当前 Sopify 在 `codex` / `claude` 宿主里的现实情况是：

1. 宿主已经会触发 Sopify 技能包与提示层规则
2. 仓库内已经存在完整的 runtime machine contract
3. 但“技能已触发”并不稳定等于“本轮已严格先进入 runtime”

这导致一个典型问题：

1. 模型已经进入 Sopify 语境
2. 但没有先消费 `manifest / preload / handoff / checkpoint`
3. 就直接输出方案、追问、甚至开始改代码

换句话说，当前缺的不是 runtime contract，而是“技能触发后的统一入口协议”。

## 当前现象

从现有仓库能力看，Sopify 已经具备这些基础：

1. 默认 runtime 入口：`scripts/sopify_runtime.py`
2. entry guard contract：`runtime/entry_guard.py`
3. handoff 写出与状态文件：`runtime/handoff.py`
4. runtime CLI 结构化 JSON 输出：`runtime/cli.py`
5. 宿主提示层中的 runtime-first 规则：`Codex/Skills/*/AGENTS.md` 与 `Claude/Skills/*/CLAUDE.md`

但这些能力当前仍主要以：

1. 提示层强规则
2. runtime 内部 machine contract

的形式存在，而没有被前置成一个宿主无关、可重复执行、可验证的 prompt-level gate。

## 为什么“技能已触发”不等于“已进入 runtime”

本轮必须明确区分两件事：

1. `Sopify 被触发`
2. `Sopify runtime 已被严格执行`

两者不等价，原因如下：

1. 技能触发只说明模型已经进入 Sopify 语境，不说明它已执行 runtime helper
2. 提示层规则是高强度约束，但仍不是宿主级硬拦截
3. 模型可能在未拿到 handoff 证据时先生成正常输出
4. pending checkpoint 状态若未被强约束，仍可能被普通回答或普通开发流绕过

因此，本轮需要在“技能已触发”与“进入 analyze/design/develop”之间加一层明确的 runtime gate。

## 本轮目标

### 1. 新增 prompt-level runtime gate

- 一旦 Sopify 被触发，必须先经过 gate
- gate 负责统一执行 preflight / preload / runtime dispatch / handoff normalize
- 未过 gate 前不得进入常规阶段输出

### 2. 复用现有 runtime 控制面

- 继续使用现有 `.sopify-runtime/manifest.json`
- 继续使用既有 default entry / preferences preload / handoff / checkpoint 契约
- 不发明第二套 runtime 协议

### 3. 约束流程与输出，而不是宣称控制思考

- gate 约束的是“允许做什么”和“允许怎么输出”
- 不把它描述成对模型隐藏思考的强控制
- 所有严格性都来自可执行步骤和可验证证据

### 4. 作为后续 host bridge 的前置层

- prompt-level gate 优先解决当前 `codex/claude` 的稳定性问题
- 后续 `host bridge` 不应替代它，而应复用同一套 gate core
- 后续 Cursor 插件也应复用这层

## 非目标

本轮明确不做以下内容：

- 不替代 `default_host_bridge_install`（已弃置，2026-04）
- 不宣称 prompt-level gate 已达到宿主硬入口级别的严格性
- 不重写现有 runtime manifest / handoff / checkpoint schema
- 不在本轮引入新的宿主安装器或插件分发逻辑
- 不试图控制模型隐藏思考链路

## 与 Host Bridge 的关系

`prompt-runtime-gate` 与 `default-host-bridge-install` 是两层不同能力：

### Layer 1: prompt-level runtime gate

目标：

1. 只要 Sopify 已被触发，就先统一经过 gate
2. 提升当前 `codex/claude` 场景下的稳定性
3. 用最小改动把“runtime-first”从规则变成可执行协议

### Layer 2: host bridge

目标：

1. 由宿主在 turn 入口做硬接管
2. 提供更高严格性、更强 doctor / smoke 证明能力
3. 最终实现宿主级稳定 ingress

本轮结论：

1. Layer 1 优先级更高
2. Layer 2 继续保留为后续硬化路径
3. Layer 2 后续应复用 Layer 1 的 gate core，而不是再做一套平行逻辑

## 成功标准

满足以下条件即可认为本期目标成立：

1. Sopify 一旦被触发，模型必须先执行统一 gate helper
2. gate 未返回通过证据前，不允许正常方案输出、直接改代码或自由追问
3. pending checkpoint 下，只允许进入对应 checkpoint 响应模式
4. gate 使用现有 runtime 入口与 handoff contract，不发明第二套主协议
5. `codex` / `claude` 当前宿主提示层可共用这层 gate
6. 后续 Cursor 插件设计可以直接复用该 gate

## 风险评估

### 风险 1

如果只加强文案规则而不引入可执行 helper，收益会有限。

缓解：

- 本轮不止改提示层
- 同步新增极小 gate helper 与结构化 contract

### 风险 2

如果 gate 再发明一套自己的状态文件与协议，会与现有 runtime contract 重叠。

缓解：

- gate 只包装现有 preflight / preload / runtime / handoff
- 仅输出轻量 JSON contract 与可选 receipt

### 风险 3

如果把 gate 描述成“已经等于宿主 bridge”，会造成预期偏差。

缓解：

- 文档明确其定位是 Layer 1
- host bridge 仍保留为 Layer 2

### 风险 4

如果 gate 不提供可验证证据，模型仍可能口头声称“已进入 runtime”。

缓解：

- gate 必须返回 compact JSON contract
- 并以 `handoff / strict_runtime_entry / manifest` 作为证据来源

## 规划结论

当前最值得优先补的不是新的宿主桥接实现，而是把“技能已触发后必须先过 runtime”落成一层统一的 prompt-level gate。

因此，本轮方案结论为：

1. 新增 `prompt-level runtime gate`
2. 先提稳 `codex/claude` 当前场景
3. 继续复用现有 runtime 控制面
4. 将其作为后续 host bridge 与 Cursor 插件的共享底座
