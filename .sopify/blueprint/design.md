# 蓝图架构与契约

本文维护模块边界、部署、所有权和设计取舍；可携带规范由 [protocol.md](./protocol.md) 维护，当前工作见 [tasks.md](./tasks.md)。

## 产品定位

Sopify 在现有 AI 编程宿主上保存方案、决策、交接与验证证据，使项目记录随仓库传递。宿主执行任务，Sopify 提供文件协议、受控写入及可替换的默认工作流；跨宿主行为仍需对应宿主的真实验证。

runtime gate、EAR、旧多文件 state、route families、运行时渲染与 deep adapter 已退场；沿革及旧 keep-list 见 [P8 归档设计](../history/2026-06/20260605_p8_protocol_kernel_runtime_retirement/design.md)、[P8 方案](../history/2026-06/20260605_p8_protocol_kernel_runtime_retirement/plan.md) 和 [ADR-017](./architecture-decision-records/ADR-017.md)，不再在当前蓝图复制历史表格。

## 产品分层

| 层 | 职责 | 实现 |
|---|---|---|
| Protocol Kernel | 可携带目录、主体与版本契约、受控 receipts / handoff / archive | protocol.md、`sopify_contracts/`、`sopify_writer/` |
| Default Workflow | 按意图分析、规划、实施、验证和知识同步 | host prompt、阶段 Skill、共享输出契约 |
| Host / Skill Adapters | prompt 与 payload 安装、workspace bootstrap、状态检查 | `installer/`、host registry、分发入口 |

- **Core promotion rule**：只有影响跨宿主互操作、receipt validity、archive admissibility 的契约才能进 Protocol Kernel。
- Default Workflow 消费 Kernel 契约，不自行定义准入语义；宿主可以采用自己的工作流。
- 外部工具输出只是证据或知识输入，不自授权；进入正式 receipt 或长期知识前分别遵守协议准入与 `knowledge_sync`。
- Sopify 不承担模型推理、真实代码执行或 agent 调度。Orca 等宿主负责执行协调，可选配合方式见 [Orca 文档](../../docs/orca.md)。

## 模块与部署

| 模块／资产 | 责任与依赖边界 |
|---|---|
| `sopify_contracts/` | schema、共享数据结构、方案结构及版本计算；公开 Python 导出保留 |
| `sopify_writer/` | 确定性结构/版本校验、receipt 写入、标准归档；依赖 contracts，不生成方案语义 |
| `skills/{zh,en}/` | prompt 单一来源；阶段规则、模板与输出契约按职责分层 |
| `skills/catalog/`、`skills/hosts.yaml` | builtin 清单及官方宿主分发元数据 |
| `installer/hosts/` | 每个宿主的路径、指令表面和能力声明 |
| `installer/payload.py`、`bootstrap_workspace.py` | 全局 bundle 分发与项目激活；bootstrap helper 必须能脱离源码仓库运行 |
| `installer/inspection.py` | status / doctor，区分安装事实与宿主行为证据 |
| `scripts/sopify_protocol_check.py` | 文件协议合规 smoke，不替代模型会话验证 |

公开安装器只下载同 ref 源码并调用 Python 安装器；默认用户入口、repo-local 安装、可选组件和卸载见 [getting-started](../../docs/getting-started.md)。公开安装要求 Python 3.11+，不自动安装解释器或修改用户环境。

全局 prompt、Skills 和 payload 按 adapter 放置。项目 `.sopify/sopify.json` 只定位 workspace 激活与所选 bundle，不是任务进度真相。旧 bundle 布局仍有升级兼容；不得把兼容读取分支当作已退场执行引擎删除。

独立部署的 bootstrap helper 与 Cursor Hook 保留窄范围 fallback；抽取共用逻辑时必须维持离开源码仓库后的可执行性。

## 设计原则

### Convergence-first

收敛链为 produce → verify → record evidence → settle。按真实风险补证据，达到交付条件即停止，不默认追求更多框架或更完整流程。只有跨任务可复用、已稳定、可引用且影响后续验证的结论进入长期知识。

### Wire-composable

组合边界是文件和机器契约，不是 Python 调用链或聊天历史。主体与版本按 [Protocol §7](./protocol.md) 建立，session 标识只作 provenance；接续处理遵循 §8，不另造 session 状态。

### Surface-shared

blueprint、plan、history、receipts 构成共享项目记录。用户明确要求接续时再恢复；本地 handoff 是恢复提示，不能替代方案正文，也不能证明动作已经验证。

## Default Workflow 策略

Analyze 确认目标、交付物与证据；Design 负责取舍、readiness、方案正文；Develop 负责批准范围内的实施与验证；KB 负责长期知识政策，Templates 负责知识文档结构。单个 Skill 可直接被宿主调用，仍共享协议和授权边界。

方案审查的设计基线是 `draft → under_review → [accept → approved | revise → draft | blocked → escalate]`：至少一轮无阻塞 finding 并被接受、用户明确 override，或达到默认三轮上限后停止继续审查。多审查者中有 blocked 则整体 blocked，accept 与 revise 混合取 revise。这些是宿主/owner 消费的策略，不是独立状态机；主体和 Verifier 规则分别由 Protocol §7、§6 定义。

## 核心管线与契约

用户意图 → 宿主请求准入 → 宿主执行 → writer 校验并记录 → 按明确请求收口。

- 宿主执行真实工作并负责语义判断；外部产出、模型自述和 verifier verdict 均不构成自授权。
- writer 不生成或修改方案语义；目录迁移例外仅为 `finalize_plan` 经版本校验后的标准归档。
- subject identity、plan_subject、action-effect pairing 的规范来源是 [Protocol §7](./protocol.md)，不在此复制字段表。
- `side_effect_delta` 保留为 `modify_files` 的可选文件级说明（`path`、`change_type: added|modified|removed`），不替换标量 side_effect；路径限定 workspace-relative、无绝对路径和 `..`，不引入 plan-scope 判断。其他动作不因此获得 delta 支持。
- 显式 finalize 的版本检查、写 final/history receipt、目录迁移和成功后清理 state，按 [Protocol §8](./protocol.md#8-host-protocol-entry-contractp8-post-cutover) 执行；失败保留源方案与 state，不自动修复。
- Checkpoint 仅 clarification / decision，通过 handoff 的 `answer_questions` / `confirm_decision` 表达；等待期间不物化正式 plan。
- `knowledge_sync` 继续使用 project/background/design/tasks 的 `skip / review / required`：skip 不检查，review 在 finalize 前复核，required 未完成阻断 finalize。具体读取与保留政策由 KB Skill 维护。

## 削减预算与持久化边界

| 维度 | 当前目标 | Hard Max |
|---|---:|---:|
| Checkpoint types | 2：clarification / decision | 2 |
| required_host_action | 5，值域见 Protocol §8.9 | 6 |
| Core state files | 2：active_plan / current_handoff | 2 |

突破 hard max 只能通过 ADR，须说明替代了什么、为何不能放进既有 artifacts/status/hint。宿主工作流路由不再另设内核枚举预算。

| 资产 | 所有权与 Git 边界 |
|---|---|
| blueprint / project.md | 长期知识，tracked；不存一次性实现和重复方案正文 |
| plan / history | 方案及证据，tracked；归档保留完整包 |
| user/preferences.md / feedback.jsonl | 长期偏好与原始反馈，tracked，不能当缓存删除 |
| state/active_plan.json / current_handoff.json | writer 管理的本地定位与恢复提示，gitignored |

协议入口、读取预算、状态缺失降级和审计写回规则只在 [Protocol §8](./protocol.md#8-host-protocol-entry-contractp8-post-cutover) 维护。新宿主不得将已退场 state 文件或输出措辞当作机器真相。

## 外部消费面与兼容性

| 消费面 | 保留边界／来源 |
|---|---|
| Verifier verdict/evidence/source 与 plan 主体身份 | Protocol §6、§7 的 normative 语义 |
| RuntimeHandoff、方案版本与 writer API | contracts / writer 的公开定义；旧公开模型不因本轮清理而删改 |
| 安装参数 | 保留 `--target`、`--ref`、`--workspace`、`--language`、`--no-copilot`、`--with-evidentloop`、`--verbose`、`-h`；分发内部参数不成为用户接口 |
| builtin catalog | schema 与发布清单保持；具体 Skill 枚举变化需正常评审 |
| 持久化资产 | 上表的知识、方案、历史与偏好不作为冗余缓存删除 |

`host_support` 只声明官方适配器能把 Skill 语义交付到对应宿主的支持界面并由宿主消费。它不等同于原生 Skill discovery，也不证明该宿主已经完成 E2E；支持等级、已验证能力和入口形态继续由 `HostCapability` 表达。

## 宿主能力治理

消费能力描述与产品支持档位是两类事实：convention_only 只消费文件约定；payload_capable 有稳定 payload 与 prompt 表面；protocol_verified 需要协议、receipt、resume 等证据。当前产品的支持表见 [README](../../README.zh-CN.md)，注册与能力声明见 `installer/hosts/`，不在蓝图重复安装命令或维护第二张支持表。

新宿主先取得安装、发现、实际按规则执行三个层次的独立证据，再声明支持范围；baseline 不自动升级为协议验证。接入矩阵、公共改动位置与测试模板统一见 [host-onboarding](../../docs/host-onboarding.md)。

接续消费 active_plan / handoff / receipts，交互消费 required_host_action，审计消费 receipts 与 history。具体读取义务由 Protocol 定义，不通过安装动作推断。

### Prompt 镜像治理

- 宿主安装产物从 `skills/{zh,en}` 渲染，不维护另一棵手工源树。
- Copilot 内联阶段规则、共享契约及必要文档模板，不重复入口导航或回复示例；tree-only scripts 不内联、不产生假路径。
- Cursor 的薄 Plugin Rule 与 CLI 顶层 Skill 复用同一套阶段资源；模型自动选择和文件放置分别取证。
- 共享的宿主指令文件（如 `CLAUDE.md`、`AGENTS.md`）与 Copilot 一样只写 managed block，块外用户内容原样保留；旧版整份安装按稳定的首尾行迁移，标记异常时不写入。
- 只发现一层 Skill 目录的宿主（Antigravity、Trae）共用一套扁平 `sopify-*` 布局；没有全局规则文件的宿主以顶层入口 Skill 承担路由。
- 入口规则写明已安装 payload 中 bootstrap helper 与 writer 的位置：首次受管写入前，或本机 state 未被忽略时，先调用 helper；machine truth 通过 writer 库 API 写入，不提供 writer CLI。
- `tools / disallowed_tools / allowed_paths / requires_network` 等 Skill 字段目前是声明，不是独立权限执行引擎。

### 可选 Verifier 与 MCP

Verifier 不默认安装或运行。配套安装行为唯一说明在 [getting-started](../../docs/getting-started.md)，证据输入和写回边界唯一规范在 Protocol §6；安装来源不进入 receipt 语义。

repo-local MCP server 为 `scripts/sopify_mcp_server.py`，只提供确定性文件事实、协议检查及受 guard 约束的 receipt 写入。Codex 持久注册和 Claude 会话级只读调用已有证据，但后者不等于持久注册；试点记录见 [MCP 归档](../history/2026-07/20260626_mcp_tool_plane_pilot/plan.md)。依赖供给、payload 打包、doctor 集成和更多宿主注册仍需重复痛点及对应实测，不升格为默认产品要求。

## 公开页面

`index.html` / `zh-CN.html` 共用 `assets/sopify-site.css` 与 `sopify-site.js`。页面使用已验证的支持范围；架构图作为技术结构入口，Product Form 双语 SVG 保留给 README，不重复加入首页。

## 设计预算与硬约束

- 产品目标保持少概念、少前置：首次上手不超过三个主要动作，初始化必需持久化文件目标不超过四个，默认 workflow 必需 contract 目标不超过五个；这是设计预算，不是新 gate。
- 新概念必须替换旧概念或证明不增加概念预算；不为未知未来预建状态、锁或调度器。
- writer 只处理确定性协议事实；host prompt 不生成机器真相，确定性层不做自然语言推断。
- develop_mode 只作 hint，归档结果不是 required_host_action；权限与主体仍按正式协议判断。
- 不以 router 文案补丁替代契约修复；新增方向须有明确范围、取舍和证据，优先降低宿主接入与维护成本。

## 外部设计影响与 ADR

外部影响沿用 T0 Reference（方案中注明）、T1 Adoption（有实现和验证路径，符合 ADR）、T2 Principle（已实现、dogfood 无回退并通过删除测试）的准入区分，不因此预建能力。历史来源与取舍查对应归档；当前代码和协议优先。

| ADR | 责任 |
|---|---|
| [ADR-013](./architecture-decision-records/ADR-013.md) | 产品定位与生存性测试 |
| [ADR-016](./architecture-decision-records/ADR-016.md) | Protocol-first 战略 |
| [ADR-017](./architecture-decision-records/ADR-017.md) | Action / Effect 与准入边界 |

完整编号注册表保留在 [ADR 索引](./architecture-decision-records/README.md)。
