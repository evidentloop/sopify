---
title: P8 Protocol Kernel & Runtime Retirement — Design
plan_id: 20260605_p8_protocol_kernel_runtime_retirement
status: pending
created: 2026-06-05
---

# Design

## 1. 产品定位

**P8 目标态**：Sopify 从"有 runtime 的工作流系统"变成"AI coding 工具可消费的协议内核"。

- **runtime/ 物理删除**：不再有 runtime router / engine / session state machine / 每轮必跑 gate
- **protocol kernel 留下**：init/bootstrap、validate/compliance、receipt/finalize、doctor/smoke，体量 ≤1K LOC
- **真相源切换**：从 runtime 切换到 protocol.md + canonical_writer + sopify_contracts

**Protocol kernel 不是 runtime 复活**：只允许 init/bootstrap、validate/compliance、receipt/finalize、doctor。不允许 router/engine/session state machine 回流。

**P8 不是**：

- 不是 protocol.md v1 全面发布（只 freeze 5 件 must-freeze，draft 保留为 draft）
- 不是新主轴（挂在 P5/P6/P7 收口主线上）
- 不是多宿主扩展（只做 1 个试点作为验收；Windsurf 放 P9）

## 2. 协议内核（Kernel）— 5 件 Must-Freeze

| # | Contract | 文件 | Schema 要点 |
|---|---|---|---|
| 1 | Active Plan Pointer | `state/active_plan.json` | `{ "plan_id": "<id>" }`；极简 |
| 2 | Current Handoff | `state/current_handoff.json` | 复用蓝图已定义 handoff schema + `required_host_action` 字段（复用蓝图 canonical 值：`continue_host_develop` / `answer_questions` / `confirm_decision` / `continue_host_consult` / `resolve_state_conflict`） |
| 3 | Plan.md Required Sections | `plan/<id>/plan.md` | 8 必备章节：Context/Why / Scope / Approach / Waves / Key Decisions / Constraints / Status / Next |
| 4 | Plan Receipts | `plan/<id>/receipts/*.json` | 命名规范 `exec_NNN / verify_NNN / final`；字段：verdict / evidence / provenance / timestamp |
| 5 | History Receipt | `history/<id>/receipt.md` | 必备章节：outcome / summary / key_decisions |

**明确不冻结**：

- pending_* 文件（已删除；折叠到 current_handoff.required_host_action）
- last_archive_receipt（已删除；归档事实进 history/receipt.md）
- plan/<id>/handoff.json（不新造；最后交接事实体现在 receipts/final.json + history/receipt.md）
- Integration Contract 中的 Producer / Knowledge Provider（仅 Verifier 升格）
- Multi-host review contract / Plugin admission（延后）
- GateReceipt / deep runtime gate（legacy/deep 迁移对象，不进 P8 新核心）

## 3. Plan Package Structure（方案包结构）

### 3.1 文件清单

```
plan/<plan_id>/
├── plan.md              # 必备，唯一语义入口（含 Context/Why）
├── tasks.md             # 可选（standard+ 级）
├── design.md            # 可选（architecture 级）
├── receipts/            # 必备，过程审计资产
│   ├── exec_NNN.json    # 执行凭证
│   ├── verify_NNN.json  # 验证凭证
│   └── final.json       # finalize 凭证
└── assets/              # 可选，图、截图、长参考材料
```

### 3.2 分级（Progressive Disclosure）

| 级 | 必备文件 | 适用场景 |
|---|---|---|
| **light** | plan.md | 小任务、单步修复、探索性提案 |
| **standard** | plan.md + tasks.md | 多任务、需逐项验收 |
| **architecture** | plan.md + design.md + tasks.md + receipts/ + assets/ | 架构级、协议级、状态模型变更 |

### 3.3 plan.md 8 必备章节

每个 plan.md 必须包含（顺序固定）：

1. **Context / Why**：触发条件、输入来源、为什么新包、为什么不做 X
2. **Scope**：做什么
3. **Approach**：怎么做
4. **Waves / Steps**：分几步
5. **Key Decisions**：关键决策（引用 design.md 章节）
6. **Constraints / Not-in-scope**：硬约束 + 延后项
7. **Status / Progress**：当前进度（任务多时拆到 tasks.md）
8. **Next**：下一步动作

plan.md 承担原 background.md 职责（Context/Why），不单独拆 background.md。

### 3.4 规则

- plan.md 是**唯一语义入口**
- tasks.md 可选；任务多、依赖复杂、需逐项验收时拆出
- design.md 可选；仅架构级、协议级、跨模块、状态模型、重大取舍时才有
- receipts/ **条件必备**（过程审计资产）：managed plan 产生执行/验证事件时必须写到 `receipts/*.json`；finalize 时必须生成 `receipts/final.json`；light plan 如无 managed execution 可无 receipts/。命名规范 `exec_NNN / verify_NNN / final`
- assets/ 可选；放架构图、PNG/SVG、长参考材料（**不拆 references/**）
- **不加** status.json（与 plan.md 重复，over-design）
- **不加** plan-level README.md（与 plan.md 职责冲突）
- **不加** plan/<id>/handoff.json（handoff 单态，只在 state/；最后交接事实体现在 receipts/final.json + history/receipt.md）

## 4. State Model（状态模型）— 极简 2 文件

### 4.1 三层硬区分

| 层 | 用户心智 | Git | 职责 |
|---|---|---|---|
| **state/** | 定位针 + 恢复提示 | ignored | 帮新宿主定位 plan、知道上次停哪、知道是否等用户 |
| **plan/<id>/** | 这件事本身 + 过程审计 | tracked | 方案、任务、凭证、可选设计 |
| **history/<id>/** | 最终档案 | tracked | finalize 后的完整可审计记录 |

### 4.2 state/ 最小集合（2 文件）

```
state/
├── active_plan.json        # 定位：{ "plan_id": "<id>" }
└── current_handoff.json    # 恢复：复用蓝图 handoff schema + required_host_action
```

**全部 gitignored，可重建**。state/ 不能成为长期事实源。

### 4.3 删除的 state 文件（P8 显式删除）

| 旧文件 | 处置 |
|---|---|
| `state/current_plan.json` | **删除** → 被 `active_plan.json` 替代 |
| `state/current_run.json` | **删除** → 语义下沉到 `plan/<id>/plan.md` 的 Status 章节 |
| `state/current_clarification.json` | **删除** → 折叠到 `current_handoff.required_host_action = answer_questions` |
| `state/current_decision.json` | **删除** → 折叠到 `current_handoff.required_host_action = confirm_decision` |
| `state/current_archive_receipt.json` | **删除** → 真相进 `history/<id>/receipt.md` |
| `state/last_route.json` | **删除** → 可从 current_handoff 派生 |

### 4.4 "AI 等人"信号折叠到 current_handoff

**复用蓝图已定义的 canonical required_host_action**，不新增字段：

| 场景 | current_handoff.required_host_action | 备注 |
|---|---|---|
| AI 继续工作 | `continue_host_develop` | 默认 |
| AI 等用户补事实 | `answer_questions` | 替代原 pending_clarification |
| AI 等用户拍板 | `confirm_decision` | 替代原 pending_decision |
| AI 等用户继续对话 | `continue_host_consult` | |
| AI 完成可 finalize | finalize hint 体现在 handoff.notes | |
| AI 空闲 | idle 体现在 handoff.notes | |

问题列表 / 选项内容放在 `current_handoff.artifacts` 或 `current_handoff.notes` 字段，复用蓝图已定义 schema。

## 5. Handoff 单态

**之前讨论的 handoff 双态（live in state/ + settled in plan/ + archived in history/）是过度设计**。

**最终设计：handoff 单态**：

- `state/current_handoff.json` 是**唯一 handoff 文件**，gitignored，每次 turn 重写
- finalize 时**不 promote 到 plan/<id>/handoff.json**
- 最后交接事实体现在：
  - `plan/<id>/receipts/final.json`（finalize 凭证）
  - `history/<id>/receipt.md`（最终审计收据）

**理由**：

- plan/<id>/ 已经有 receipts/ 作为过程审计资产，handoff 是"live 状态"不是"审计事实"，不应进 plan scope
- 跨宿主接续只需要 state/current_handoff.json（live cache）+ plan/<id>/plan.md（语义真相）
- 审计追溯靠 history/<id>/receipt.md + receipts/，不需要 handoff.json

## 6. 接续逻辑（Continuation Logic）

**架构图（手绘风格）**：

- ![State 极简 + Host 入口](./assets/state-and-host-flow.svg) — state/ 2 文件 + plan/<id>/ 方案本体 + history/<id>/ 归档档案 + host 4 步入口读顺序
- ![跨宿主接续](./assets/cross-host-continuation.svg) — host 4 步入口读顺序详解 + handoff 单态 + 跨宿主接续场景

> 浏览器直接打开 SVG 可看完整标注；GitHub / IDE markdown preview 通常也能渲染。

### 6.1 Host 入口读顺序（4 步）

```
1. state/active_plan.json         → 定位 plan_id（如无 → consult / new-plan）
2. plan/<id>/plan.md              → 语义入口：做什么 + 进度（真相源）
3. state/current_handoff.json     → 恢复提示 + 是否等用户（required_host_action）
4. plan/<id>/receipts/            → 按 ID 字典序取最新，知道"哪些被验证过"
```

**顺序设计原则**：active_plan 定位后**先读 plan.md 建立语义真相**，再读 current_handoff 作为恢复提示——**避免 handoff 反过来变成第二真相源**。

### 6.2 链路设计原则

1. **bootstrapping 优先**（step 1）：host 必须先知道 plan_id，否则无法定位其他资产
2. **语义优先于缓存**（step 2 在 3 前）：plan.md 是真相源，current_handoff 是恢复提示
3. **证据收尾**（step 4）：receipts 是补充信息，host 可在前几步已能开始工作

### 6.3 链路失败模式与 fail-open 规则

| 步 | 文件缺失时 host 行为 |
|---|---|
| 1 active_plan 缺失 | 进入 consult 模式或提示用户 new-plan；不阻断 |
| 2 plan.md 缺失 | 异常（active_plan 指向的 plan 目录应该有 plan.md）→ 提示用户 state 不一致 |
| 3 current_handoff 缺失 | 正常（plan.md 已能表达进度）→ host 仅按 plan.md 进度接续，无精细恢复 |
| 4 receipts/ 缺失或空 | 正常（无历史验证）→ host 不假设任何动作已被验证 |

### 6.4 三种典型场景

**场景 A：同一宿主连续 session**

- session N 写 `state/current_handoff.json` + `plan/<id>/receipts/exec_NNN.json`
- session N+1 按 4 步读顺序接续

**场景 B：跨宿主接续（核心差异化）**

- Codex session 写 current_handoff + receipts
- 用户切到 Cursor，Cursor 按 4 步读顺序接续
- **plan_id 是身份；session_id 只出现在 handoff/receipt 的 provenance 字段**

**场景 C：Finalize + 归档**

- 宿主生成 `plan/<id>/receipts/final.json`（finalize 凭证）
- 移动整包 → `history/YYYY-MM/<plan_id>/`
- 生成 `history/<plan_id>/receipt.md`（最终可审计收据）
- 更新 blueprint + 清空 `state/active_plan.json` + `state/current_handoff.json`

### 6.5 完整用户旅程

```
用户进入任意 AI 宿主（Claude / Codex / Copilot / Cursor / Windsurf）
  → 宿主加载 Sopify instruction / prompt asset
  → 宿主自动：
      1. 读 state/active_plan.json           （当前在做哪件事）
      2. 读 plan/<id>/plan.md                （目标、方案、进度）
      3. 读 state/current_handoff.json       （上次停在哪、是否等用户）
      4. 读 plan/<id>/receipts/              （哪些动作已被验证）
  → 宿主形成 ActionProposal → 走 Validator / compliance check
  → 宿主用原生工具执行
  → 写回 plan/<id>/plan.md + receipts/ + state/current_handoff.json
  → 如有 clarify/decide 分叉：写 current_handoff.required_host_action = answer_questions/confirm_decision
  → 全部完成后：
      生成 plan/<id>/receipts/final.json
      移动整包 → history/YYYY-MM/<plan_id>/
      生成 history/<plan_id>/receipt.md
      更新 blueprint + 清空 state/
```

**用户心智**：

- 不需要记住 session_id / 上次用的宿主 / 上次做到哪
- 换宿主 = 换工具，**plan 身份不变**
- 打开任何宿主都能"接着做"，因为接续锚点都在 .sopify-skills/ 里

### 6.6 接续链路与状态写入的对称性

**读顺序（session 启动）** ↔ **写顺序（turn 结束 / session 关闭）**：

| 读的步 | 对应写 | 何时写 |
|---|---|---|
| 1 active_plan | 写 active_plan | new-plan 时；finalize 时清空 |
| 2 plan.md | 写 plan.md + tasks.md | 每次 turn 可能更新进度 |
| 3 current_handoff | 写 current_handoff | 每次 turn 结束重写 |
| 4 receipts/ | 写 receipts/exec_NNN.json 等 | 每次有可验证动作产生新凭证 |

**关键不对称**：plan.md 是 "semantic entry"，**写频率低（进度变化时）但读是必需**。current_handoff 是 "live cache"，**写频率高（每次 turn）但读是补充**。

## 7. Verifier Read-Only Contract

**吸收 v3 双层验证思想，落点在 schema 而非 prompt**：

```yaml
# protocol.md §6 Verifier 新增 MUST
verifier_contract:
  MUST:
    - emit_verdict: { verdict, evidence, source }
    - read_only: true   # 不得写 state/, plan/, blueprint/
    - no_self_authorize: true  # 只产出 evidence，不得自授权
  MUST_NOT:
    - write: ["state/**", "plan/**", "blueprint/**"]
    - invoke: ["execute_command", "modify_files"]
```

**消费路径**：

- Validator 消费 verdict 时校验 verifier_contract 声明
- 违反 read-only → verdict 降级为 advisory（不是 REJECT，保持 advisory 语义）
- 具体 enforcement 在 cross-review Phase 4b bridge 落地

**为什么这一刀值钱**：

- 是 v3 "验证者工具列表无写权限" 在 Sopify 的最小实现
- 与 Validator-centered 哲学一致——验证者不授权，只出证据
- 为后续外部 verifier 接入（lint/test/CI gate adapter）提供硬契约

## 8. Compliance Smoke（最小可校验）

**不做完整测试平台，不做三档 fixture 矩阵**。只做一个可独立运行的 compliance smoke 脚本（Python，挂在 `scripts/sopify_compliance.py`），验证主链 3 场景：

| 场景 | 检查项 |
|---|---|
| **new-plan** | 创建新 plan → 写 active_plan → 写 plan.md（8 必备章节齐全） |
| **continuation** | 中断后新 session 按 4 步读顺序接续，能定位 plan + 理解进度 |
| **finalize** | promote 到 history + 生成 receipt.md + 清空 state/ |

**fixture 策略**：

- 当前 repo 作为主 fixture（dogfood）
- 1 个最小 external repo 作为辅助 fixture
- **不做 convention/payload/deep 三档全矩阵**——过度验证

## 9. Runtime Phase 2 物理删除

**Keep-list（保留）**：

| 模块 | 理由 |
|---|---|
| `installer/bootstrap_workspace.py` | 新宿主 payload 安装必备 |
| `installer/inspection.py` | sopify_status / sopify_doctor 依赖 |
| `installer/payload.py` | payload 分发核心 |
| `installer/validate.py` | 安装前校验 |
| `installer/models.py` / `distribution.py` / `outcome_contract.py` | installer 基础设施 |
| `installer/hosts/copilot/`（如仍在） | payload_capable 试点已验证 |
| `canonical_writer/`（P6 已切出） | 新真相源，新宿主唯一写路径 |
| `sopify_contracts/`（P6 已切出） | contract schema 定义 |
| `scripts/install_sopify.py` / `sopify_init.py`（解耦后） | 用户入口 |

**Delete-list（激进删除）**：

| 模块 | 理由 |
|---|---|
| `runtime/` 全目录（~16K LOC / 37 文件） | runtime 退场主线目标 |
| `installer/sopify_bundle.py` | 完整 runtime 打包器，runtime 删除后无意义 |
| `installer/hosts/{codex,claude}/`（deep adapter） | deep host legacy glue，蓝图 design.md 已拍板 2026-05-22 停止维护 |
| 所有 `*_bridge.py` / `*_renderer.py` / `*_bundle.py` legacy deep script | 同上 |
| `state/current_run.json` / `current_plan.json` / `current_clarification.json` / `current_decision.json` / `current_archive_receipt.json` / `last_route.json` | State 极简 cutover（§4.3） |

**迁移-list（先解耦后删）**：

- `scripts/sopify_status.py` / `sopify_doctor.py` → 改为消费 `installer/inspection.py` 暴露的 contract，不调 runtime API
- `tests/` 中 runtime-coupled 测试 → 按 Phase 1 经验分类：保留 contract / 删除 runtime-coupled / 迁移到 canonical_writer 测试
- canonical_writer / sopify_contracts → 适配 state/ 新结构（2 文件）

**目标 LOC**：

- 起点：runtime ~16K LOC
- 终点：runtime 0 + canonical_writer ~605 + sopify_contracts ~1,160 + installer（保留部分 ~2K）
- 净效果：Sopify 真相源从 ~16K runtime 切换到 ~4K protocol+writer+installer

## 10. 新宿主试点（P8 验收项）

**宿主候选**：**Cursor**（Windsurf 放 P9）。

**选择 Cursor 理由**：

- 更贴近 prompt/payload 适配心智（与 P8 协议内核方向一致）
- 社区活跃度高；用户偏好
- 已有 Copilot P7 payload_capable 经验可复用

**接入档位**：payload_capable + 接续增强（消费 active_plan / plan.md / current_handoff / receipts）。**不做 deep_verified**。

**验收口径（不是"跑通安装"）**：

1. Cursor 在 fixture repo 上完成 `~go` 风格的启动
2. Cursor 按 4 步读顺序接续：active_plan → plan.md → current_handoff → receipts/
3. Cursor 写 `state/current_handoff.json` + `plan/<id>/receipts/*.json` 后退出，再由 Cursor 新 session 接续
4. 整条链路**不依赖 runtime 进程**——只消费 protocol 文件 + canonical_writer

**产出物**：

- `installer/hosts/cursor/` adapter（payload 级，非 deep）
- `docs/hosts/cursor-onboarding.md` 接入文档
- 一个端到端验收 transcript 作为 P8 收口证据

**Checkpoint 不作为硬验收**：Cursor 只要能完成 mainline 接续即可；checkpoint（clarify/decide 分叉）最多作为 bonus evidence。

## 11. Document Narrative Cutover（文档叙事切换）

**切换前**：

- "Sopify 通过 runtime gate 分发任务"
- "runtime 是真相源"
- "host 调 runtime API"

**切换后**：

- "AI coding 工具执行任务，Sopify 提供协议、任务资产、校验器和收据"
- "protocol.md + canonical_writer 是真相源"
- "host 读写 protocol 文件，可选调 protocol kernel CLI"

**必须重写的文档**：

- `README.md` / `README.zh-CN.md`：主流程图
- `docs/how-sopify-works.md` / `docs/how-sopify-works.en.md`：主流程图 + 状态模型
- `docs/getting-started.md`：新用户引导

## 12. ID 语义表

| ID | 作用 | 主键性 | 出现位置 |
|---|---|---|---|
| **plan_id** | 工作单元身份；跨宿主接续主键 | **是** | 目录名、active_plan、handoff.provenance、receipt.provenance |
| **receipt_id** | plan 内凭证编号（exec_NNN / verify_NNN） | 否 | receipts/*.json |
| **session_id** | 来源审计字段 | **否** | handoff.provenance / receipt.provenance |

**核心原则**：plan_id 是接续主键；session_id 仅作 provenance 审计，不参与接续定位。

## 13. 风险与缓解

| 风险 | 严重度 | 缓解 |
|---|---|---|
| runtime 16K LOC 删除后暴露未知依赖 | 高 | W1 compliance smoke 先行建立契约基线；W2 dogfood smoke 验证主链 |
| State 重构破坏现有 host 接续 | 中 | W2 S2.3 物理重构后立刻跑 dogfood smoke 验证 |
| installer 5 文件解耦时发现隐式 import | 中 | 逐个文件做 import graph 审计（Phase 1 经验） |
| canonical_writer 未经历真实场景考验 | 中 | W3 Cursor proof 强制走 canonical_writer 写路径，作为硬验收 |
| Cursor 试点卡在宿主 API 限制 | 低 | 试点档位是 payload_capable 非 deep；不强求宿主实现所有能力 |
| Verifier read-only 约束被绕过 | 中 | schema 级声明 + Validator 消费时校验；不做 runtime enforcement |

## 14. 不在 P8 的延后项（明确登记）

- Knowledge_sync novelty_rationale 字段：吸收 v3 新颖性检查思想，但落点是 knowledge_sync 增量字段，不属于 P8 协议内核。P9 或独立 slice。
- Multi-host review contract normative 升格：等 P8 协议内核 freeze 后再评估。
- Plugin admission + Verifier evidence 标准化：设计阶段，不进 P8。
- Skill packaging / localization：独立延后。
- Windsurf 试点：放 P9。
