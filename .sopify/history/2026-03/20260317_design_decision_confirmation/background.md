# 变更提案: 决策确认能力通用化（兼容现有接入链路）

## 当前真实状态

截至 2026-03-18，`sopify-skills` 已经把 decision runtime contract 从窄版单选 checkpoint 升级到“通用 checkpoint + submission + legacy projection”的可恢复状态。当前代码已经提供内置 CLI interactive renderer 与文本降级路径，runtime 侧的核心 contract 与 CLI bridge 最小闭环均已具备：

1. runtime 已支持 `decision_pending / decision_resume` 路由，并把活跃决策持久化到 `.sopify-skills/state/current_decision.json`。
2. planning 路由中的自动触发目前基于显式分叉语义，主要识别 `还是 / vs / or`，同时要求请求中带有 runtime、bundle、manifest、handoff、workspace、plan、blueprint 等架构关键词。
3. 当前 `DecisionState` 已承载 `schema_version / checkpoint / submission / selection` 语义分层；同时保留 `question / options / recommended_option_id / selected_option_id` 的 legacy projection，便于单选场景继续工作。
4. `current_handoff.json` 仍保持 `required_host_action == confirm_decision`，但已额外暴露 `artifacts.decision_checkpoint` 与 `artifacts.decision_submission_state`，宿主可优先读取 handoff 中的结构化 checkpoint。
5. 用户当前既可通过自然输入 `1 / 2 / ...`、`~decide choose <option_id>` 选择方案，也可由宿主先把结构化 `submission` 写回 `current_decision.json`，再通过默认 runtime 入口恢复。
6. 已确认决策会恢复 planning，随后重新进入 `execution_gate`；若 gate 仍发现阻塞风险，runtime 可以创建新的 follow-up decision checkpoint。
7. `ready_for_execution` 已作为内部 `RunState.stage` 落地；普通主链路在 gate ready 后会进入 `execution_confirm_pending`，不能通过 `~go exec` 绕过 clarification / decision / execution-confirm。

这意味着当前系统已经具备“通用 decision runtime contract + host bridge helper”的主要机器能力；`decision_templates.py`、`decision_policy.py`、CLI bridge contract 与 bridge 契约测试均已落地。

## 当前问题

现状已经满足 runtime contract 的最小闭环，但仍有几个明确缺口：

1. runtime contract 已能表达 `select / multi_select / confirm / input / textarea` 的字段类型，且第一版通用模板已抽出，但当前只覆盖 `strategy_pick` 这一类最小模板。
2. 宿主桥接当前以 vendored helper 方式落地：`scripts/decision_bridge_runtime.py` 提供 `inspect / submit / prompt`，标准接入不变；CLI 型宿主已可直接复用内置 interactive renderer，后续只需在具体宿主产品里继续对接。
3. 当前自动触发已演进为两层：一层保留 planning request 的显式分叉语义基线；另一层优先消费 `RouteDecision.artifacts.decision_candidates` 的结构化 tradeoff 候选，并支持显式抑制标记。仍未演进到“design 子流程自动产出候选后无缝接入”的全自动模式。
4. `~compare` 已可在 handoff 中输出 `compare_decision_contract` facade，供宿主复用同一套 decision bridge UI；当前仍保持原 compare 路由，不直接改写为 `current_decision.json` 主链路。
5. replay 摘要已能稳定记录 checkpoint 创建、推荐项、推荐理由、最终选择与关键约束，并默认省略自由输入原文。

## 下一阶段目标

下一阶段目标不是继续重做 runtime contract，而是在保持接入方式不变的前提下，把已落地能力继续向更强模板与更稳定的 CLI 交互推进：

1. 保留当前默认入口、workspace bootstrap、manifest-first、handoff-first 的接入链路。
2. 继续沿用 `.sopify-skills/state/current_decision.json` 与 `current_handoff.json`，由宿主消费现有 checkpoint / submission 契约。
3. 保留 `confirm_decision` 作为稳定宿主动作名，不额外发明新的主链路动作。
4. 让 CLI 型宿主按同一份 checkpoint schema 提供终端问答桥接；当前默认内置 interactive renderer，必要时退化到纯文本问答。
5. 在兼容旧版 `1 / 2 / ~decide choose` 的同时，继续扩展 `strategy_pick` 之外的模板族，并把 clarification/decision 的 CLI 交互体验统一收口。

## 接入方式硬约束

这一轮通用化必须明确遵守以下接入约束，不允许偏移：

1. 一键接入仍由 `scripts/install-sopify.sh` / `scripts/install_sopify.py` 完成，继续安装宿主提示层与全局 payload。
2. 用户在项目中触发 Sopify 时，宿主仍然先读取全局 `payload-manifest.json`，再按需调用 `bootstrap_workspace.py` 自动补齐当前仓库的 `.sopify-runtime/`。
3. workspace 内仍以 `.sopify-runtime/manifest.json` 为机器契约；宿主优先读取 `default_entry` 与 `plan_only_entry`，而不是硬编码新入口。
4. 默认 raw-input 入口继续保持为 `scripts/sopify_runtime.py`；vendored 默认入口继续保持为 `.sopify-runtime/scripts/sopify_runtime.py`。
5. 决策能力升级后，不得要求用户记住新的安装步骤、单独同步新的 bundle 目录，或额外执行新的主入口脚本。
6. 如后续新增 helper，也只能是内部测试 / 调试 / 宿主实现辅助能力，不能取代现有默认 runtime 入口链路。

## 非目标

下一阶段不做以下事情：

1. 不改造一键安装链路，不新增新的“决策能力安装器”。
2. 不把 decision 强制提升成固定第 4 个公开主 route。
3. 不要求所有宿主统一引入某个第三方终端问答库；CLI richer UI 只能是宿主实现细节，而不是平台级标准。
4. 不在当前阶段实现 editor-side 或图形表单 UI；当前只收口 CLI 终端问答桥接。
5. 不让用户依赖新的命令记忆成本来恢复流程；默认仍通过既有 runtime 入口与 handoff 恢复。

## 变更内容

### 1. Runtime Contract 已完成升级

在保留当前 `current_decision.json` 文件位点和 `confirm_decision` 动作名的前提下，runtime 已把窄版 `DecisionState` 升级为可承载：

- 字段定义
- 条件显示
- 校验规则
- 推荐项
- 统一 submission
- 恢复上下文

的通用 checkpoint 契约。

### 2. Runtime State / Engine 已完成升级

runtime 不再只依赖原始文本解析来确认决策，而是已支持宿主先写入结构化 submission，再通过默认 runtime 入口恢复当前会话。

### 3. Host Bridge 已落地为内部 helper

当前通过 `scripts/decision_bridge_runtime.py` 提供统一 helper，不改变现有接入方式：

- 当前文档范围只要求 CLI 型宿主接入 bridge contract
- CLI bridge contract 当前优先映射到内置 interactive renderer，并保留文本降级路径
- vendored helper 内置 CLI text fallback，保证缺少 richer renderer 时仍可恢复

### 4. Policy 演进已进入第二阶段

当前已保持 planning-request 语义触发基线可用，同时新增了结构化 tradeoff candidate policy。后续仍应继续保持分阶段迁移，避免一次性把触发逻辑全部推翻。

### 5. Compare facade、scope clarify 与 replay 摘要已补齐最小闭环

当前 `~compare` 已能在 handoff 中输出 shortlist 版 `DecisionCheckpoint` facade，clarification 也已能输出 `clarification_form` 并支持结构化恢复，replay 也已记录 compare 推荐依据与 decision 关键摘要；这些都属于“复用统一契约”的保守接入，不改变既有主路由语义。

### 6. 文档与计划收口已进入第二轮

当前方案目录已改写为“已落地基线 + 下一阶段 delta”；本轮继续补充代码完成态与剩余工作边界，避免后续实施继续被旧口径误导。

## 影响范围

若后续实施代码，预计会涉及：

- `runtime/models.py`
- `runtime/state.py`
- `runtime/decision.py`
- `runtime/router.py`
- `runtime/engine.py`
- `runtime/handoff.py`
- `runtime/output.py`
- `runtime/execution_gate.py`
- `runtime/manifest.py`
- `runtime/builtin_catalog.py`
- `tests/test_runtime.py`
- 宿主桥接层实现仓库

本轮已修改 runtime 相关代码与测试；文档收口会继续同步当前方案目录中的真实完成状态。

## 风险评估

### 风险 1: 通用 schema 升级破坏现有宿主兼容性

- 风险描述：如果直接把 `current_decision.json` 改成全新结构，现有只读取 `question/options/recommended_option_id` 的宿主会失效。
- 缓解措施：
  - 新旧字段并行一段时间
  - 宿主优先读 `artifacts.decision_checkpoint`
  - 对单选场景继续保留 legacy projection

### 风险 2: 宿主 UI 方案绑死到某一平台库

- 风险描述：若把某个第三方终端问答库写成平台级统一标准，会把宿主实现细节误写成 runtime 契约，增加接入成本。
- 缓解措施：
  - 先抽象 host-agnostic checkpoint / submission 协议
  - 保持 checkpoint / submission 协议 host-agnostic
  - richer terminal UI 只作为 CLI 型宿主的可选实现

### 风险 3: 为了表单能力破坏现有接入链路

- 风险描述：若决策能力要求新增主入口或新的 bundle 目录，现有一键接入和自动 bootstrap 将被打断。
- 缓解措施：
  - 明确默认入口、bundle 布局、manifest-first 不变
  - 决策能力只能作为现有 runtime 的 contract 升级
  - 新 helper 只作为内部辅助，不进入主链路

### 风险 4: 多步输入导致恢复状态更复杂

- 风险描述：宿主写入 submission 后，runtime 若没有稳定恢复协议，容易出现 state / handoff 不一致。
- 缓解措施：
  - `current_decision.json` 继续作为唯一 decision 状态文件
  - `current_handoff.json` 只承载当前阶段机器摘要
  - 恢复入口仍统一走默认 runtime，而不是散落的专用脚本

## 成功标准

下一阶段完成后，应满足以下标准：

1. 用户继续通过现有一键接入和项目内触发方式使用 Sopify，无需新的安装步骤。
2. 宿主继续通过现有 manifest-first + handoff-first 链路进入 decision 环节。
3. runtime 能稳定表达通用 decision checkpoint schema，并支持结构化 submission。
4. CLI 型宿主能稳定消费同一份 checkpoint 契约，并在缺少 richer renderer 时退回文本桥接。
5. 旧版单选决策输入在过渡期仍可用，不会因为通用化而立刻失效。

## 实施阶段建议

### 已落地基线

- 通用 `DecisionCheckpoint / DecisionSubmission` contract
- `current_decision.json` 持久化与结构化 submission 回写
- `confirm_decision` handoff + `decision_checkpoint` artifacts
- `~decide` debug / override + `1 / 2 / ~decide choose <option_id>` 兼容
- execution gate follow-up decision
- internal `ready_for_execution` + `execution_confirm_pending`

### 当前已完成

- 抽出通用 `decision_templates.py`
- 拆出 `decision_policy.py`
- 保持 planning-request 触发基线，同时把 checkpoint 构造收口到模板层
- 让 design-stage structured tradeoff candidates 直接复用同一套 checkpoint contract
- 让 `~compare` 输出 `compare_decision_contract` facade，供宿主复用同一套 decision bridge UI
- 把推荐项、推荐理由、最终选择与关键约束稳定写入 replay 摘要，并默认省略自由输入原文

### 下一阶段第一步

- 继续扩展更多非单选模板
- 把 richer templates 与 compare facade 边界继续向前推进
- 收口 compare facade 的边界，而不是提前并入共享 state 主链路
