---
title: P8 Protocol Kernel & Runtime Retirement
plan_id: 20260605_p8_protocol_kernel_runtime_retirement
status: in_progress (W1 ✅ / W2 ✅ / Phase 0 ✅ / W3.1 ✅ / W3.2 next)
level: architecture
created: 2026-06-05
owner: sanze.li
depends_on: [P7 (payload_only_onboarding_mainline), P6 (writer_cutover), P5 (contract_surface_shrinkage)]
---

# P8 Protocol Kernel & Runtime Retirement

## Plan Snapshot

- **Goal**: 把 AI 开发过程中的方案、决策、交接、执行/验证证据收敛为可追溯审计资产；真相源从 runtime 切到 protocol.md + sopify_writer，并用 Qoder 证明这些资产可跨宿主接续
- **Status**: W1 完成 / W2 完成 / Phase 0 完成 / W3.1 完成 — W3.2 待执行
- **Next**: W3.2 Qoder Continuation Writer Path（Installed Payload Proof）
- **Task**: W3.2 → W3.3 → W3.5 → W3.6 → Finalize

## Context / Why

**触发条件**（三条输入同时成立，使 P8 窗口打开）：

1. **runtime 仍是最大真相源**：~16K LOC / 37 模块。P6 已切出 writer 基础（当前名 `canonical_writer`，P8 收敛为 `sopify_writer`）+ sopify_contracts（1,160 LOC），但 runtime/ 仍在产出 state/ 文件，installer/sopify_bundle.py 仍在打包完整 runtime。
2. **协议不是真相源**：protocol.md 仍是"阅读材料"。§6 Integration Contract 整体 informative（仅 Verifier + EAR 升格 normative）。外部宿主接入时实际消费的 contract 散落在 design.md / ADR / protocol.md 之间。
3. **审计资产协议缺少"轻量可插拔"的硬证据**：蓝图已经把 Sopify 定位为证据与授权层，但当前公开证明仍偏 runtime/installer。缺少"宿主不装 runtime、只消费 plan / handoff / receipts / sopify_writer 就能继续工作并写回证据"的硬验收。

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

把 Sopify 的核心真相源从 runtime 工作流系统切到 **AI 开发审计资产协议内核**：方案、决策、交接、执行/验证证据、归档记录都是可追溯资产；跨宿主接续是这些资产被正确消费后的硬验收。默认工作流和开发 skill 继续作为协议之上的产品体验层存在，消费 protocol assets 与 sopify_writer，但不再拥有独立 machine truth。

用一个 architecture 级方案包闭合四件事：

1. **协议内核 freeze + State 极简 cutover**：5 件 must-freeze schema 化 + state/ 从 6 个 legacy 文件压到 2 文件
2. **Registry 退场**：`plan/_registry.yaml` 及其生产/消费链路删除；不把多 plan 治理放进 P8 核心
3. **Runtime Phase 2 物理删除**：runtime/ 全删 + runtime gate / bundle / deep adapter 清理 + state/ 物理重构
4. **新宿主试点验收**：Qoder PROTOCOL_VERIFIED（full-capability, home-scope hybrid）+ 5 条全能力闭环 proof，证明审计资产协议可被真实宿主消费；Cursor 作为后续候选，不进 P8 硬验收

## Approach

- **协议内核，不是协议 v1**：只 freeze 5 件 must-freeze，draft 面保留为 draft
- **审计资产优先**：P8 的主叙事不是"换宿主很方便"，而是"AI 开发过程不只留下代码，还留下可追溯的方案、决策、证据和归档"；跨宿主接续是这些资产可携带的结果
- **默认工作流不退场**：P8 退的是 runtime router / engine / gate，不是 analyze / design / develop / kb / templates 等默认工作流与开发 skill；这些能力继续作为 host/prompt/skill 层消费协议资产，并用 runtime-independent ActionProposal 做请求准入
- **用户请求先于接续**：active_plan 是接续锚点，不是路由权威；host 先判断用户请求是 consult / quick fix / managed plan / continue / finalize 等，再决定是否读取 active_plan → plan.md → handoff → receipts
- **激进删除，零用户红利**：线上无用户，不需要渐进迁移、不需要 shadow writer、不需要 pre-commit 锁死
- **状态模型极简**：state/ 只留 2 文件（active_plan + current_handoff），"AI 等人"折叠进 current_handoff.required_host_action
- **Registry 不保留**：`_registry.yaml` 对用户不可读、对跨宿主接续非必需；P8 直接退场，后续如需 backlog 另做 human-readable work index
- **Compliance 先于删除**：W1 smoke 必须独立于 runtime import，否则不能作为 W2 删除 runtime 的验收基线
- **产品叙事切换**：docs/how-sopify-works 从 "runtime gate first" 重写为 "host executes, Sopify preserves auditable development assets"
- **新宿主试点是硬验收**：不是 installer smoke，而是"新宿主消费审计资产完成跨 session 接续并写回证据"

## P8 CLI Scope（最小集）

P8 不新增"运行任务"型 CLI，不做 `sopify run/route/finalize/gate`，也不把 `sopify_writer` 包成新的 runtime CLI。

只保留或新增 4 类脚本入口：

| CLI / Script | 类型 | P8 作用 | 边界 |
|---|---|---|---|
| `scripts/sopify_init.py` | 用户辅助 | 初始化/修复 `.sopify-skills/` 基础结构与激活标记 | 不路由、不写执行状态 |
| `scripts/sopify_status.py` | 只读辅助 | 展示 active plan、handoff health、latest receipt | 只读，不决策 |
| `scripts/sopify_doctor.py` | 只读诊断 | 检查安装、payload、schema、host asset 健康度 | 只读，不修复业务状态 |
| `scripts/sopify_protocol_check.py` | 开发/CI 验收 | 检查 new-plan / continuation / finalize 三场景 | 不 import runtime，不读取 `_registry.yaml` |

Qoder 接续写入优先走 `sopify_writer` 库 API；如果宿主限制导致不能调库，再评估一个薄 wrapper，默认不做。

## 三波次（串行）

### Wave 1 — Protocol + State Contract Cutover

**目标**：把协议和状态模型说清楚，给出可机器校验的最小基线

- W1.1 protocol.md 升级：5 件 must-freeze 字段 + schema（JSON Schema 或 CDDL）
- W1.2 protocol.md §2 升级：plan 包结构（plan.md 唯一入口 + 可选 tasks/design/assets + receipts 条件必备）+ plan.md 8 必备章节
- W1.3 protocol.md §6 升级：Verifier read-only contract（MUST_NOT 写 state/plan/blueprint）
- W1.4 protocol.md §8 升级：Host Protocol Entry Contract（request admission + managed/continuation/finalize 触发条件 + 4 步读顺序：active_plan → plan.md → current_handoff → receipts/）
- W1.4b prompt asset 入口摘要：宿主看到 `.sopify-skills/` 时必须先形成 runtime-independent ActionProposal；只有 managed plan / continuation / finalize 才执行 4 步 protocol entry，不再要求 `runtime_gate.py enter`
- W1.5 Define Registry Retirement Contract：protocol.md 明确 `_registry.yaml` deprecated by P8；design.md 记录删除理由；compliance smoke 检查 host entry path 不读取 `_registry.yaml`
- W1.5b Blueprint interim sync（W1 gate 前必须完成）：ADR-013/017 加注 P8 Scope Clarification（authorization 语义收窄）+ ADR-017 EAR 标注 [SUPERSEDED by P8] + 收敛链 produce→verify→authorize→settle → produce→verify→record evidence→settle + Core State Files 6→2 + persistence_red_line 重写 + 宿主能力治理段落加注 interim disclaimer
- W1.6 `scripts/sopify_protocol_check.py`：主链 smoke（new-plan / continuation / finalize 三场景）；**不得 import runtime/**
- W1.7 最小 fixture：repo-hosted minimal fixture + 1 个最小 external repo

**验收**：

- 文档自洽（protocol.md 各章节字段对得上）
- sopify_protocol_check.py 在 repo-hosted minimal fixture（`tests/fixtures/minimal_plan`）跑通 3 场景
- 蓝图 design.md Core State Files 段落已更新为 2 文件模型

### Wave 2 — Runtime Physical Retirement + State 物理重构

**目标**：runtime 不再是路由器；state/ 物理瘦身

- W2.1 Installer 5 文件解耦（validate / bootstrap_workspace / inspection / install_sopify / sopify_init 移除 runtime import）
- W2.2 CLI Helper 迁移（sopify_status / sopify_doctor 改消费 installer/inspection.py contract）
- W2.3 `sopify_writer` 命名与职责收敛（只写 protocol state + receipts，不路由、不执行、不调 AI）
- W2.4 State 物理重构：
  - 删 `state/current_run.json`（语义下沉到 plan.md status）
  - 删 `state/current_plan.json`（被 active_plan 替代）
  - 删 `state/current_clarification.json` / `current_decision.json`（折叠到 current_handoff.required_host_action）
  - 删 `state/current_archive_receipt.json`（真相进 history/receipt.md）
- W2.5 Clarification/Decision 折叠到 current_handoff.required_host_action
- W2.6 Registry 退场：删除 `plan/_registry.yaml`、registry 生产/消费代码、priority 建议渲染与 registry 测试
- W2.7 ✅ Tests 重分类：删 20 个 runtime 镜像测试 + 外科修 installer/status/release 测试 + 新增 sopify_writer 测试锚点（163 passed / 0 failed）
- W2.8 ✅ 删 runtime entry/smoke 脚本 + 清 validate.py smoke helper + 修 CONTRIBUTING 文档引用
- W2.9 ✅ Reclassify Protocol-Verified Hosts: `DEEP_VERIFIED` → `PROTOCOL_VERIFIED`（5 文件 tier 重命名，保留 Codex/Claude adapter）。边界：PROTOCOL_VERIFIED 验证 protocol entry + payload + bootstrap + handoff-first，不承诺 receipt/finalize write API（W2.9b/W3 scope）
- W2.10 ✅ 删除 `runtime/` 全目录（46 tracked files / ~15.6K LOC）+ CONTRIBUTING builtin catalog 真源修正 + sopify_writer/_resume.py docstring 修正。残留：`scripts/check-context-checkpoints.py` 中 Plan A scope 仍含旧 runtime 路径名，留 W3.6 治理叙事收口时统一清理
- W2.11 ✅ Writer Finalize API + Dogfood Mainline：StateStore → ProtocolStore(sopify_root) 重命名；新增 write_plan_receipt / write_history_receipt / finalize_plan（keyword-only）；33 writer tests；protocol smoke 3 场景全 PASS；184 passed / 0 failed

**P8 Extension Candidates（post-W3，非 P8 硬验收）**

- **W4 Copilot Workspace Protocol Uplift**
  - 目标：Copilot 从 `BASELINE_SUPPORTED` 提升到 `WORKSPACE_PROTOCOL_VERIFIED`（workspace instruction surface 已验证完整 protocol continuation + writer evidence）
  - Fallback：如 Copilot 宿主限制导致无法证明 writer/receipt/finalize，保留 `BASELINE_SUPPORTED` 或引入 `WORKSPACE_PROTOCOL_SUPPORTED` 作为中间态
  - 不现在新增枚举值，W4 执行时再加
  - 验收（硬标准）：
    - Copilot instructions 消费 protocol.md §8 四步链（active_plan → plan.md → current_handoff → receipts）
    - 可通过 sopify_writer 或明确批准的 thin wrapper 写 current_handoff 和 receipts
    - doctor_checks 扩展（不止 host_prompt_present）
    - 不声明 PAYLOAD_INSTALL，除非 Copilot 路径真的安装 payload
    - CONTINUATION 是 EnhancementGroup，不是 FeatureId
  - 依赖：W2.10（runtime 删除）+ W3（Qoder 硬验收完成）
  - 注册表保留形态差异：Codex/Claude/Qoder = protocol_verified / payload host；Copilot = workspace_protocol_verified / workspace host
  - **W3.6 文档收口不等待 W4**：如 W4 在文档前完成则同步纳入，否则按当前状态写 Copilot = baseline_supported

**验收**：

- W1 compliance smoke 仍绿
- runtime/ 不存在
- `plan/_registry.yaml` 不存在，且无 registry 生产/消费链路
- sopify_writer 是唯一写路径（grep 确认无 runtime 调用）
- state/ 只剩 active_plan + current_handoff 两个文件

### Wave 3 — Host Proof + Docs Cutover

**目标**：用 Qoder CLI 证明"只消费 protocol 文件与审计资产即可全能力接续"；文档叙事切换

**Qoder 架构裁定（审计收口结论）**：

- **Tier**：`PROTOCOL_VERIFIED`（与 Codex/Claude 同级全能力接续）
- **形态**：home-scope hybrid（`~/.qoder/AGENTS.md` + `~/.qoder/sopify/` payload；不接管 `.qoder/rules/`；不宣称 home skill tree 消费）
- **Host of record**：Qoder CLI only（IDE 文件面一致，不重复认证）
- **Writer**：sopify_writer 库 API 直调；仅 installed payload 调不通时才允许极薄 wrapper
- **全能力闭环**：5 条标准（request admission / 4 步读链 / writer 写回 / 跨 session proof / 默认工作流消费），详见 design.md §11.3

#### Phase 0 — Pre-flight Cleanup（W3 前置，消除自相矛盾）

在 Qoder proof 之前，先清理与 P8 2-file 模型和 runtime 退场相矛盾的残留：

- P0.1 删 stale state files：`state/current_decision.json` / `current_gate_receipt.json` / `current_run.json` / `last_route.json` / `sessions/`（协议只承认 2 文件）
- P0.2 删 `scripts/check-context-checkpoints.py`（整体无效：Plan A tasks 文件不存在，CHECKPOINT_FILE_REQUIREMENTS 引用已删除 runtime 文件）
- P0.3 删 `tests/test_context_checkpoints.py`（仅测上述死脚本）
- P0.4 清 `.githooks/commit-msg` / `.github/workflows/ci.yml` / `scripts/release-preflight.sh` / `tests/test_release_hooks.py` / `CONTRIBUTING.md` / `CONTRIBUTING_CN.md` 中对 check-context-checkpoints / Plan A Context-Checkpoint 的引用（原子 removal package）
- P0.5 重写 `.sopify-skills/project.md` §Runtime 实现与测试约定（L27-35 整段过时：runtime/models.py facade / runtime_test_support.py / .sopify-runtime smoke 全部不存在）
- P0.6 清 `.pytest_cache/`（引用已删除测试文件）

**验收**：legacy state files 已清退（当前实例只剩 `current_handoff.json`，`active_plan.json` 待后续 managed plan 创建时生成）；`rg "check.context.checkpoints\|plan-a-risk-adaptive"` 在活跃代码/配置中无匹配；`project.md` 无 runtime facade 引用。**用户文档旧 state 结构图（`docs/how-sopify-works*.md`）待 W3.5 收口，不阻断 W3.1。**

#### W3.1 Build Qoder PROTOCOL_VERIFIED Adapter

- [x] Depends: Phase 0
- [x] Input: existing Codex/Claude PROTOCOL_VERIFIED host patterns, Copilot workspace-scope adapter
- [x] Output: `installer/hosts/qoder.py`（home-scope hybrid adapter；destination_dirname=`.qoder`，header_filename=`AGENTS.md`，config_dir=`~/.qoder`，default_language=`zh-CN`）
- [x] Output: Qoder 注册进 `installer/hosts/__init__.py`
- [x] Output: Qoder prompt asset 消费 Host Protocol Entry Contract（复用共享 header.md.template，已是 post-P8 口径）
- [x] Output: prompt asset 明确 consult / quick_fix **不**自动接续 active plan
- [x] Output: `install.sh --target qoder` 安装路径（bare target via default_language）
- [x] Output: skills/hosts.yaml + distribution display name + 工具映射表 + golden snapshots + contract test 同步
- [x] Output: doctor/status 推荐命令通过 `_recommend_target` 适配 bare/explicit target
- [x] Verify: adapter does not import runtime
- [x] Verify: adapter does not depend on `_registry.yaml`
- [x] Verify: `.qoder/settings.local.json` / `.qoder/rules/` 不被当作 Sopify state
- [x] Verify: prompt asset does not instruct LLM to run `runtime_gate.py` or always auto-continue active plan
- [x] Verify: 181 passed / 0 failed / protocol smoke 3/3 PASS

#### W3.2 Qoder Continuation Writer Path（installed payload proof）

- [ ] Depends: W3.1
- [ ] Input: sopify_writer 2-file model + installed payload at `~/.qoder/sopify/`
- [ ] Output: Qoder 通过 installed payload 路径调 sopify_writer 写 `state/current_handoff.json`
- [ ] Output: Qoder 写 `plan/<id>/receipts/exec_NNN.json` / `verify_NNN.json`
- [ ] Output: 如 installed payload 路径调不通，记录 thin wrapper 为已知限制（wrapper 只透传 writer 写入）
- [ ] Verify: 不依赖 repo-local `sys.path.insert` 或 PYTHONPATH hack
- [ ] Verify: Qoder new session reads `active_plan → plan.md → current_handoff → receipts`

#### W3.3 End-to-End Proof Transcript

- [ ] Depends: W3.2
- [ ] Input: fixture repo
- [ ] Output: transcript showing session A writes handoff/receipt
- [ ] Output: transcript showing session B resumes from files via 4-step read chain
- [ ] Output: transcript showing session B writes new receipt
- [ ] Verify: transcript includes active_plan plan_id, plan.md Plan Snapshot or full-plan fallback, plan/task decision context, handoff required_host_action, latest receipt
- [ ] Verify: no command invokes runtime
- [ ] Verify: prompt does not force auto-continuation for consult / quick_fix requests
#### W3.5 Docs Narrative Cutover

- [ ] Depends: W3.3
- [ ] Input: README / README.zh-CN / docs/how-sopify-works(.en).md / docs/getting-started.md
- [ ] Output: main narrative becomes "host executes; Sopify preserves auditable AI development assets through protocol, file assets, sopify_writer, receipts"
- [ ] Output: docs describe the post-P8 product stack as protocol kernel + default workflow + skills/host adapters
- [ ] Output: docs clarify runtime retirement does not retire analyze/design/develop/kb/templates workflow or development skills
- [ ] Output: docs describe Qoder as PROTOCOL_VERIFIED full-capability host (home-scope hybrid)
- [ ] Output: architecture diagrams reflect 2 state files + plan/history/receipts
- [ ] Output: remove runtime gate first language
- [ ] Output: remove `_registry.yaml` from user-facing docs
- [ ] Verify: docs present cross-host continuation as a hard proof of asset portability, not the whole Sopify value proposition
- [ ] Verify: `rg "runtime gate|runtime/|_registry|current_run|current_plan" README.md README.zh-CN.md docs` returns no active legacy docs

#### W3.6 Blueprint Sync（全量叙事收口 — 11 项显式回写清单）
  - ADR-013 scope clarification 从 interim 升级为 final 语义边界
  - ADR-017 EAR 标注从 interim [SUPERSEDED] 升级为 final [RETIRED]
  - 底层哲学收敛链 produce→verify→authorize→settle → produce→verify→record evidence→settle
  - 实操协议层显式声明 write admission + archive admission 两个准入点
  - Protocol-first / Runtime-optional 三层定位更新（runtime 层标 legacy reference 或删除）
  - 核心管线 ActionProposal / Validator 表述（Validator 从"唯一授权者"收窄为 protocol admission）
  - Runtime 五层架构段落标 legacy reference 或删除
  - Core State Files / Persistence Surface / Mainline Keep-list 更新为 2 文件模型
  - 外部消费面 Keep-list 全面更新（删除 EAR/gate_receipt/runtime-only 面）
  - 宿主能力治理段落重定义（能力梯度、契约消费矩阵、官方接入画像、增强组合）
  - Runtime 退场路线标记完成 + LOC 数据更新

**验收（5 条全能力闭环 + 2 条工程约束）**：

1. Qoder prompt 完成 request admission（consult / quick_fix 不自动接续 active plan）
2. Qoder 消费 `state/active_plan.json` → `plan/<id>/plan.md` → `state/current_handoff.json` → `plan/<id>/receipts/` 4 步读链恢复上下文
3. Qoder 通过 sopify_writer（installed payload 路径）写 `state/current_handoff.json` + `plan/<id>/receipts/*.json`
4. Qoder 新 session 仅通过 4 步读链恢复并继续写新 receipt（跨 session proof）
5. Qoder 能继续 Sopify analyze / design / develop / finalize 主流程
6. **整条链路不依赖 runtime 进程**
7. **installed payload 路径验证通过**（不依赖 repo-local sys.path hack）

## 关键设计决策（详细论证见 design.md）

1. **审计资产是核心价值**：plan / tasks / design / handoff / receipts / history 把 AI 开发过程中的方案、决策、执行、验证、归档留成可追溯资产；跨宿主接续是这些资产可携带后的结果
2. **协议内核承载 truth，默认工作流承载体验**：P8 后 Sopify 仍有 analyze/design/develop/kb/templates 等默认工作流和开发 skill；它们不能定义额外 machine truth，只能读协议资产、通过 sopify_writer 写回状态和 receipts
3. **ActionProposal 保留在工作流层，不进 P8 must-freeze**：它用于请求准入和分发（consult / quick_fix / new_plan / continue_plan / finalize / ask_user 等），不再是 runtime gate 输入，也不新增核心 schema 文件
4. **plan_id 是跨宿主接续主键**；session_id 仅 provenance 审计字段
5. **state/ 极简到 2 文件**：active_plan（bootstrapping 锚）+ current_handoff（live continuation state + "AI 等人"信号）
6. **handoff 单态**：只在 state/current_handoff.json；finalize 时最后交接事实体现在 `receipts/final.json` + `history/receipt.md`，**不新造 plan/<id>/handoff.json**
7. **receipts/ 保留在 plan scope（条件必备）**：managed plan 产生执行/验证事件时必须写到 receipts/；finalize 时必须生成 receipts/final.json；light plan 如无 managed execution 可无 receipts/。作为过程审计资产，是跨宿主判断"是否验证过"的依据
8. **plan.md 是语义入口，顶部推荐有 Plan Snapshot 区块**（Goal / Status / Next / Task）；Plan Snapshot 不是目录索引，也不是权威审计事实，而是用户可读的当前状态快照和 host/LLM 默认只读的接续入口摘要。内部 schema 字段统一为可选的 `plan_snapshot`；缺失时 host 回退读取完整 plan.md。8 必备章节（Context/Why / Scope / Approach / Waves / Key Decisions / Constraints / Status / Next）仍是 plan.md 的必备正文
9. **"AI 等人"折叠到 current_handoff.required_host_action**：复用蓝图已定义的 canonical 语义（answer_questions / confirm_decision 等），不新增字段
10. **`_registry.yaml` 退场**：当前 registry 是 observe-only 内部治理索引，不属于用户价值或跨宿主接续主链；P8 删除，不做 optional 保留
11. **不加 status.json / 不加 plan-level README.md / plan/<id>/handoff.json / pending_* / last_archive_receipt**
12. **plan 包分级 light / standard / architecture**：渐进披露
13. **assets/ 替代 references/**：统一放架构图、截图、长参考材料
14. **Verifier read-only contract 只 freeze schema**：P8 写清 verifier MUST_NOT 写 state/plan/blueprint；cross-review bridge 实现不作为 P8 必须项
15. **EAR / gate receipt 在 P8 显式退场**：ExecutionAuthorizationReceipt / current_gate_receipt 是 pre-P8 runtime-gate 授权模型产物，不迁移到 protocol kernel；P8 之后的审计主链改由 `plan/<id>/receipts/*.json` + `history/<id>/receipt.md` 承担
16. **blueprint persistence_red_line 必须同步改写**：不是只改 protocol.md；必须把旧 `state/current_run/current_plan/current_handoff/current_clarification/current_decision` 红线重写为 post-P8 persistence model，避免蓝图 keep-list 与 P8 目标态冲突
17. **current_handoff schema cutover 必须显式**：这是 strict schema 变更，不允许靠实现收缩隐式带过；required 字段集、删除字段、保留字段都要在 W1 明确
18. **P8 Scope Clarification — 授权语义显式收窄**：P8 后"Authorization"不再指 pre-execution side-effect approval（该职责退回宿主原生权限、sandbox、用户确认、工具审批）。Sopify 保留的 authorization 语义收窄为 protocol admission（sopify_writer schema/contract 校验）、receipt validity（证据链完整性）、archive admission（归档准入）。EAR / gate_receipt 作为 pre-execution authorization artifact 在 P8 显式退场。ADR-013 标题不改（不做品牌手术），但在 ADR-013 / ADR-017 正文加注 P8 Scope Clarification；ADR-017 ExecutionAuthorizationReceipt 标注 [SUPERSEDED by P8]。收敛链从 produce → verify → authorize → settle 收窄为 produce → verify → record evidence → settle；实操协议层拆为 write admission（sopify_writer）+ archive admission（finalize）两个准入点
19. **全能力接续原则**：宿主接法可以不同（home-scope / workspace-scope / hybrid），但 Sopify 的能力合同应该尽量相同。差异压在 adapter 层，不跑到产品能力层。所有 PROTOCOL_VERIFIED 宿主对齐 5 条全能力闭环（request admission / 4 步读链 / writer 写回 / 跨 session proof / 默认工作流消费）
20. **Qoder = PROTOCOL_VERIFIED home-scope hybrid**：与 Codex/Claude 同级 tier；`~/.qoder/AGENTS.md` + `~/.qoder/sopify/` payload；不接管 `.qoder/rules/`（用户 override 层）；不宣称 home skill tree 消费；host of record = Qoder CLI only
21. **Writer 调用边界**：sopify_writer 库 API 直调为默认；仅 installed payload 场景下调不通时才允许极薄 wrapper；wrapper 只透传 writer 写入，不得做路由或执行
22. **Phase 0 前置清理**：W3 proof 之前先消除自相矛盾（stale state files / dead checkpoint governance 链 / project.md runtime 约定），否则 proof 期间一直带着与 2-file model 冲突的残留
23. **Narrative cutover 在 proof 之后**：README / docs 不能在 Qoder proof 通过前做出"跨宿主已成立"的承诺

## 目标项目结构（详细字段定义见 design.md）

```
.sopify-skills/
├── project.md                        # git-tracked | 项目约定
├── blueprint/                        # git-tracked | 长期知识
│   ├── README.md / background.md / design.md / tasks.md / protocol.md
├── plan/<plan_id>/                   # git-tracked | 活动工作 + 过程审计资产
│   ├── plan.md                       # 唯一语义入口（推荐含 Plan Snapshot + 必备正文）
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

## Host Protocol Entry Contract（最小入口约束）

P8 删除 runtime gate 后，入口约束由 host prompt asset + protocol.md 共同承担，不新造 CLI 或 state 文件。

**触发条件**：

- 宿主/LLM 在 workspace 中检测到 `.sopify-skills/sopify.json` 或 `.sopify-skills/` 时，必须先形成 runtime-independent ActionProposal，判断用户请求属于 consult / quick_fix / new_plan / continue_plan / finalize / ask_user / 其他 host-supported action。
- 只有 ActionProposal 指向 managed plan / continuation / finalize 时，才执行 4 步 protocol entry。
- consult / unmanaged quick_fix 不自动接续 active_plan；必要时只读取 blueprint/project 轻上下文。
- 如果 `.sopify-skills/` 不存在，则按普通宿主行为处理；不要创建隐式 state。

**入口动作（4 步，仅 managed plan / continuation / finalize）**：

```
1. state/active_plan.json         → 定位 plan_id（如无 → consult / new-plan）
2. plan/<id>/plan.md              → 语义入口：做什么 + 进度（真相源）
3. state/current_handoff.json     → 恢复提示 + 是否等用户（required_host_action）
4. plan/<id>/receipts/            → 取最新 1-3 个 receipt，知道"哪些被验证过"
```

**约束边界**：LLM 可直接读 protocol 文件；写 `state/active_plan.json`、`state/current_handoff.json`、`plan/<id>/receipts/*.json` 时必须走 `sopify_writer`。Host prompt 负责 request admission 与默认 spec workflow 入口，不负责生成机器真相、不生成计划优先级、不执行验证。

**读取预算红线**：protocol entry 默认只读小入口，不得全量灌入 protocol.md / design.md / receipts/。

- `active_plan.json` / `current_handoff.json`：完整读取（必须保持小文件）
- `plan.md`：如存在 Plan Snapshot，默认只读该区（Goal / Status / Next / Task）；如缺失或与正文/receipts 冲突，回退读完整 plan.md → tasks.md → design.md → assets
- `receipts/`：默认只读最新 1-3 个 receipt（详见 design.md §6.2b Receipts Latest-Only 算法）；不得全量读历史 receipts
- `assets/` / 长设计材料：只在当前任务明确需要时读取

**顺序设计原则**：active_plan 定位后先读 plan.md 建立语义真相，再读 current_handoff 作为恢复提示——**避免 handoff 反过来变成第二真相源**。current_handoff.required_host_action 复用蓝图 canonical 值（continue_host_develop / answer_questions / confirm_decision / continue_host_consult / resolve_state_conflict）。

## Plan 包分级（Progressive Disclosure）

| 级 | 文件 | 适用场景 |
|---|---|---|
| **light** | plan.md | 小任务、单步修复、探索性提案 |
| **standard** | plan.md + tasks.md | 多任务、需逐项验收 |
| **architecture** | plan.md + design.md + tasks.md + receipts/ + assets/ | 架构级、协议级、状态模型变更 |

**规则**：

- plan.md 是**唯一语义入口**，顶部推荐有 Plan Snapshot 区块（Goal / Status / Next / Task），然后是 8 必备章节；Plan Snapshot 是用户可读的派生状态快照和接续入口摘要，不是目录索引或新状态文件，不作为唯一审计依据
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
- plan/_registry.yaml（P8 删除；后续如需 backlog，另做 human-readable work index）
- Integration Contract 中的 Producer / Knowledge Provider（仅 Verifier 升格）
- Multi-host review contract / Plugin admission（延后）
- ExecutionAuthorizationReceipt / current_gate_receipt（P8 显式 retire，不迁入 5 件 must-freeze）

## 硬约束（P8 内部红线）

1. Wave 1 未收口前不动 Wave 2（文档自洽先于物理删除）
2. Wave 2 未收口前不动 Wave 3（runtime 删除前，新宿主不能依赖 runtime）
3. 任何与 blueprint keep-list / persistence_red_line / 对外承诺分层表冲突的地方，必须在 W1/W3 显式回写；不得只删实现不改权威文档
4. 新宿主试点必须证明"不依赖 runtime 进程即可接续"，否则 P8 不算收口
5. Verifier read-only 约束是 MUST，违反则 verdict 降级为 advisory（不自授权）
6. state/ 只能有 2 文件；新增任何 state 文件必须 ADR
7. `plan/_registry.yaml` 不得作为 active plan pointer 或 host 入口依赖；P8 内删除
8. 所有 plan 包必须遵守 light / standard / architecture 三档分级

## 削减预算对齐（对照蓝图 design.md 削减预算表）

| 维度 | P8 前 | P8 后 | 红线 |
|---|---|---|---|
| Checkpoint types | 2 (canonical) | 2 | 不变 |
| required_host_action | 5 (canonical) | 5 | 不变（复用） |
| Route families | 6 (canonical) | **不承诺** | deep runtime 删除后 route 语义下沉到 handoff contract |
| Core state files | 6 (authoritative) | **2** | active_plan + current_handoff；其他全部删除或折叠 |
| Plan registry | 1 observe-only machine registry | **0** | 删除 `_registry.yaml` 与 registry 生产/消费链路 |

**重大更新**：Core state files 6 → 2。这是蓝图 design.md §Core State Files 段落的显式调整，P8 收口后需回写蓝图。

## 与蓝图对齐

- 挂在蓝图主航道 P5/P6/P7 延长线上（符合 hard max §8）
- 吸收蓝图 open backlog：Runtime retirement Phase 2 / 第三方宿主自助接入证明 / Protocol Compliance Phase 2
- **显式调整蓝图**：Core state files 6 → 2；§State Model 重写；§Plan Package Structure 新增
- **显式调整蓝图**：persistence_red_line 从 pre-P8 runtime state 集合切到 post-P8 persistence model；ExecutionAuthorizationReceipt 从 Now/✅ 退场，并把 receipts/history receipt 写入新的审计承诺面
- **显式调整蓝图（W1 中期同步）**：ADR-013 加注 P8 Scope Clarification（authorization 语义收窄）；ADR-017 EAR 标注 [SUPERSEDED by P8]；收敛链 produce→verify→authorize→settle → produce→verify→record evidence→settle；宿主能力治理段落加注 interim disclaimer（deep_verified / 审计增强 / EAR 相关表述在 P8 后失效）
- 收口后回写蓝图（W3.6 全量叙事收口）：design.md §Runtime 退场完成 + §State Model + §Plan Package Structure + tasks.md + protocol.md §8/state file index + ADR-013 scope clarification 升级为 final + ADR-017 EAR 从 SUPERSEDED 升级为 RETIRED + 核心管线 Validator 表述 + Runtime 五层架构标 legacy + 外部消费面 Keep-list + 宿主能力梯度重定义

## 不在 P8（明确延后）

- Knowledge_sync novelty_rationale 字段（吸收 v3 新颖性检查；独立 slice）
- Multi-host review contract 升格（等 P8 协议内核 freeze 后评估）
- cross-review verifier bridge enforcement（P8 仅 freeze read-only schema；桥接实现后续独立做）
- Plugin admission + Verifier evidence 标准化（设计阶段）
- Skill packaging / localization governance（独立延后）
- 多宿主扩展（P9 延后；Windsurf 放 P9）

## 风险与缓解

| 风险 | 严重度 | 缓解 |
|---|---|---|
| runtime 16K LOC 删除后暴露未知依赖 | 高 | W1 compliance smoke 先行建立契约基线；W2 dogfood smoke 验证主链 |
| State 重构破坏现有 host 接续 | 中 | W2 W2.3 物理重构后立刻跑 dogfood smoke 验证 |
| installer 5 文件解耦时发现隐式 import | 中 | 逐个文件做 import graph 审计（Phase 1 经验） |
| 删除 registry 后失去多 plan 优先级建议 | 低 | 接受该取舍；P8 聚焦跨宿主接续，backlog/index 后续按 human-readable 方式重做 |
| sopify_writer 未经历真实场景考验 | 中 | W3 Qoder proof 强制走 sopify_writer 写路径，作为硬验收 |
| Qoder 试点卡在宿主能力限制 | 中 | 基线是 payload + 完整接续读写；若不能直接调库，只允许薄 writer wrapper，不扩大成 runtime CLI |
| Verifier read-only 约束被绕过 | 中 | P8 只做 schema freeze + compliance；bridge enforcement 后续独立落地 |
