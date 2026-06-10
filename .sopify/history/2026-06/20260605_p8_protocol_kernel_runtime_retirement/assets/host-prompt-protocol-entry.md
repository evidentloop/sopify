# Host Prompt Plan Snapshot — P8 Content Spec

> 本文定义 P8 post-cutover 宿主 prompt asset 必须包含的协议入口摘要内容。
> 不是完整 prompt 文本，不是第二份 protocol.md，不是 runtime router。
> W3.1 Qoder adapter 和后续宿主接入时，按此 spec 生成对应 host prompt。

## 必须包含的内容

### 1. Request Admission（请求准入）

当 workspace 中存在 `.sopify/` 时，host prompt MUST 指示 LLM：

- 先判断用户请求意图，形成 runtime-independent ActionProposal
- 将请求归类为以下之一：

| 类别 | 是否进入 4 步协议入口 |
|---|---|
| consult（问问题、解释、代码阅读） | 否 |
| quick_fix（unmanaged 单步修复） | 否 |
| new_plan（新建 managed plan） | 是（创建后进入） |
| continue_plan（继续当前 plan） | 是 |
| finalize（归档） | 是 |
| ask_user | 否 |

**关键约束**：consult / quick_fix 默认不自动接续 active_plan。不要求所有请求都进入协议入口。

### 2. 4 步协议入口（仅 managed plan / continuation / finalize）

```
1. state/active_plan.json         → 定位 plan_id
2. plan/<id>/plan.md              → 语义入口（优先读 Plan Snapshot 区）
3. state/current_handoff.json     → 恢复提示 + required_host_action
4. plan/<id>/receipts/            → 最新 1-3 个 receipt
```

**顺序原则**：先读 plan.md 建立语义真相，再读 current_handoff 作为恢复提示。handoff 不是第二真相源。

### 3. 读取预算

- active_plan / current_handoff：全量读（必须保持小文件）
- plan.md：优先读 Plan Snapshot（Goal / Status / Next / Task）；缺失或冲突时回退完整 plan.md
- tasks.md / design.md：默认不读，只在执行任务或架构判断时按需读
- receipts/：最新 1-3 个 receipt 或 final.json；不全量扫描
- protocol.md：默认不全量读；host prompt 已携带入口摘要

### 4. 写回边界

- 写 state/active_plan.json、state/current_handoff.json、receipts/*.json 时 MUST 走 `sopify_writer`
- Host prompt 负责请求准入与默认工作流入口
- Host prompt 不负责生成机器真相、不生成计划优先级、不执行验证

### 5. 默认工作流声明

默认 spec workflow（analyze → design → develop → finalize）是 prompt asset / skill 层功能，不是 runtime 逻辑。P8 后不存在 runtime router / engine / gate。

### 6. Fail-Open 规则

- active_plan 缺失 → consult / new-plan；不阻断
- current_handoff 缺失 → 按 plan.md 进度接续
- receipts/ 缺失 → 不假设任何动作已验证
- plan.md 与 handoff 冲突 → 以 plan.md 为准

## 必须不包含的内容

| 禁止项 | 理由 |
|---|---|
| `runtime_gate.py` / `runtime_gate.py enter` | P8 退场 |
| route families / route_name | runtime 内部实现，P8 后下沉 |
| `_registry.yaml` | P8 退场 |
| 要求全量读 protocol.md / design.md / receipts/ | 违反读取预算 |
| 暗示 consult / quick_fix 必须接续 active_plan | 违反请求准入 |
| 定义 runtime router / engine / session state machine | P8 退场 |
| ExecutionAuthorizationReceipt / gate receipt | P8 显式退场 |

## 验证条件

| 检查项 | 方法 |
|---|---|
| Qoder prompt asset 可从同一 spec 生成 | W3.1 验收 |
| prompt 文本足够短，不成为第二 protocol.md | 人工审查 |
| 不指示 LLM 默认加载完整 protocol.md | grep 检查 |
| 不暗示 consult / quick_fix 必须接续 active_plan | grep 检查 |
