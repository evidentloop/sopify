# Sopify 宿主接入规范 (Protocol v0)

本文定位: 宿主接入 Sopify 的规范入口。Convention 最小合规（§1–§5）+ Host Protocol Entry Contract（§8）均在本文覆盖。

**阅读地图：**

| 宿主能力 | 需要阅读的章节 |
|---|---|
| **convention_only** — 只按目录约定读写 blueprint/plan/receipt | §1–§5 |
| **payload_capable** — 已安装 payload bundle，可消费 prompt asset | §1–§5 + §8 + prompt asset |
| **deep_verified** — ~~完整 runtime gate / handoff / checkpoint~~ | [RETIRED in P8] 原 deep runtime 集成路径退场；§8 替换为 Host Protocol Entry Contract |

> **术语解耦**：本文承载文档披露梯度的入口定义，以 protocol 章节为主轴，后续层级衔接 prompt asset 与架构参考。KB SKILL 中的 L0/L1/L2/L3 是知识持久化分层（index → stable → active → archive），描述 AI 运行时的上下文消费顺序，两者不是同一套模型。

**文档披露梯度：**

| Layer | 名称 | 覆盖 | 定位 |
|-------|------|------|------|
| **0** | Protocol | §1–§3 | 协议基础：目录约定、必备文件、宿主义务 |
| **1** | Lifecycle | §4–§5 | 理解验证：生命周期样例、合规自检 |
| **2** | Integration | §6–§8 + prompt asset | 集成能力：外部契约、主体身份、Host Protocol Entry Contract |
| **3** | Reference | design.md · ADR-016 · ADR-017 | 架构参考：不进 prompt，不面向接入者 |

与宿主能力梯度的对应：convention_only 读完 Layer 0–1（§1–§5）；payload_capable 在 Layer 0–1 基础上加 prompt asset + §8；deep_verified ~~完整读至 Layer 0–2~~ [RETIRED in P8]，原 deep runtime 集成路径退场，新宿主走 §8 Host Protocol Entry Contract。Prompt asset 是 payload 的能力附加面，不单独改变章节阅读层级。

**权限边界：**

- 最小合规看本文；runtime/扩展契约以 `design.md` / ADR 为准
- `design.md` 负责架构分层、削减目标、runtime 参考实现、核心契约细节（含 state 文件、checkpoint、knowledge_sync）
- `ADR-016` 负责 Protocol-first 决策理据与演进路线
- `ADR-017` 负责 ActionProposal / Receipt 字段定义（含 ExecutionAuthorizationReceipt 字段规范）
- 本文不重复上述内容，只定义"宿主能不能只看这一页就接入"

**Reader Contract（读者定位）：**

- 普通用户：读 README / docs/how-sopify-works，不需要本文
- Host / LLM 日常运行：消费 prompt asset 中的 §8 摘要（4 步入口 + read budget + write boundary），不全量读本文
- Host adapter / compliance 实现者：读本文全文 + schemas

## 1. 最小必备目录结构

```
.sopify-skills/
├── project.md              # 项目技术约定（长期可复用）
├── blueprint/
│   ├── background.md       # 为什么存在、核心价值
│   ├── design.md           # 架构基线、核心契约
│   └── tasks.md            # 未完成长期项
├── plan/
│   └── YYYYMMDD_feature/   # 活动方案包
├── history/
│   └── YYYY-MM/            # 收口归档
├── state/                  # 运行态（runtime 管理，Convention 模式可省略）
└── user/                   # 用户偏好（可选）
```

**最小下界（Convention 模式）**：只需 `project.md` + `blueprint/` + `plan/` + `history/`。`state/` 和 `user/` 是 runtime 增强，Convention 模式下宿主自行管理等价状态。

## 2. 最小必备文件与字段

### Plan 方案包（P8 post-cutover 结构）

> plan.md 是唯一语义入口。方案包分三档（Progressive Disclosure），receipts 条件必备。

每个方案包是一个目录 `plan/<plan_id>/`，`plan_id` 命名规范：日期前缀 + 下划线分隔（如 `20260605_p8_protocol_kernel_runtime_retirement`），不允许连字符。

**三档分级：**

| 级 | 必备文件 | 适用场景 |
|---|---|---|
| **light** | plan.md | 小任务、单步修复、探索性提案 |
| **standard** | plan.md + tasks.md | 多任务、需逐项验收 |
| **architecture** | plan.md + design.md + tasks.md + receipts/ + assets/ | 架构级、协议级、状态模型变更 |

**plan.md 结构**：顶部推荐有 Plan Snapshot 区块（Goal / Status / Next / Task），然后是 8 必备章节（顺序固定）：

1. **Context / Why** — 触发条件、输入来源、为什么新包、为什么不做 X
2. **Scope** — 做什么
3. **Approach** — 怎么做
4. **Waves / Steps** — 分几步
5. **Key Decisions** — 关键决策（引用 design.md 章节）
6. **Constraints / Not-in-scope** — 硬约束 + 延后项
7. **Status / Progress** — 当前进度（任务多时拆到 tasks.md）
8. **Next** — 下一步动作

Plan Snapshot 缺失不阻断审计和接续；host 回退读取完整 plan.md。Plan Snapshot 不是目录索引、不是 state 文件、不是权威审计事实。

**receipts/ 规则（条件必备）**：managed plan 产生执行/验证事件时必须写到 `receipts/*.json`；finalize 时必须生成 `receipts/final.json`；light plan 如无 managed execution 可无 receipts/。命名规范 `exec_NNN / verify_NNN / final`。

**不加**：status.json / plan-level README.md / plan/\<id\>/handoff.json（handoff 单态，只在 state/）。

### blueprint 知识层

| 文件 | 最小内容 | 更新时机 |
|------|---------|---------|
| `project.md` | 项目名、工作目录、运行时目录 | 项目初始化时 |
| `blueprint/background.md` | 项目定位（≤3 段） | 目标变更时 |
| `blueprint/design.md` | 架构基线 | 方案归档后回写 |
| `blueprint/tasks.md` | 未完成长期项 | 方案归档后回写 |

### history 归档

归档目录 `history/YYYY-MM/YYYYMMDD_slug/`，在显式 finalize 时按需创建（archive on demand），至少包含：

| 文件 | 必需字段 | 说明 |
|------|---------|------|
| `receipt.md` | outcome, summary, key_decisions | 可审计收据 |

## 3. 宿主最小义务

宿主（Host）接入 Sopify 协议需满足以下最小义务：

| 义务 | Convention 模式 | Runtime 模式 |
|------|----------------|-------------|
| **读取 blueprint** | 必须。每轮开始前消费 `project.md` + `blueprint/` | 同左 |
| **结构化提案** | 推荐。将用户意图映射为 ActionProposal | 必须。走 Validator 写前授权 |
| **方案包管理** | 必须。创建/更新 `plan/` 下的方案包 | 必须。runtime 辅助 |
| **归档** | 必须。完成后归档到 `history/` 并写 receipt | 必须。runtime 辅助 |
| **knowledge_sync** | 推荐。归档时将稳定结论回写 blueprint | 必须 |
| **checkpoint 响应** | 推荐。遇到 clarification/decision 时暂停等用户 | 必须。runtime 强制（详见 §8.2） |
| **handoff 消费** | 推荐。读取上轮 handoff 恢复上下文 | 必须（详见 §8.2） |
| **Validator 校验** | 事后校验。最小交互流可不依赖 Validator 实时阻断，但正式合规与 receipt authority 仍由 Validator 事后校验提供 | 写前授权。Validator 是 pre-write authorizer |

**Convention 模式最小合规**：读 blueprint → 写方案包 → 归档。最小交互流不要求 Validator 实时阻断或 runtime state 文件；但要获得正式 receipt authority 和合规校验，仍需调用 Validator（可事后批量）。

## 4. 典型生命周期样例

### 样例 A: 正常方案流（Convention 模式）

```
1. 宿主读取 blueprint/{background,design}.md 理解项目上下文
2. 用户："添加暗色模式"
3. 宿主创建 plan/20260501_dark_mode/plan.md（含 title/scope/approach + 内联 tasks）
4. 宿主逐项完成 tasks，更新 plan.md 中 status → done
   - 可插拔点：用户可在此阶段引入外部工具（如 graphify 生成架构图、
     cross-review 做独立审查）强化 blueprint 或方案质量，不改变核心方案流
5. 宿主归档到 history/2026-05/20260501_dark_mode/receipt.md
6. 宿主将稳定设计决策回写 blueprint/design.md（knowledge_sync）
```

### 样例 B: 中断与恢复（跨 session / 跨模型 / 跨宿主接力）

```
1. 用户在会话 A（Claude Code）中开始方案，完成 2/5 任务
2. 会话 A 中断（用户关闭/网络断开/切换宿主）
3. 新会话 B（可以是不同宿主如 Cursor，或不同模型）启动，宿主读取：
   - blueprint/ 获取项目上下文
   - plan/20260501_dark_mode/plan.md 获取进度（内联 tasks: 2 done, 3 pending）
   - state/current_handoff.json（如有）获取上轮交接事实
   - history/ 获取已归档方案的决策记忆
4. 宿主从第 3 个 pending task 继续，无需用户重述上下文
   - 协议保证：任意 host/model 只要正确消费 blueprint + plan + handoff，
     就能基于同一项目记忆继续工作
   - 正式 receipt authority 和 compliance 仍由 Validator 事后校验提供
```

### 样例 C: Checkpoint — 需要用户决策

```
1. 宿主在实现过程中发现两种可行方案（CSS variables vs. class toggle）
2. 宿主暂停执行，向用户展示选项
   - Convention 模式：宿主直接在对话中展示选项
   - Runtime 模式：写入 state/current_decision.json，handoff 暴露 checkpoint_request
3. 用户选择方案 A
4. 宿主记录决策到 plan.md（内联在方案正文或 tasks 备注中），继续执行
   - receipt.md 仅在最终归档时生成，不在进行中承载决策状态
```

### 样例 D: 归档失败与回退

```
1. 宿主尝试归档，但方案包缺少必需字段（如 plan.md 无 scope 或 approach）
2. Validator 返回 validation_failed（或 Convention 模式下宿主自检失败）
3. 宿主不执行归档，向用户报告缺失项
4. 用户补全后重新归档
5. 归档成功，receipt.md 记录 outcome + 关键决策
```

## 5. 协议合规检查清单

宿主实现者可用此清单自检最小合规：

- [ ] 能读取 `.sopify-skills/project.md` 并识别项目名
- [ ] 能读取 `blueprint/` 三件套并作为上下文消费
- [ ] 能在 `plan/` 下创建结构化方案包
- [ ] 方案包至少包含 `plan.md`（title/scope/approach + 内联 tasks/status）；standard/full 另需单独 tasks.md 等
- [ ] 能将完成的方案归档到 `history/YYYY-MM/` 并生成 `receipt.md`
- [ ] 归档后能将稳定结论回写 blueprint

以上全部通过即为 **Convention 模式最小合规**。如需 Runtime 模式，另需满足 Validator 接入（见 design.md 核心管线）。

## 6. Integration Contract（外部能力接入契约）— *informative；Verifier / ExecutionAuthorizationReceipt 为 normative 例外*

> 本节整体 informative。其中 **Verifier**（§6.Verifier）和 **ExecutionAuthorizationReceipt**（§7 内引用）已升格为 normative（P1.5-D）；其余子段仍为 draft。

Sopify 不做生产/验证/知识处理节点本身，但拥有证据规范、授权判定、收据生成这几个控制节点。外部能力通过以下契约接入 Sopify 的收敛链。

### Producer（外部生产器）

外部生产器（LLM、宿主、代码执行器）交给 Sopify 的是 **ActionProposal**：

| 字段 | 说明 |
|------|------|
| `action_type` | 要做什么（plan / develop / archive / consult …） |
| `side_effect` | 会产生什么副作用 |
| `confidence` | 生产器自评置信度 |
| `evidence` | 支撑提案的事实引用 |

Sopify 接收后由 Validator 授权，不由生产器自行决定执行。

### Verifier（外部验证器）

> **升格状态**：本子段从 informative 升格为 **normative**（P1.5-D 升格）。字段约束使用 RFC 2119 表述。消费路径为 normative 声明。evidence attachment wire format 为 deferred。

外部验证器（cross-review、测试框架、lint 等）回传给 Sopify 的是 **verdict + evidence**：

| 字段 | RFC 2119 | 说明 |
|------|----------|------|
| `verdict` | **MUST** | 可被 Validator 消费的判定标识。具体值域可由 Verifier 实现细化；canonical verdict 值域与完整 mapping 待后续里程碑正式化 |
| `evidence` | **MUST** | 可 machine-readably 消费的证据（如文件路径、行号、代码片段等） |
| `source` | **MUST** | 验证器来源标识（如 `cross-review:v1`、`unittest`），供 Validator 和宿主解释 evidence provenance |
| `scope` | **SHOULD** | 验证范围（全量 / 增量 / 特定文件）。缺失不阻断 contract 成立，但会降低证据解释力 |

**注意**：Verifier 输出的是 **evidence 输入**，不是授权输出；只有 Validator 有权授权。

#### Verifier 消费路径

**verdict**：Validator **MUST** 将 Verifier verdict 视为授权风险因子。Verifier **MAY** 使用实现特定的更细粒度枚举；Validator 与宿主 **SHOULD** 能将其归一化到稳定语义层。canonical verdict 值域与完整 normalization mapping 待后续里程碑正式化；在此之前，verdict **MUST NOT** 被当作自授权信号，而只能作为风险/证据输入。

**evidence**：Verifier evidence **MUST** 进入 Sopify 的后续证据链。当存在结构化 handoff 承载位点时，**SHOULD** 挂载到 handoff。receipt / history / plan metadata 的具体 attachment 位置与 wire format 继续 **deferred**。

**source**：**MUST** 标识验证器来源，供 Validator 和宿主解释 evidence provenance。是否基于 source 做差异化处理不在当前 normative scope。

#### Verifier Read-Only Contract（P8 升格）

P8 新增 Verifier 写入边界约束：

| 规则 | RFC 2119 |
|---|---|
| Verifier **MUST** emit verdict + evidence + source | MUST |
| Verifier **MUST** be read-only: true | MUST |
| Verifier **MUST NOT** write `state/**`, `plan/**`, `blueprint/**` | MUST NOT |
| Verifier **MUST NOT** invoke `execute_command` or `modify_files` | MUST NOT |
| Verifier verdict **MUST NOT** be treated as self-authorization | MUST NOT |

违反 read-only 约束的 Verifier verdict 降级为 advisory（不自授权）。具体 bridge enforcement 不在 P8 必须范围，后续由 cross-review 独立 slice 实现。

### Knowledge Provider（外部知识工具）

外部知识工具（graphify、摘要生成器等）沉淀给 Sopify 的是 **artifact + reference**：

| 字段 | 说明 |
|------|------|
| `artifact_type` | 产出类型（graph / summary / diagram / analysis） |
| `artifact_ref` | 产出定位（repo-relative 路径或 URI + digest） |
| `reference_target` | 该产出关联的 plan / blueprint 节点 |
| `stability` | draft / stable（只有 stable 才可进入长期知识层） |

只有满足沉淀准入门槛（跨任务可复用 + 影响后续授权/验证 + 已稳定 + 可 machine-readably 引用）的产出才由 knowledge_sync 回写 blueprint。

### Sopify 的统一出口

Sopify 把上述三类输入统一收敛为：

| 出口 | 承载内容 |
|------|---------|
| `receipt` | 授权回执（见下方 ExecutionAuthorizationReceipt） |
| `handoff` | 交接事实：当前状态 + 验证结果 + 下一步建议 + checkpoint（如有） |
| `history` | 归档事实：outcome + key_decisions + verification_evidence |
| `blueprint` | 长期知识：只有稳定结论（via knowledge_sync） |

#### ExecutionAuthorizationReceipt — *[RETIRED in P8]*

> **P8 退场声明**：ExecutionAuthorizationReceipt 在 P8 中显式退场。pre-execution authorization model（runtime gate 在执行前生成的机器授权回执）不再适用；P8 删除 runtime gate 后，不存在稳定的"执行前授权时刻"。post-P8 审计主链改由 `plan/<id>/receipts/*.json`（过程审计资产）+ `history/<id>/receipt.md`（最终审计收据）承担。这不是 EAR 的同义替代，而是产品承诺切换：从 pre-execution authorization proof 切到 post-execution evidence chain。详见 P8 plan.md 决策 #15 / #18 和 design.md §4.7。

<details>
<summary>Legacy 字段规范（保留为历史参考）</summary>

ExecutionAuthorizationReceipt 是 execute_existing_plan 授权通过后生成的机器事实，回答"这次执行被谁、基于哪个 revision、通过什么授权"。

**Receipt MUST 包含以下字段：**

| 字段 | 类型 | 语义 |
|------|------|------|
| `plan_id` | string | 目标 plan 的唯一标识（plan 目录名） |
| `plan_path` | string | 目标 plan 的 workspace-relative 目录路径 |
| `plan_revision_digest` | string | plan.md 内容的 SHA-256 hex digest |
| `gate_status` | string | 生成时 ExecutionGate.gate_status 的值 |
| `action_proposal_id` | string | 触发授权的 ActionProposal 唯一标识（engine 确定性生成，MUST NOT 由 host 指定） |
| `authorization_source` | object | `{ kind: "request_hash", request_sha1: string }` |
| `fingerprint` | string | `sha256(canonical_json({plan_id, plan_path, plan_revision_digest, gate_status, action_proposal_id}))` |
| `authorized_at` | string | ISO 8601 UTC 时间戳 |

**Fail-closed 不变量：**

- Validator 在处理 execute_existing_plan 请求时 MUST 从持久化的 authoritative runtime state 读取已有 receipt
- 如 `plan_revision_digest` 与当前 plan.md 实际 SHA-256 不匹配，Validator MUST 返回 DECISION_REJECT
- 如 `plan_path` 指向的 plan 目录不存在，Validator MUST 返回 DECISION_REJECT
- 如 `gate_status` 与当前 ExecutionGate.gate_status 不匹配，Validator MUST 返回 DECISION_REJECT
- Stale receipt MUST NOT 降级为 consult，MUST NOT 自动 re-authorize

**命名对齐注释**：`plan_revision_digest`（receipt 字段）是通用 Subject Identity 中 `revision_digest` 在 plan subject 场景的特化命名，不是独立概念。两者 MUST NOT 长期并存为不同语义。

</details>

## 7. Subject Identity & Review Wire Contract

> **升格状态**：本节中 Subject Identity 的通用字段与核心语义（subject_type / subject_ref / revision_digest / 取证优先级）为 **normative**（其中 `subject_type` 仅 `"plan"` 为 normative，其余值域保留 draft）。Bound-subject local actions 的 Subject Binding 为 **normative**（P1 升格 execute_existing_plan；P2 扩展到 modify_files / checkpoint_response / cancel_flow 条件性）。Review Wire Contract 部分仍为 informative/draft，待后续里程碑联动升格。
>
> 本节定义跨宿主协作中"操作的是谁"的最小 machine contract（wire level）。适用于 review、execute_existing_plan、modify_files、checkpoint_response、cancel_flow、archive 等所有需要绑定主体的场景。收敛策略性规则（轮数上限、severity 判定、冲突解决）归 `design.md` Default Workflow 策略。

### Subject Identity（跨场景通用）

每个 bound-subject side-effecting action 必须携带明确的主体身份，以保证跨宿主可追溯、可验证。Subject identity 是 protocol 层契约，validator 和 runtime 都是消费方。Subject-free actions（`consult_readonly`、`propose_plan`）不要求主体；`archive_plan` 使用独立的 `archive_subject`（见 §5）。

| 字段 | 说明 |
|------|------|
| `subject_type` | 被操作对象类型（`plan` 为 normative；`code` / `architecture` 保留 draft） |
| `subject_ref` | 对象定位：workspace-relative 路径（如 `.sopify-skills/plan/20260501_dark_mode`） |
| `revision_digest` | 版本标识：目标对象的确定性快照标识（SHA-256 hex digest），保证操作绑定到确定性快照 |

> **命名对齐注释**：通用 Subject Identity 使用 `revision_digest`；ExecutionAuthorizationReceipt 使用 `plan_revision_digest`。后者是前者在 plan subject 场景的特化命名，不是独立概念。实现时 MUST NOT 混用或创建不同语义。

**主体取证优先级**（当 subject 未显式给出时的解析链路）：

1. `explicit_reference` — 用户或 ActionProposal 显式指定
2. `self_reference` — 当前上下文中可唯一推定的活跃主体
3. `new_plan_intent` — 检测到新建意图，不绑定已有主体
4. `stable_handoff_evidence` — 上轮 handoff 中稳定的主体引用
5. `current_plan_anchor` — 全局 current_plan 作为兜底

**Validator 消费边界**：validator 基于 subject identity 做 admission / authorization 判定。subject 不明确时 validator MUST 拒绝而非猜测。

**Runtime 消费边界**：runtime 作为参考实现消费 protocol 定义的 subject identity contract，MUST NOT 自行定义主体解析语义。

### Bound-Subject Local Actions 的 Subject Binding — *normative*

以下 action_type 为 **bound-subject actions**，MUST 在 ActionProposal 中通过 `plan_subject` 字段块携带主体身份：

- `execute_existing_plan` — 执行已有 plan（P1 升格）
- `modify_files` — 在已绑定 plan 上下文中修改代码文件（P2 升格）
- `checkpoint_response` — 回应已绑定 plan 的 pending checkpoint（P2 升格）

**条件性 bound-subject action**：

- `cancel_flow` — 当取消目标是已绑定 plan 的活动流时 MUST 携带 `plan_subject`；其他取消场景不强制。Validator 在 `plan_subject` 存在时做全套 admission check，缺失时不 REJECT（P2 升格）

宿主 MUST 在 ActionProposal 中通过 `plan_subject` 字段块携带以下信息：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `subject_ref` | string | MUST | 目标 plan 的 workspace-relative 方案目录路径（如 `.sopify-skills/plan/20260501_dark_mode`） |
| `revision_digest` | string | MUST | 该目录下 `plan.md` 文件内容的 SHA-256 hex digest |

**可携带规则**：

- 跨 session 接力时，新 session MUST 通过 handoff 或 plan 文件重新建立 subject binding，MUST NOT 隐式继承前 session 的绑定
- plan 内容变更（revision_digest 不匹配）后，已有 ExecutionAuthorizationReceipt 自动失效
- Validator 在 admission 阶段 MUST 校验 `subject_ref` 存在性 + `revision_digest` 一致性
- `subject_ref` MUST 是 workspace-relative 路径，MUST 以 `.sopify-skills/plan/` 开头，MUST NOT 包含 `..` 或绝对路径
- 对 bound-subject actions：缺少 `plan_subject`、`subject_ref` 指向不存在的 plan、或 `revision_digest` 与文件实际内容不匹配时，Validator MUST 返回 DECISION_REJECT（不降级 consult）
- 对 `cancel_flow`：上述检查在 `plan_subject` 存在时适用；缺失 `plan_subject` 时不触发 REJECT

> **Legacy mapping 注释**（informative）：
>
> 现役 machine truth 中，plan 主体的表达形式与上述 canonical subject binding 存在映射关系：
>
> | 现役路径 | canonical 映射 |
> |---------|--------------|
> | `current_plan.path`（state.py） | → `plan_subject.subject_ref`（workspace-relative 目录路径） |
> | bare `~go` 隐含的 plan 指向 | → 应显式携带 `plan_subject`，当前未携带 |
> | `review_or_execute_plan`（action_projection） | ✅ P3a 已收口：plan review 语义迁移至 `continue_host_develop` + `plan_generated` stage |
>
> 以上映射为 informative 注释，不构成规范性要求。现役路径的 canonical 化属于 P3a contract-aligned cleanup 范围。

### Action Applicability Matrix — *normative*

以下矩阵定义每个 action_type 与 subject / delta / side_effect 字段的适用关系。Parser 和 Validator 以此为准入依据。

| action_type | plan_subject | archive_subject | side_effect_delta | canonical side_effect | 分类 |
|---|---|---|---|---|---|
| `consult_readonly` | 禁止 | 禁止 | 禁止 | `none` | subject-free |
| `propose_plan` | 禁止 | 禁止 | 禁止 | `write_plan_package` | subject-free |
| `execute_existing_plan` | MUST | 禁止 | 禁止 (P2) | `write_files` | bound-subject |
| `modify_files` | MUST | 禁止 | SHOULD (`write_files` 时) | `write_files` | bound-subject |
| `checkpoint_response` | MUST | 禁止 | 禁止 | `write_runtime_state` | bound-subject |
| `cancel_flow` | 条件性 | 禁止 | 禁止 | `none` | 条件性 bound-subject |
| `archive_plan` | 禁止 | MUST | 禁止 | `write_files` | 独立主体 |

**字段语义**：

- **MUST**：宿主 MUST 携带，缺失时 Validator 返回 REJECT
- **SHOULD**：宿主 SHOULD 携带，缺失时 Validator 不 REJECT（delta 为可选变更清单）
- **条件性**：取消 bound plan flow 时 MUST 携带；其他场景不强制
- **禁止**：宿主 MUST NOT 携带，Parser 在解析阶段拒绝
- **canonical side_effect**：该 action_type 唯一合法的 side_effect 值，不匹配时 Validator 返回 REJECT（P2 pairing 闭合）

> **side_effect_delta 的首个 runtime acceptance scope（P2）**：仅 `modify_files` 消费 `side_effect_delta`。`execute_existing_plan` 的 delta 支持为 future hook（蓝图留口，P2 不进 runtime acceptance）。详细 schema 见 `design.md` P2 side_effect_delta 段落。

### Review Subject Identity — *informative/draft*

审查是 subject identity 的一个消费场景。每次审查必须绑定被审查对象，字段复用上述 Subject Identity 定义。本小节仍为 informative/draft，待后续里程碑联动升格。

### Review Record Shape

审查记录遵循 Verifier contract（§6），附加跨宿主审查所需字段：

| 字段 | 说明 |
|------|------|
| `review_id` | 唯一审查标识 |
| `reviewer_source` | 审查来源标识（`host:cursor` / `host:claude-code` / `skill:cross-review`） |
| `convergence_action` | `accept` / `revise` / `blocked` / `escalate` |
| `revision_suggestions` | 具体修改建议（可选） |

### 存储位置

审查记录作为 evidence 进入 handoff 或 plan metadata，归档时纳入 receipt 的 verification_evidence。evidence 挂载的 normative 消费规则见 §6 Verifier 消费路径。evidence attachment 的 wire format（字段 schema、路径约定）为 deferred，不属于当前 normative scope。

## 8. Host Protocol Entry Contract（P8 post-cutover）

> 本节替代 pre-P8 "Deep Host 运行时集成协议"。P8 删除 runtime gate 后，入口约束由 host prompt asset + 本协议共同承担，不新造 CLI 或 state 文件。原 §8.1–§8.5 deep runtime 集成内容退场，保留一行 retirement note 指向历史背景。

### 8.1 Request Admission Before Continuation

宿主/LLM 在 workspace 中检测到 `.sopify-skills/sopify.json` 或 `.sopify-skills/` 时，MUST 先形成 runtime-independent ActionProposal，判断用户请求属于以下哪类：

| 用户意图 | Host 行为 |
|---|---|
| consult（问问题、澄清、解释、代码阅读） | 不读取 active_plan 接续链；必要时只读 blueprint/project 轻上下文 |
| quick_fix（unmanaged 单步修复） | 不切 active_plan，不强制写 receipts |
| new_plan（新建 managed plan） | 创建方案包；如已有 active_plan，先确认切换/合并/暂停 |
| continue_plan（继续当前/上次 plan） | 执行 4 步 protocol entry（§8.3） |
| finalize（归档） | 进入 finalize 工作流 |
| ask_user | 响应用户，不自动接续 |

**关键约束**：protocol 不要求所有用户请求都自动接续 active_plan。consult / unmanaged quick_fix 默认不进入 4 步 protocol entry。

### 8.2 触发条件

4 步 protocol entry 仅在以下条件全部满足时执行：

1. workspace 存在 `.sopify-skills/sopify.json` 或 `.sopify-skills/`
2. ActionProposal 指向 managed plan / continuation / finalize
3. 非 consult / unmanaged quick_fix 路径

### 8.3 入口读顺序（4 步）

```
1. state/active_plan.json         → 定位 plan_id（如无 → consult / new-plan）
2. plan/<id>/plan.md              → 语义入口：做什么 + 进度（真相源）
3. state/current_handoff.json     → 恢复提示 + 是否等用户（required_host_action）
4. plan/<id>/receipts/            → 取最新 1-3 个 receipt，知道"哪些被验证过"
```

**顺序设计原则**：active_plan 定位后**先读 plan.md 建立语义真相**，再读 current_handoff 作为恢复提示——避免 handoff 反过来变成第二真相源。

### 8.4 读取预算红线

| 资产 | 默认读取 | 何时扩展 |
|---|---|---|
| `state/active_plan.json` | 全量（应只有 plan_id） | 进入 managed plan / continuation / finalize 时 |
| `state/current_handoff.json` | 全量（必须保持短小） | active_plan 存在时 |
| `plan/<id>/plan.md` | 优先读 Plan Snapshot 区 | 评审方案/执行任务/状态冲突时展开完整 plan.md |
| `plan/<id>/tasks.md` | 默认不读 | 执行 standard/architecture 任务时 |
| `plan/<id>/design.md` | 默认不读 | 架构取舍/schema/风险判断需要时 |
| `plan/<id>/receipts/` | 最新 1-3 个 receipt 或 final.json | 审计/回滚/争议时 |
| `assets/` | 默认不读 | 当前任务明确需要时 |
| `blueprint/protocol.md` | 默认不全量读 | 协议实现/合规检查时 |

**MUST NOT**：protocol entry 默认不得全量读 protocol.md / design.md / receipts/ 目录。compliance smoke 必须检查此约束。

### 8.5 Receipts Latest-Only 算法

receipts/ 目录的读取是精确的 latest-only 查找，不是全量扫描：

1. 列出 `plan/<id>/receipts/` 目录
2. 如果存在 `final.json`，始终包含（不受 N 限制）
3. 其余 receipt 按 timestamp 降序取最新 1-3 个
4. timestamp 缺失时按 provenance.receipt_id 数字部分兜底排序
5. 只读 verdict / evidence / provenance / timestamp 字段

host MUST NOT 默认全量扫描 receipts/ 内容。

### 8.6 写回边界

写 `state/active_plan.json`、`state/current_handoff.json`、`plan/<id>/receipts/*.json` 时 MUST 走 `sopify_writer`。Host prompt 负责 request admission 与默认 spec workflow 入口，不负责生成机器真相、不生成计划优先级、不执行验证。

### 8.7 链路失败模式（fail-open）

| 步 | 文件缺失时 host 行为 |
|---|---|
| 1 active_plan 缺失 | 进入 consult 模式或提示 new-plan；不阻断 |
| 2 plan.md 缺失 | 异常 → 提示用户 state 不一致 |
| 3 current_handoff 缺失 | 正常 → 仅按 plan.md 进度接续 |
| 4 receipts/ 缺失或空 | 正常 → 不假设任何动作已验证 |

### 8.8 读后分叉

| 读到的事实 | Host 行为 |
|---|---|
| 无 active_plan | consult / new-plan |
| 用户请求不指向当前 active_plan | 不自动接续；按 ActionProposal 处理 |
| active_plan 存在且 continue_plan | 按 plan.md + tasks.md 继续 |
| required_host_action = answer_questions | 只展示问题并等待回答 |
| required_host_action = confirm_decision | 只展示选项并等待确认 |
| plan.md 与 handoff 冲突 | 以 plan.md 为准；提示 state conflict |

### 8.9 State 文件索引（P8 post-cutover: 2 文件）

| 文件 | 说明 | Git |
|---|---|---|
| `state/active_plan.json` | 定位：当前 plan_id | ignored |
| `state/current_handoff.json` | 恢复：上次停哪 + required_host_action | ignored |

P8 删除的 state 文件：`current_run.json`、`current_plan.json`、`current_clarification.json`、`current_decision.json`、`current_gate_receipt.json`、`current_archive_receipt.json`、`last_route.json`。

`required_host_action` canonical 值域（5 个）：

| 值 | 语义 |
|---|---|
| `continue_host_develop` | 宿主继续代码修改 |
| `answer_questions` | 宿主展示缺失事实，等待用户补充 |
| `confirm_decision` | 宿主展示设计分叉，等待用户选择 |
| `continue_host_consult` | 宿主继续问答 |
| `resolve_state_conflict` | 状态冲突，需宿主介入 |

### 8.10 Retirement Note

本节（§8）在 P8 中整体替换。pre-P8 §8 "Deep Host 运行时集成协议"定义了 gate-first 义务、runtime gate entry、deep host adapter、runtime helper 索引等内容，适用于 deep_verified 宿主。P8 删除 runtime gate 和 deep host adapter 后，原 §8.1–§8.5 全部退场。原 deep runtime 集成的历史背景见 git history。

### 8.11 ActionProposal 角色声明

ActionProposal 是 runtime-independent workflow/admission 层概念，用于 host/default workflow 做请求准入与分发。它不是 P8 must-freeze schema，不作为 runtime gate 输入（runtime gate 已在 P8 退场），不新增核心 schema 文件。P8 不冻结完整 ActionProposal schema，只要求宿主先判断用户请求意图，再决定是否进入接续读链。

## 非目标

- 不定义 Validator 实现细节（见 ADR-017）
- 不定义 Runtime 内部架构（见 design.md "Runtime 五层架构"）
- 不定义 state 文件 schema（归 runtime 管理）
- 不定义 SKILL.md 编排规范（待 ADR-016 Step 3 稳定后补充）
- 不替代 design.md 的契约定义，只提取"不依赖 runtime 也成立"的最小子集
- 不定义收敛策略性规则（轮数上限、severity 判定等归 design.md Default Workflow 策略）
