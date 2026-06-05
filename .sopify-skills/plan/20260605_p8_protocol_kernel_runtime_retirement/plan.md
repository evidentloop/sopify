---
title: P8 Protocol Kernel & Runtime Retirement
plan_id: 20260605_p8_protocol_kernel_runtime_retirement
status: pending
level: architecture
created: 2026-06-05
owner: sanze.li
depends_on: [P7 (payload_only_onboarding_mainline), P6 (canonical_writer_cutover), P5 (contract_surface_shrinkage)]
---

# P8 Protocol Kernel & Runtime Retirement

## Context / Why

**触发条件**（三条输入同时成立，使 P8 窗口打开）：

1. **runtime 仍是最大真相源**：~16K LOC / 37 模块。P6 已切出 canonical_writer（605 LOC）+ sopify_contracts（1,160 LOC），但 runtime/ 仍在产出 state/ 文件，installer/sopify_bundle.py 仍在打包完整 runtime。
2. **协议不是真相源**：protocol.md 仍是"阅读材料"。§6 Integration Contract 整体 informative（仅 Verifier + EAR 升格 normative）。外部宿主接入时实际消费的 contract 散落在 design.md / ADR / protocol.md 之间。
3. **新宿主接入没有"轻量可插拔"的硬证据**：Copilot P7 走的是 installer 路径而非纯协议路径。缺少"宿主不装 runtime、只消费 protocol + canonical_writer 就能接续"的公开证据。

**输入来源**：

- 蓝图主航道 P5/P6/P7 收口结论
- 蓝图 design.md §Runtime 退场路线（已拍板 target-state-first，零用户无迁移负担）
- 外部治理协议对比：wow-harness v3 / Superpowers / OpenSpec / ESAA
- 蓝图 open backlog：Runtime retirement Phase 2 / Protocol Compliance Phase 2 / 第三方宿主自助接入证明

**为什么不在现有 plan 做**：

- `20260522_runtime_slimming_kernel_extraction` 已归档，仅覆盖 Phase 1
- 当前 plan 需要覆盖 **状态模型重构 + 协议内核 freeze + runtime 全删 + 文档叙事切换 + 新宿主验收** 五件事，是架构级 cutover，不是 Phase 1 的延续

**为什么不做**：

- 不可变事件时间线（v3 P1）——与 blueprint/history 可改语义冲突
- 概念节点状态机（v3 P2）——与 hard max §1 能删则删冲突
- 多 agent 自组织图（v3 P4）——与 design.md 竞品边界冲突（Sopify 不做 orchestration）
- Protocol v1 全面 normative 升格——过度设计
- Concept Evolution Gate——不需要独立 gate
- Multi-host review contract 升格——等 P8 收口后评估
- Plugin admission + Verifier evidence 标准化——设计阶段
- 多宿主扩展（P9）——协议未 freeze 前铺宿主是生态债务
- 完整 checkpoint / shadow writer / pre-commit 接入——过度验证

## Scope

把 Sopify 的真相源从 runtime 切换到 protocol.md + canonical_writer，用一个 architecture 级方案包闭合三件事：

1. **协议内核 freeze + State 极简 cutover**：5 件 must-freeze schema 化 + state/ 从 5 文件压到 2 文件
2. **Runtime Phase 2 物理删除**：runtime/ 全删 + installer bundle 清理 + state/ 物理重构
3. **新宿主试点验收**：Cursor payload_capable + 接续增强，证明轻量可插拔 + 文档叙事切换

## Approach

- **协议内核，不是协议 v1**：只 freeze 5 件 must-freeze，draft 面保留为 draft
- **激进删除，零用户红利**：线上无用户，不需要渐进迁移、不需要 shadow writer、不需要 pre-commit 锁死
- **状态模型极简**：state/ 只留 2 文件（active_plan + current_handoff），"AI 等人"折叠进 current_handoff.required_host_action
- **产品叙事切换**：docs/how-sopify-works 从 "runtime gate first" 重写为 "host is executor, Sopify is protocol kernel"
- **新宿主试点是硬验收**：不是 installer smoke，而是"新宿主消费 protocol 文件完成跨 session 接续"

## 三波次（串行）

### Wave 1 — Protocol + State Contract Cutover

**目标**：把协议和状态模型说清楚，给出可机器校验的最小基线

- S1.1 protocol.md 升级：5 件 must-freeze 字段 + schema（JSON Schema 或 CDDL）
- S1.2 protocol.md §2 升级：plan 包结构（plan.md 唯一入口 + 可选 tasks/design/assets + receipts 条件必备）+ plan.md 8 必备章节
- S1.3 protocol.md §6 升级：Verifier read-only contract（MUST_NOT 写 state/plan/blueprint）
- S1.4 protocol.md §8 升级：host 入口读顺序（4 步：active_plan → plan.md → current_handoff → receipts/）
- S1.5 `scripts/sopify_compliance.py`：主链 smoke（new-plan / continuation / finalize 三场景）
- S1.6 最小 fixture：当前 repo + 1 个最小 external repo

**验收**：

- 文档自洽（protocol.md 各章节字段对得上）
- sopify_compliance.py 当前 repo 跑通 3 场景

### Wave 2 — Runtime Physical Retirement + State 物理重构

**目标**：runtime 不再是路由器；state/ 物理瘦身

- S2.1 Installer 5 文件解耦（validate / bootstrap_workspace / inspection / install_sopify / sopify_init 移除 runtime import）
- S2.2 CLI Helper 迁移（sopify_status / sopify_doctor 改消费 installer/inspection.py contract）
- S2.3 State 物理重构：
  - 删 `state/current_run.json`（语义下沉到 plan.md status）
  - 删 `state/current_plan.json`（被 active_plan 替代）
  - 删 `state/current_clarification.json` / `current_decision.json`（折叠到 current_handoff.required_host_action）
  - 删 `state/current_archive_receipt.json`（真相进 history/receipt.md）
  - canonical_writer / sopify_contracts 适配新结构
- S2.4 Tests 分类（保留 contract / 删除 runtime-coupled / 迁移到 canonical_writer）
- S2.5 删除 `runtime/` 全目录（~16K LOC / 37 文件）
- S2.6 删除 `installer/sopify_bundle.py`
- S2.7 删除 `installer/hosts/{codex,claude}/` deep adapter（保留 copilot/）
- S2.8 Dogfood smoke：当前 repo 跑 new-plan / continuation / finalize 三场景各 1 次

**验收**：

- W1 compliance smoke 仍绿
- runtime/ 不存在
- canonical_writer 是唯一写路径（grep 确认无 runtime 调用）
- state/ 只剩 active_plan + current_handoff 两个文件

### Wave 3 — Host Proof + Docs Cutover

**目标**：用真实宿主证明"只消费 protocol 文件即可接续"；文档叙事切换

- S3.1 选定 Cursor 作为试点宿主（Windsurf 放 P9）
- S3.2 Payload-capable adapter（不写 deep glue；只调 canonical_writer）
- S3.3 接续增强接入：消费 active_plan / plan.md / current_handoff / receipts
- S3.4 端到端验收：Cursor 写 handoff → Cursor 新 session 消费 handoff 继续
- S3.5 文档叙事切换：
  - 重写 README / README.zh-CN 主流程图
  - 重写 docs/how-sopify-works(.en).md 主流程图 + 状态模型
  - 更新 docs/getting-started.md
  - 画架构图（state 2 文件 + host 4 步入口 + 跨宿主接续）
- S3.6 Blueprint design.md 回写：runtime 退场完成 + 状态模型极简 + plan 包结构

**验收（4 条硬指标）**：

1. Cursor 消费 `state/active_plan.json` 定位 plan ✓
2. Cursor 读 `plan/<id>/plan.md` 理解进度 ✓
3. Cursor 写 `state/current_handoff.json` + `plan/<id>/receipts/*.json` 后可被另一 session 接续 ✓
4. **整条链路不依赖 runtime 进程** ✓

## 关键设计决策（详细论证见 design.md）

1. **plan_id 是跨宿主接续主键**；session_id 仅 provenance 审计字段
2. **state/ 极简到 2 文件**：active_plan（bootstrapping 锚）+ current_handoff（live continuation state + "AI 等人"信号）
3. **handoff 单态**：只在 state/current_handoff.json；finalize 时最后交接事实体现在 `receipts/final.json` + `history/receipt.md`，**不新造 plan/<id>/handoff.json**
4. **receipts/ 保留在 plan scope（条件必备）**：managed plan 产生执行/验证事件时必须写到 receipts/；finalize 时必须生成 receipts/final.json；light plan 如无 managed execution 可无 receipts/。作为过程审计资产，是跨宿主判断"是否验证过"的依据
5. **plan.md 是语义入口**：承担原 background.md 职责（Context/Why / Scope / Approach / Waves / Key Decisions / Constraints / Status / Next）
6. **"AI 等人"折叠到 current_handoff.required_host_action**：复用蓝图已定义的 canonical 语义（answer_questions / confirm_decision 等），不新增字段
7. **不加 status.json / 不加 plan-level README.md / 不加 pending_* / 不加 last_archive_receipt**
8. **plan 包分级 light / standard / architecture**：渐进披露
9. **assets/ 替代 references/**：统一放架构图、截图、长参考材料
10. **Verifier read-only contract**：verifier MUST_NOT 写 state/plan/blueprint，违反则 verdict 降级为 advisory

## 目标项目结构（详细字段定义见 design.md）

```
.sopify-skills/
├── project.md                        # git-tracked | 项目约定
├── blueprint/                        # git-tracked | 长期知识
│   ├── README.md / background.md / design.md / tasks.md / protocol.md
├── plan/<plan_id>/                   # git-tracked | 活动工作 + 过程审计
│   ├── plan.md                       # 唯一语义入口（含 Context/Why）
│   ├── tasks.md                      # 可选（standard+）
│   ├── design.md                     # 可选（architecture 级）
│   ├── receipts/                     # 过程审计资产（条件必备）
│   │   ├── exec_NNN.json             # 执行凭证
│   │   ├── verify_NNN.json           # 验证凭证
│   │   └── final.json                # finalize 时生成
│   └── assets/                       # 可选（图、截图、长参考）
├── history/YYYY-MM/<plan_id>/        # git-tracked | 归档档案（整包搬入）
│   ├── plan.md / tasks.md / design.md / receipts/ / assets/
│   └── receipt.md                    # 最终可审计收据（归档时生成）
├── state/                            # gitignored | 仅 2 文件
│   ├── active_plan.json              # 定位：{ "plan_id": "..." }
│   └── current_handoff.json          # 恢复：复用蓝图 handoff schema + required_host_action
└── user/                             # git-tracked
    ├── preferences.md
    └── feedback.jsonl
```

## Host 入口读顺序（4 步）

```
1. state/active_plan.json         → 定位 plan_id（如无 → consult / new-plan）
2. plan/<id>/plan.md              → 语义入口：做什么 + 进度（真相源）
3. state/current_handoff.json     → 恢复提示 + 是否等用户（required_host_action）
4. plan/<id>/receipts/            → 按 ID 字典序取最新，知道"哪些被验证过"
```

**顺序设计原则**：active_plan 定位后先读 plan.md 建立语义真相，再读 current_handoff 作为恢复提示——**避免 handoff 反过来变成第二真相源**。current_handoff.required_host_action 复用蓝图 canonical 值（continue_host_develop / answer_questions / confirm_decision / continue_host_consult / resolve_state_conflict）。

## Plan 包分级（Progressive Disclosure）

| 级 | 文件 | 适用场景 |
|---|---|---|
| **light** | plan.md | 小任务、单步修复、探索性提案 |
| **standard** | plan.md + tasks.md | 多任务、需逐项验收 |
| **architecture** | plan.md + design.md + tasks.md + receipts/ + assets/ | 架构级、协议级、状态模型变更 |

**规则**：

- plan.md 是**唯一语义入口**，承担 Context/Why 职责（8 必备章节）
- tasks.md 可选；任务多、依赖复杂、需逐项验收时拆出
- design.md 可选；仅架构级、协议级、跨模块、状态模型、重大取舍时才有
- receipts/ **条件必备**（过程审计资产）：managed plan 产生执行/验证事件时必须写到 receipts/；finalize 时必须生成 receipts/final.json；light plan 如无 managed execution 可无 receipts/。命名规范 `exec_NNN / verify_NNN / final`
- assets/ 可选；放架构图、PNG/SVG、长参考材料（不拆 references/）
- **不加** status.json / plan-level README.md / plan/<id>/handoff.json（避免 over-design）

## 5 件 Must-Freeze（协议内核最小集）

| # | Contract | 文件 | 职责 |
|---|---|---|---|
| 1 | Active Plan Pointer | `state/active_plan.json` | 定位：当前 plan_id |
| 2 | Current Handoff | `state/current_handoff.json` | 恢复：上次停哪 + 是否等用户（required_host_action） |
| 3 | Plan.md Required Sections | `plan/<id>/plan.md` | 语义真相：8 必备章节 |
| 4 | Plan Receipts | `plan/<id>/receipts/*.json` | 过程审计：exec/verify/final 命名规范 |
| 5 | History Receipt | `history/<id>/receipt.md` | 最终审计：outcome / summary / key_decisions |

**明确不冻结**：

- pending_* 文件（已删除；折叠到 current_handoff.required_host_action）
- last_archive_receipt（已删除；归档事实进 history/receipt.md）
- plan/<id>/handoff.json（不新造；最后交接事实体现在 receipts/final.json + history/receipt.md）
- Integration Contract 中的 Producer / Knowledge Provider（仅 Verifier 升格）
- Multi-host review contract / Plugin admission（延后）

## 硬约束（P8 内部红线）

1. Wave 1 未收口前不动 Wave 2（文档自洽先于物理删除）
2. Wave 2 未收口前不动 Wave 3（runtime 删除前，新宿主不能依赖 runtime）
3. 不引入、不删除、不修改蓝图 design.md 已定义的 canonical machine truth 语义
4. 新宿主试点必须证明"不依赖 runtime 进程即可接续"，否则 P8 不算收口
5. Verifier read-only 约束是 MUST，违反则 verdict 降级为 advisory（不自授权）
6. state/ 只能有 2 文件；新增任何 state 文件必须 ADR
7. 所有 plan 包必须遵守 light / standard / architecture 三档分级

## 削减预算对齐（对照蓝图 design.md 削减预算表）

| 维度 | P8 前 | P8 后 | 红线 |
|---|---|---|---|
| Checkpoint types | 2 (canonical) | 2 | 不变 |
| required_host_action | 5 (canonical) | 5 | 不变（复用） |
| Route families | 6 (canonical) | **不承诺** | deep runtime 删除后 route 语义下沉到 handoff contract |
| Core state files | 6 (authoritative) | **2** | active_plan + current_handoff；其他全部删除或折叠 |

**重大更新**：Core state files 6 → 2。这是蓝图 design.md §Core State Files 段落的显式调整，P8 收口后需回写蓝图。

## 与蓝图对齐

- 挂在蓝图主航道 P5/P6/P7 延长线上（符合 hard max §8）
- 吸收蓝图 open backlog：Runtime retirement Phase 2 / 第三方宿主自助接入证明 / Protocol Compliance Phase 2
- **显式调整蓝图**：Core state files 6 → 2；§State Model 重写；§Plan Package Structure 新增
- 收口后回写蓝图 design.md：§Runtime 退场路线 + §State Model + §Plan Package Structure + tasks.md

## 不在 P8（明确延后）

- Knowledge_sync novelty_rationale 字段（吸收 v3 新颖性检查；独立 slice）
- Multi-host review contract 升格（等 P8 协议内核 freeze 后评估）
- Plugin admission + Verifier evidence 标准化（设计阶段）
- Skill packaging / localization governance（独立延后）
- 多宿主扩展（P9 延后；Windsurf 放 P9）

## 风险与缓解

| 风险 | 严重度 | 缓解 |
|---|---|---|
| runtime 16K LOC 删除后暴露未知依赖 | 高 | W1 compliance smoke 先行建立契约基线；W2 dogfood smoke 验证主链 |
| State 重构破坏现有 host 接续 | 中 | W2 S2.3 物理重构后立刻跑 dogfood smoke 验证 |
| installer 5 文件解耦时发现隐式 import | 中 | 逐个文件做 import graph 审计（Phase 1 经验） |
| canonical_writer 未经历真实场景考验 | 中 | W3 Cursor proof 强制走 canonical_writer 写路径，作为硬验收 |
| Cursor 试点卡在宿主 API 限制 | 低 | 试点档位是 payload_capable 非 deep；不强求宿主实现所有能力 |
| Verifier read-only 约束被绕过 | 中 | schema 级声明 + Validator 消费时校验；不做 runtime enforcement |
