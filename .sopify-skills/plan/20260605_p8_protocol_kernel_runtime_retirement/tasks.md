---
title: P8 Protocol Kernel & Runtime Retirement — Tasks
plan_id: 20260605_p8_protocol_kernel_runtime_retirement
status: pending
created: 2026-06-05
---

# Tasks

> 三波次严格串行：W1 contract baseline → W2 physical cutover → W3 host proof/docs。
> 状态标记：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成 / `[-]` 阻塞 / `[·]` 取消
> 每个切片必须闭合：Depends / Input / Output / Verify 均明确后才执行。

## Wave 1 — Protocol + Contract Baseline

目标：先建立不依赖 runtime 的协议基线。W1 未绿，禁止删除 runtime。

### W1.1 Freeze 5 Must-Freeze Schemas

- [x] Depends: P6 writer 基础（当前 `canonical_writer`）+ sopify_contracts 已存在
- [x] Input: `design.md §2` / `protocol.md` 当前 Integration Contract / state 现状
- [x] Output: `sopify_contracts/schemas/active_plan.schema.json`
- [x] Output: `sopify_contracts/schemas/current_handoff.schema.json`
- [x] Output: `sopify_contracts/schemas/plan_md_sections.schema.json`
- [x] Output: `sopify_contracts/schemas/plan_receipt.schema.json`
- [x] Output: `sopify_contracts/schemas/history_receipt.schema.json`
- [x] Verify: schema 文件不 import `runtime`
- [x] Verify: `active_plan` schema 只允许 `plan_id`
- [x] Verify: `current_handoff.required_host_action` 只允许 canonical 5 值
- [x] Verify: `current_handoff` post-P8 required 字段集明确为 `schema_version` / `plan_id` / `required_host_action`
- [x] Output: `route_name` / `run_id` / `handoff_kind` / `resolution_id` 默认从 post-P8 `current_handoff` schema `properties` 中全删；未来如需 provenance 字段，必须另走 ADR 重加
- [x] Verify: `current_handoff.schema.json` 不再声明 `route_name` / `run_id` / `handoff_kind` / `resolution_id`
- [x] Note: schema draft files may exist locally before this task is completed; W1.1 is done only after protocol/compliance review closes the fields.

### W1.2 Rewrite protocol.md Kernel Sections

- [x] Depends: W1.1 schema 字段已确定
- [x] Input: `.sopify-skills/blueprint/protocol.md`
- [x] Output: protocol.md §2 plan package structure 改为 `plan.md` 唯一语义入口
- [x] Output: protocol.md §6 verifier read-only contract 升格为 MUST
- [x] Output: protocol.md §6 明确 ExecutionAuthorizationReceipt 为 `[RETIRED in P8]`，并把 post-P8 审计主链指向 `plan/<id>/receipts/*.json` + `history/<id>/receipt.md`
- [x] Output: protocol.md §8 Host Protocol Entry Contract：request admission、触发条件、4 步读顺序、读取预算、读后分叉、写回边界
- [x] Output: protocol.md §8 明确 ActionProposal 是 runtime-independent workflow/admission 概念，不是 P8 must-freeze schema，不再作为 runtime gate 输入
- [x] Output: protocol.md §8 用新的 Host Protocol Entry Contract 整节替换 pre-P8 deep runtime gate 正文，只保留一行 retirement note 指向历史背景
- [x] Output: host 在 ActionProposal 指向 managed plan / continuation / finalize 时，入口读顺序为 `active_plan → plan.md → current_handoff → receipts`
- [x] Output: protocol.md state file index 改为 2 文件
- [x] Verify: protocol.md 不再要求 `runtime_gate.py enter`
- [x] Verify: protocol.md 不要求所有用户请求都自动接续 active_plan
- [x] Verify: protocol.md 不再把 `current_run/current_plan/current_decision/current_clarification/current_archive_receipt` 作为主链必读
- [x] Verify: protocol.md §8 旧 gate-first normative 内容不存在；若有历史说明，仅允许 retirement note
- [x] Verify: protocol.md 明确 `_registry.yaml` 不属于 protocol kernel
- [x] Verify: protocol.md 明确 prompt asset 负责触发 protocol entry，但不得定义 runtime router
- [x] Verify: protocol.md 明确默认不得全量读取 protocol.md / design.md / receipts/

### W1.3 Define Host Prompt Plan Snapshot

- [x] Depends: W1.2
- [x] Input: current host prompt assets / installer host payload patterns
- [x] Output: host prompt summary says: if `.sopify-skills/` exists, first form a runtime-independent ActionProposal for request admission
- [x] Output: prompt summary says: only managed plan / continuation / finalize ActionProposal enters the 4-step protocol entry
- [x] Output: prompt summary includes ActionProposal categories, 4-step entry order, read budget, and `sopify_writer` write boundary
- [x] Output: prompt summary explicitly states that default spec workflow (analyze → design → develop → finalize) is a prompt asset / skill layer function, not runtime logic
- [x] Output: prompt summary does not mention `runtime_gate.py`, route families, or `_registry.yaml`
- [x] Verify: Qoder prompt asset can be generated from the same Plan Snapshot rules
- [x] Verify: host prompt text is short enough to avoid becoming a second protocol.md
- [x] Verify: host prompt does not instruct LLM to load full protocol.md by default
- [x] Verify: host prompt does not imply consult / quick_fix must continue active_plan

### W1.4 Define Plan Package Required Sections

- [x] Depends: W1.2
- [x] Input: current plan package examples under `.sopify-skills/plan/`
- [x] Output: plan.md recommended Plan Snapshot + 8 required sections documented: Plan Snapshot (Goal/Status/Next/Task; optional schema field `plan_snapshot`) + Context/Why / Scope / Approach / Waves / Key Decisions / Constraints / Status / Next
- [x] Output: Plan Snapshot is the default read window for LLM when present; host falls back to full plan.md when absent or conflicting
- [x] Output: Plan Snapshot is documented as user-readable derived status snapshot and continuation entry summary, not directory index, not `_registry.yaml` replacement, not a new state file, and not authoritative audit evidence
- [x] Verify: `plan_snapshot` schema 注释明确它只是 plan.md 顶部区块的 schema 抽象，不是独立 carrier，不是 machine truth，不覆盖正文或 receipts
- [x] Output: light / standard / architecture 三档文件矩阵
- [x] Output: receipts 条件必备规则
- [x] Verify: 不新增 `status.json`
- [x] Verify: 不新增 plan-level `README.md`
- [x] Verify: 不新增 `plan/<id>/handoff.json`

### W1.5 Define Registry Retirement Contract

- [x] Depends: W1.2
- [x] Input: `runtime/plan/registry.py` / `_registry.yaml` / registry tests
- [x] Output: protocol.md 明确 `_registry.yaml` deprecated by P8
- [x] Output: design.md 记录 registry 删除理由和后续替代原则
- [x] Output: compliance smoke 需要检查 host entry path 不读取 `_registry.yaml`
- [x] Verify: `_registry.yaml` 不在 must-freeze 列表
- [x] Verify: host 入口读顺序不包含 registry

### W1.5b Blueprint Interim Sync + persistence_red_line + promise surface

- [x] Depends: W1.1 / W1.2
- [x] Input: `.sopify-skills/blueprint/design.md` keep-list / persistence_red_line / 对外承诺分层表 / ADR-013 / ADR-017
- [x] Output: P8 design 明确 blueprint `persistence_red_line` 将从 pre-P8 runtime state 集合切到 post-P8 persistence model
- [x] Output: P8 design 明确 ExecutionAuthorizationReceipt / current_gate_receipt 在 P8 中 retire，而不是静默丢失
- [x] Output: W3 blueprint sync 需要同步更新对外承诺分层表（EAR 从 Now/✅ 退场，receipts/history receipt 写入新的审计承诺面）
- [x] Output: ADR-013 正文加注 P8 Scope Clarification（authorization 语义收窄为 protocol admission / receipt validity / archive admission；不再指 pre-execution side-effect approval；实操层拆为 write admission + archive admission 两个准入点）
- [x] Output: ADR-017 ExecutionAuthorizationReceipt 标注 [SUPERSEDED by P8]
- [x] Output: 蓝图 design.md 收敛链从 produce→verify→authorize→settle 改为 produce→verify→record evidence→settle
- [x] Output: 蓝图 design.md Core State Files target 6→2
- [x] Output: 蓝图 design.md 宿主能力治理段落加注 interim disclaimer（deep_verified / 审计增强 / EAR 相关表述在 P8 后失效，W3.6 全量重定义）
- [x] Output: 蓝图 design.md “Validator 是唯一授权者” 表述收窄为 protocol admission / receipt validity / archive admission
- [x] Verify: P8 不再只写 “Core state files 6 → 2”，还明确 red-line / keep-list / promise surface 的同步回写要求
- [x] Verify: 蓝图 design.md 中 EAR 不再标记为 Now/✅/normative
- [x] Verify: 蓝图 design.md 中 “Validator 是唯一授权者” 表述已收窄
- [x] Verify: ADR-017 ExecutionAuthorizationReceipt 已标注 [SUPERSEDED by P8]

### W1.6 Build Runtime-Free Compliance Smoke

- [x] Depends: W1.1 / W1.2 / W1.3 / W1.4 / W1.5 / W1.5b
- [x] Input: schema files + filesystem fixture
- [x] Output: `scripts/sopify_protocol_check.py`
- [x] Output: CLI: `python3 scripts/sopify_protocol_check.py check --scenario <new-plan|continuation|finalize> --fixture <path>`
- [x] Output: JSON report with scenario, verdict, failures, evidence
- [x] Output: CLI is dev/CI smoke only; not a `sopify run/finalize/route` replacement
- [x] Verify: `rg "from runtime|import runtime" scripts/sopify_protocol_check.py` returns no matches
- [x] Verify: new-plan scenario writes/validates `state/active_plan.json` + `plan/<id>/plan.md`
- [x] Verify: continuation scenario reads 4-step entry order
- [x] Verify: continuation scenario fails if prompt/protocol entry references `runtime_gate.py`
- [x] Verify: continuation scenario fails if prompt/protocol entry requires active_plan continuation for every user request
- [x] Verify: prompt/protocol entry explicitly states consult / unmanaged quick_fix does not enter active_plan continuation by default
- [x] Verify: continuation scenario fails if protocol.md §8 still contains pre-P8 gate-first normative body text
- [x] Verify: continuation scenario fails if protocol.md still lists `current_run/current_plan/current_clarification/current_decision/current_gate_receipt` as主链必读
- [x] Verify: continuation scenario fails if prompt/protocol entry requires full protocol.md/design.md/receipts directory reads by default
- [x] Verify: finalize scenario checks `receipts/final.json`, history receipt, and no non-P8/legacy state files
- [x] Verify: any `_registry.yaml` in entry path fails compliance

### W1.7 Create Minimal Fixtures

- [x] Depends: W1.6
- [x] Input: repo-hosted minimal fixture + minimal external fixture directory
- [x] Output: repo-hosted minimal fixture dogfood
- [x] Output: minimal external repo fixture under tests/fixtures or temporary generated path
- [x] Output: consult/quick_fix admission fixture: active_plan exists, user request is unrelated consult or unmanaged quick_fix, expected behavior does not enter 4-step continuation
- [x] Verify: fixtures do not need runtime process
- [x] Verify: protocol check passes all 3 scenarios on repo-hosted minimal fixture (`tests/fixtures/minimal_plan`)
- [x] Verify: compliance passes continuation scenario on external fixture
- [x] Verify: consult/quick_fix admission fixture is represented as text-level expected behavior or compliance assertion; no LLM behavior test required

### Wave 1 Gate

- [x] Depends: W1.1-W1.7
- [x] Verify: `python3 scripts/sopify_protocol_check.py check --scenario new-plan --fixture tests/fixtures/minimal_plan`
- [x] Verify: `python3 scripts/sopify_protocol_check.py check --scenario continuation --fixture tests/fixtures/minimal_plan`
- [x] Verify: `python3 scripts/sopify_protocol_check.py check --scenario finalize --fixture tests/fixtures/minimal_plan`
- [x] Verify: `rg "runtime_gate|current_run|current_plan|_registry" .sopify-skills/blueprint/protocol.md` only returns legacy notes marked retired or no matches
- [x] Verify: protocol.md §8 已完成整节替换；旧 deep runtime gate 正文不存在
- [x] Verify: host prompt entry summary exists and does not reintroduce runtime routing
- [x] Verify: ADR-013 正文已加注 P8 Scope Clarification（authorization 语义收窄）
- [x] Verify: ADR-017 ExecutionAuthorizationReceipt 已标注 [SUPERSEDED by P8]
- [x] Verify: 蓝图 design.md 收敛链已改为 produce → verify → record evidence → settle
- [x] Verify: 蓝图 design.md 宿主能力治理段落已加注 interim disclaimer
- [x] Verify: 蓝图 design.md 中 EAR 不再标记为 Now/✅/normative
- [x] Verify: 蓝图 design.md 中 "Validator 是唯一授权者" 表述已收窄为 protocol admission / receipt validity / archive admission
- [x] Stop: W1 gate must pass before W2 starts

---

## Wave 2 — Physical Runtime Retirement

目标：硬切到 protocol kernel。线上用户少，不做 shadow writer，不保留 runtime compatibility layer。

### W2.0a Registry Snapshot

- [x] Depends: W1 gate
- [x] Input: `.sopify-skills/plan/_registry.yaml`（当前全部 registry entries，当前预期 4 条）
- [x] Output: 导出当前全部 registry entries 为人类可读摘要，存入当前 P8 plan 的 `assets/registry-lifecycle-snapshot.md`（随 P8 归档时一起进 history）
- [x] Verify: 快照文件存在于 `assets/` 且包含全部 plan 的 id + lifecycle_state + 关键时间戳

### W2.0b Catalog Relocation + Generator Runtime-Free

- [x] Depends: W1 gate
- [x] Input: `runtime/builtin_skill_packages/*/skill.yaml`（5 个 builtin skill YAML 源）
- [x] Input: `runtime/builtin_catalog.generated.json`
- [x] Input: `runtime/skill_schema.py` / `runtime/_yaml.py`
- [x] Output: 迁移 YAML 源 → `skills/catalog/<skill_id>/skill.yaml`（扁平路径，去掉 `builtin_skill_packages/` 中间层）
- [x] Output: 迁移生成产物 → `skills/catalog/builtin_catalog.generated.json`
- [x] Output: 迁移 `runtime/skill_schema.py` → `sopify_contracts/skill_schema.py`（保留旧名，不改为 skill_manifest.py）
- [x] Output: 创建 `scripts/_yaml_subset.py`：仅 `load_yaml` 最小解析子集，不含 `dump_yaml` / 写逻辑
- [x] Output: 改造 `scripts/generate-builtin-catalog.py`：import 改为 `sopify_contracts.skill_schema` + `_yaml_subset`；输入路径改为 `skills/catalog/*/skill.yaml`；输出路径改为 `skills/catalog/builtin_catalog.generated.json`
- [x] Output: 从 skill schema normalizer（`normalize_skill_manifest`）和 generated JSON 删除 `runtime_entry` + `entry_kind` + `supports_routes` 字段
- [x] Output: 更新 CI drift check 路径（`ci.yml:36` + `scripts/release-preflight.sh:28,70`）
- [x] Output: 更新 `skills/{en,zh}/header.md.template:351` 对 generated JSON 路径的引用
- [x] Verify: `python3 scripts/generate-builtin-catalog.py` 成功输出 `skills/catalog/builtin_catalog.generated.json`
- [x] Verify: generated JSON 不含 `runtime_entry` / `entry_kind` / `supports_routes` 字段
- [x] Verify: `rg "from runtime|import runtime" scripts/generate-builtin-catalog.py` returns no matches

### W2.1 Extract/Keep Minimal CLI Entrypoints

- [x] Depends: W1 gate
- [x] Input: `scripts/sopify_init.py` / `scripts/sopify_status.py` / `scripts/sopify_doctor.py` / `installer/inspection.py`
- [x] Output: `sopify_init.py` only bootstraps/fixes workspace layout and activation marker
- [x] Output: `sopify_status.py` is read-only: active plan pointer, handoff health, protocol state file health
- [x] Output: `sopify_doctor.py` is read-only: install/payload/schema/host asset health
- [x] Output: helper names and user-facing CLI args preserved only where still relevant
- [x] Output: no new `sopify run/route/finalize/gate` CLI
- [x] Verify: `rg "from runtime|import runtime" scripts/sopify_init.py scripts/sopify_status.py scripts/sopify_doctor.py installer/inspection.py` returns no matches
- [x] Verify: status/doctor still report workspace activation, plan pointer, handoff health

### W2.2 Decouple Installer Core

- [x] Depends: W2.1
- [x] Input: `installer/sopify_bundle.py` / `installer/validate.py` / `installer/bootstrap_workspace.py` / `installer/payload.py` / `scripts/install_sopify.py` / `runtime/manifest.py`
- [x] Output: runtime bundle 概念收缩退场——installer 不再打包 `runtime/` 目录，不再引用 `scripts/sopify_runtime.py`、`scripts/runtime_gate.py`、`scripts/check-bundle-smoke.sh`
- [x] Sub-step 2.2a: 删除或空化 `installer/sopify_bundle.py`（移除 `_DIRECTORY_ASSETS` 中的 `"runtime"` 条目、`_SCRIPT_ASSETS` 中的 `sopify_runtime.py` / `runtime_gate.py` / `check-bundle-smoke.sh`、`from runtime.manifest import write_bundle_manifest` import）；如果 bundle 整体概念退场，直接删除此文件
- [x] Sub-step 2.2b: 更新 `installer/validate.py` 的 `expected_bundle_paths()`——移除 `runtime/__init__.py`、`runtime/gate.py`、`scripts/sopify_runtime.py`、`scripts/runtime_gate.py` 必备路径
- [x] Sub-step 2.2c: 更新 `installer/bootstrap_workspace.py` 的 `_REQUIRED_BUNDLE_FILES`——移除上述 runtime 必备文件
- [x] Sub-step 2.2d: 检查 `installer/payload.py` 中 bundle 同步调用链——如引用 `sopify_bundle.sync_runtime_bundle`，移除或替换为仅同步 `sopify_contracts/` + `canonical_writer/`（或后续 `sopify_writer/`）
- [x] Sub-step 2.2e: 更新 `scripts/install_sopify.py` 中对 bundle 路径的校验——不再要求 runtime 文件存在
- [x] Sub-step 2.2f: 去 runtime 化 `installer/payload.py` 中的 payload manifest 能力字段和路径——移除 `"runtime_gate": True`、`"runtime_entry_guard": True` capability 字段（line 28-29）；重命名 `_install_versioned_runtime_bundle` 函数（去 runtime 前缀）；更新 `"default_bundle_dir": ".sopify-runtime"` 路径为 post-P8 payload 目录名；清理 `sync_runtime_bundle` import（line 15）
- [x] Verify: `rg "runtime_gate|sopify_runtime|runtime/|write_bundle_manifest|runtime_entry_guard|_install_versioned_runtime|sopify-runtime|sync_runtime_bundle" installer scripts/install_sopify.py` returns no active dependency（仅允许注释/docstring 中的 retired 说明）
- [x] Verify: install smoke 仍能安装 payload assets（sopify_contracts + canonical_writer/sopify_writer）
- [x] Verify: installer 不再依赖 `runtime/manifest.py` 的传递 import（builtin_catalog / entry_guard / clarification / decision / handoff / knowledge_layout / router）
- [x] Note: 额外完成项——`preferences_preload` / `SMOKE_VERIFIED` capability 从 FeatureId enum + host adapter declared/verified features + doctor_checks + inspection 全链路退场；bundle manifest 补写 capabilities 字段对齐 `_REQUIRED_BUNDLE_CAPABILITIES`；doctor_checks() 不再输出 bundle_smoke；蓝图 design.md persistence red-line 补 preferences_preload retirement note

### W2.2b Catalog Payload Resource

- [x] Depends: W2.2, W2.0b
- [x] Input: `skills/catalog/builtin_catalog.generated.json` / `installer/payload.py` / `installer/inspection.py`
- [x] Output: `installer/sopify_bundle.py` 安装时拷贝 `builtin_catalog.generated.json` 到 payload bundle `catalog/` 子目录
- [x] Output: bundle manifest 和 `payload-manifest.json` 均记录 `catalog_path`
- [x] Output: `sopify_doctor` 通过 `expected_bundle_paths` + `_REQUIRED_BUNDLE_FILES` 检查 catalog 文件存在性（payload_present check 链路覆盖）
- [x] Verify: `sync_payload_bundle` 输出目录包含 `catalog/builtin_catalog.generated.json`（4 entries）
- [x] Verify: bundle manifest `catalog_path` 字段指向正确路径

### W2.3 Rename and Scope sopify_writer

- [x] Depends: W1 schemas
- [x] Input: `canonical_writer/` / `sopify_contracts/*`
- [x] Output: package/module surface becomes `sopify_writer`
- [x] Output: public writer role documented as "the writer for Sopify protocol state and receipts"
- [x] Output: writer allowed writes: `state/active_plan.json`, `state/current_handoff.json`, `plan/<id>/receipts/*.json`, `history/<id>/receipt.md`
- [x] Output: writer must not route, choose plan priority, call AI, execute tasks, or orchestrate hosts
- [x] Verify: no new writer CLI is introduced by default
- [x] Verify: old `canonical_writer` import path is removed; no compatibility alias by default
- [x] Note: W2.3 完成 public surface scope（`__all__` 只导出 `iso_now`；StateStore 降级为 `sopify_writer.store` 内部临时实现，runtime/ 通过 `from sopify_writer.store import StateStore` 访问）；具体 2-file writer API / StateStore method migration 归 W2.4

### W2.3b CI Runtime Detachment

- [x] Depends: W2.3, W2.0b
- [x] Input: `.github/workflows/ci.yml` / `scripts/release-preflight.sh`
- [x] Output: restructure `runtime-tests` job 为 `protocol-tests` job：删除 runtime-only test steps，保留 catalog drift / protocol smoke / installer-payload smoke / 非 runtime 测试
- [x] Output: 删除 `check-bundle-smoke.sh` step
- [x] Output: 删除 `check-prompt-runtime-gate-smoke.py` step
- [x] Output: 改写 `check-install-payload-bundle-smoke.py` 为 payload/catalog smoke（移除 runtime bundle 校验，只验证 sopify_contracts + sopify_writer + catalog 安装完整性）
- [x] Output: 更新 `scripts/release-preflight.sh`——移除 runtime bundle / runtime gate smoke 相关步骤，保留 catalog drift + protocol smoke
- [x] Output: 替换为 `sopify_protocol_check` smoke（W1.6 已建）
- [x] Output: 保留 catalog drift check（路径已更新 by W2.0b）+ installer/payload smoke
- [x] Verify: CI pipeline 绿；无 runtime-only test step
- [x] Verify: catalog drift check 和 protocol smoke 在 CI 中正常运行

### W2.3c Host Prompt / Copilot Instructions Cutover

- [x] Depends: W2.3b
- [x] Input: `.github/copilot-instructions.md`
- [x] Output: 清理 runtime-first 措辞（runtime gate / sopify_runtime 引用）
- [x] Output: 删除不存在的 `go_plan_runtime.py` 引用
- [x] Output: 替换为 protocol-first 入口（protocol.md + sopify_writer）；sopify_protocol_check 是 CI/preflight 验证项（W2.3b 已接入），不进入宿主 prompt
- [x] Verify: `rg "runtime_gate|sopify_runtime|go_plan_runtime" .github/copilot-instructions.md` returns no matches
- [x] Verify: copilot-instructions.md 不再引用 runtime-first 入口

### W2.4 Migrate StateStore to 2-File Model

- [x] Depends: W2.3
- [x] Input: `sopify_writer/store.py` / `sopify_contracts/*`
- [x] Output: `StateStore.get/set/clear_active_plan`
- [x] Output: `StateStore.get/set/clear_current_handoff`
- [x] Output: removed writer methods for current_run/current_plan/current_clarification/current_decision/current_archive_receipt/last_route
- [x] Verify: `state/active_plan.json` contains only `plan_id`
- [x] Verify: current_handoff carries plan_id, plan_path, required_host_action, artifacts, notes, observability
- [x] Verify: post-P8 writer/schema 不再要求 `route_name` / `run_id` 作为 current_handoff 主链 required 字段
- [x] Verify: no sopify_writer code writes removed state files

### W2.5 Fold Clarification/Decision Into Handoff

- [x] Depends: W2.4
- [x] Input: current ClarificationState / DecisionState semantics
- [x] Output: handoff artifacts convention for questions/options/submission state
- [x] Output: `required_host_action=answer_questions` replaces current_clarification
- [x] Output: `required_host_action=confirm_decision` replaces current_decision
- [x] Verify: compliance fixture can represent clarification pending with only current_handoff
- [x] Verify: compliance fixture can represent decision pending with only current_handoff

### W2.6 Retire Registry Chain

- [ ] Depends: W1.4
- [ ] Input: `runtime/plan/registry.py`, registry tests, output renderer priority notes, `_registry.yaml`
- [ ] Output: delete `runtime/plan/registry.py`
- [ ] Output: remove registry upsert/recommend/inspect callers
- [ ] Output: remove `_registry.yaml` from active plan directory
- [ ] Output: remove registry tests or migrate only non-registry plan lookup behavior
- [ ] Output: remove registry mention from docs
- [ ] Verify: `find .sopify-skills/plan -name _registry.yaml` returns no files
- [ ] Verify: `rg "plan.registry|_registry|registry_is_observe_only|suggested_priority" runtime sopify_writer sopify_contracts installer scripts tests docs README.md README.zh-CN.md` returns no active code/docs

### W2.7 Reclassify Tests

- [ ] Depends: W2.0b, W2.1-W2.3, W2.2b, W2.3b-W2.3c, W2.4-W2.6
- [ ] Input: all tests importing runtime
- [ ] Output: keep protocol / contracts / sopify_writer / installer / compliance tests
- [ ] Output: delete runtime router/engine/gate/output tests
- [ ] Output: migrate useful state invariant tests to sopify_writer
- [ ] Output: migrate plan lookup/scaffold tests if the code survives outside runtime
- [ ] Output: **显式删除清单**（审计确认，以下文件必须删除）：
  - `tests/runtime_test_support.py`（269 行共享 helper，import 20+ runtime 模块，是 15+ 测试文件的 import 根）
  - `test_runtime_engine.py` / `test_runtime_gate.py` / `test_runtime_router.py` / `test_runtime_orchestration.py` / `test_runtime_execution_gate.py`
  - `test_runtime_kb.py` / `test_runtime_knowledge_layout.py` / `test_runtime_config.py` / `test_runtime_output_rendering.py` / `test_runtime_state.py`
  - `test_runtime_decision.py` / `test_runtime_plan_reuse.py` / `test_runtime_plan_intent.py` / `test_runtime_plan_lookup.py` / `test_runtime_plan_registry.py` / `test_runtime_plan_scaffold.py` / `test_runtime_preferences.py`
  - `test_bundle_smoke.py`
  - `test_action_intent.py`（2561 行，测试 runtime.action_intent / runtime.gate / runtime.engine）
- [ ] Output: **显式外科手术清单**（以下文件保留但需局部修改）：
  - `tests/test_installer.py`：删除第 46-47 行 `from runtime.engine import run_runtime` / `from runtime.output import render_runtime_output`；重写或移除 `HostPromptContractTests._assert_installed_footer_contract`（~1193 行）中的 `run_runtime()` 调用
  - `tests/test_release_hooks.py`：更新 `_init_release_hook_fixture` 中合成仓库 fixture 的 `runtime/gate.py` 文件路径
  - `tests/test_installer_status_doctor.py`：更新 bundle copy 操作中 `runtime` 目录名引用
  - `tests/test_installer_validate.py`：删除或改写全部 `run_bundle_smoke_check` / `check-bundle-smoke.sh` 相关测试方法（line 16 import + line 24/37/48/61/73/87/92/98 共 9 处引用）；W2.8 删除 smoke 脚本后这些测试必须同步清理
- [ ] Output: **Fixture 清理清单**：
  - `tests/fixtures/p4d_smoke/`：检查是否仍被活跃测试引用；如无引用则整体删除（含 `current_decision.json` / `current_run.json` / `current_gate_receipt.json` 等已退役 state 文件）
  - `tests/fixtures/sample_invariant_gate_matrix.yaml`：删除（引用 runtime gate 概念）
- [ ] Output: 清理 `tests/conftest.py` 中 `implementation_mirror` marker 注册（仅被 `test_runtime_router.py` 使用，已删除）
- [ ] Verify: `rg "from runtime|import runtime|runtime\\." tests` returns no active imports
- [ ] Verify: retained test names reflect new modules, not runtime
- [ ] Verify: `runtime_test_support.py` 不存在；无 test 文件 import 它

### W2.8 Remove Runtime Entrypoints and Bundle

- [ ] Depends: W2.1-W2.7
- [ ] Input: `scripts/runtime_gate.py`, `scripts/sopify_runtime.py`, `scripts/check-prompt-runtime-gate-smoke.py`, `installer/sopify_bundle.py`
- [ ] Output: delete runtime gate/default runtime entry/bundle smoke scripts
- [ ] Output: remove bundle manifest fields that point to runtime entry
- [ ] Output: **显式脚本删除清单**：
  - `scripts/runtime_gate.py`
  - `scripts/sopify_runtime.py`
  - `scripts/check-prompt-runtime-gate-smoke.py`
  - `scripts/check-bundle-smoke.sh`
  - `installer/sopify_bundle.py`（如 W2.2 未整体删除）
- [ ] Output: **CI / release-preflight 同步清单**（与 W2.3b 协同）：
  - `.github/workflows/ci.yml`：移除 `check-bundle-smoke.sh` / `check-prompt-runtime-gate-smoke.py` step；改写 `check-install-payload-bundle-smoke.py` step 为 payload/catalog smoke
  - `scripts/release-preflight.sh`：移除 runtime bundle / runtime gate smoke 相关步骤
  - `scripts/check-install-payload-bundle-smoke.py`：改写为 payload/catalog smoke（或整体替换为新脚本）
- [ ] Verify: `rg "runtime_gate.py|sopify_runtime.py|default_runtime_entry|runtime_gate_entry" installer scripts tests docs README.md README.zh-CN.md .sopify-skills/blueprint` returns no active dependency
- [ ] Verify: `scripts/check-bundle-smoke.sh` 和 `scripts/check-prompt-runtime-gate-smoke.py` 不存在

### W2.9 Remove Deep Host Adapters

- [ ] Depends: W2.2 / W2.8
- [ ] Input: `installer/hosts/{codex,claude}.py`
- [ ] Output: delete deep adapters for Codex/Claude
- [ ] Output: keep payload-capable host path, including Copilot if still useful
- [ ] Output: installer host exports updated
- [ ] Verify: `rg "deep_verified|hosts.codex|hosts.claude|runtime gate" installer docs README.md README.zh-CN.md` returns no active deep path

### W2.10 Delete runtime/ Directory

- [ ] Depends: W2.0b, W2.1-W2.3, W2.2b, W2.3b-W2.3c, W2.4-W2.9
- [ ] Input: `runtime/` all files
- [ ] Output: delete `runtime/`
- [ ] Output: 确认 W2.7 fixture 清理清单已执行（`tests/fixtures/p4d_smoke/`、`tests/fixtures/sample_invariant_gate_matrix.yaml`）
- [ ] Verify: `test ! -d runtime`
- [ ] Verify: `rg "from runtime|import runtime|runtime\\." . -g '!**/__pycache__/**'` returns no active code imports
- [ ] Verify: `python3 scripts/sopify_protocol_check.py check --scenario continuation --fixture <current>` passes

### W2.11 Dogfood Mainline

- [ ] Depends: W2.10
- [ ] Input: current repo
- [ ] Output: create/update active plan through sopify_writer
- [ ] Output: write current_handoff through sopify_writer
- [ ] Output: finalize to history with final receipt
- [ ] Verify: state/ only contains `active_plan.json` and `current_handoff.json` during active flow
- [ ] Verify: finalize clears active_plan/current_handoff
- [ ] Verify: no `_registry.yaml`
- [ ] Verify: compliance 3 scenarios all pass

### Wave 2 Gate

- [ ] Depends: W2.0a-W2.0b, W2.1-W2.3, W2.2b, W2.3b-W2.3c, W2.4-W2.11
- [ ] Verify: runtime directory absent
- [ ] Verify: registry absent
- [ ] Verify: no runtime imports in active code/tests
- [ ] Verify: compliance 3 scenarios pass
- [ ] Stop: W2 gate must pass before W3 starts

---

## Wave 3 — Qoder Host Proof + Narrative Cutover

目标：用 Qoder proof 证明 Sopify 是协议内核，不是 runtime 工作流系统。

### W3.1 Build Qoder Payload Adapter

- [ ] Depends: W2 gate
- [ ] Input: existing payload host patterns, Copilot payload-capable adapter
- [ ] Output: `installer/hosts/qoder/` or equivalent payload target
- [ ] Output: Qoder prompt asset consumes Host Protocol Entry Contract
- [ ] Output: Qoder prompt asset includes 4-step continuation instructions
- [ ] Output: install path through `install.sh --target qoder`
- [ ] Verify: adapter does not import runtime
- [ ] Verify: adapter does not depend on `_registry.yaml`
- [ ] Verify: `.qoder/` repo wiki config is not treated as Sopify state
- [ ] Verify: Qoder prompt asset does not ask LLM to run `runtime_gate.py`

### W3.2 Qoder Continuation Writer Path

- [ ] Depends: W3.1
- [ ] Input: sopify_writer 2-file model
- [ ] Output: Qoder can write `state/current_handoff.json`
- [ ] Output: Qoder can write `plan/<id>/receipts/exec_NNN.json` / `verify_NNN.json`
- [ ] Output: Qoder uses sopify_writer library/API; no writer CLI unless host limitation forces a thin wrapper
- [ ] Verify: Qoder new session reads `active_plan → plan.md → current_handoff → receipts`
- [ ] Verify: same fixture can be resumed without runtime process

### W3.3 End-to-End Proof Transcript

- [ ] Depends: W3.2
- [ ] Input: fixture repo
- [ ] Output: transcript showing session A writes handoff/receipt
- [ ] Output: transcript showing session B resumes from files
- [ ] Verify: transcript includes active_plan plan_id, plan.md Plan Snapshot or full-plan fallback, plan/task decision context, handoff required_host_action, latest receipt
- [ ] Verify: no command invokes runtime

### W3.5 Docs Narrative Cutover

- [ ] Depends: W3.3
- [ ] Input: README / README.zh-CN / docs/how-sopify-works(.en).md / docs/getting-started.md
- [ ] Output: main narrative becomes "host executes; Sopify preserves auditable AI development assets through protocol, file assets, sopify_writer, receipts"
- [ ] Output: docs describe the post-P8 product stack as protocol kernel + default workflow + skills/host adapters
- [ ] Output: docs clarify runtime retirement does not retire analyze/design/develop/kb/templates workflow or development skills; those layers consume protocol assets and write through sopify_writer
- [ ] Output: architecture diagrams reflect 2 state files + plan/history/receipts
- [ ] Output: remove runtime gate first language
- [ ] Output: remove `_registry.yaml` from user-facing docs
- [ ] Verify: docs present cross-host continuation as a hard proof of asset portability, not the whole Sopify value proposition
- [ ] Verify: docs do not describe protocol kernel as the whole product, and do not describe default workflow/skills as independent machine truth
- [ ] Verify: docs do not describe Plan Snapshot as a directory index, registry, or authoritative audit evidence
- [ ] Verify: `rg "runtime gate|runtime/|_registry|current_run|current_plan" README.md README.zh-CN.md docs` returns no active legacy docs

### W3.6 Blueprint Sync（全量叙事收口 — 11 项显式回写清单）

- [ ] Depends: W3.5
- [ ] Input: `.sopify-skills/blueprint/README.md`, `design.md`, `tasks.md`, `protocol.md`
- [ ] Output: ADR-013 scope clarification 从 interim disclaimer 升级为 final 语义边界
- [ ] Output: ADR-017 EAR 标注从 interim [SUPERSEDED] 升级为 final [RETIRED]
- [ ] Output: 底层哲学收敛链 produce→verify→authorize→settle → produce→verify→record evidence→settle
- [ ] Output: 实操协议层显式声明 write admission + archive admission 两个准入点
- [ ] Output: Protocol-first / Runtime-optional 三层定位更新（runtime 层标 legacy reference 或删除）
- [ ] Output: 核心管线 ActionProposal / Validator 表述（Validator 从"唯一授权者"收窄为 protocol admission）
- [ ] Output: Runtime 五层架构段落标 legacy reference 或删除
- [ ] Output: Core State Files / Persistence Surface / Mainline Keep-list 更新为 2 文件模型
- [ ] Output: 外部消费面 Keep-list 全面更新（删除 EAR/gate_receipt/runtime-only 面）
- [ ] Output: 宿主能力治理段落重定义（能力梯度、契约消费矩阵、官方接入画像、增强组合）
- [ ] Output: Runtime 退场路线标记完成 + LOC 数据更新
- [ ] Output: blueprint design state model updated to 2 files
- [ ] Output: registry retirement recorded
- [ ] Output: blueprint product model updated to protocol kernel + default workflow + skills/host adapters, with protocol kernel as the only truth/evidence layer
- [ ] Output: blueprint tasks runtime retirement Phase 2 marked done
- [ ] Output: protocol.md §8 / state file index / EAR section 同步更新
- [ ] Verify: blueprint no longer calls runtime state files "运行期不可删"
- [ ] Verify: blueprint does not imply default workflow or development skills were removed by runtime retirement
- [ ] Verify: ADR-017 EAR 标注为 [RETIRED by P8]（非 [SUPERSEDED]）
- [ ] Verify: 蓝图中 "Validator 是唯一授权者" 表述已收窄为 protocol admission / receipt validity / archive admission
- [ ] Verify: 蓝图 Runtime 五层架构段落已标 legacy reference 或整体删除

### Wave 3 Gate

- [ ] Depends: W3.1-W3.6
- [ ] Verify: Qoder consumes active_plan to locate plan
- [ ] Verify: Qoder reads plan.md to understand progress
- [ ] Verify: Qoder writes handoff + receipts that another session can consume
- [ ] Verify: whole chain has no runtime process

---

## Finalize

### F1 Final Receipts

- [ ] Depends: W3 gate
- [ ] Output: `plan/<id>/receipts/final.json`
- [ ] Output: final receipt includes outcome, verification commands, key decisions, deleted surfaces
- [ ] Verify: final receipt validates against schema

### F2 Archive

- [ ] Depends: F1
- [ ] Output: move plan package to `history/2026-06/20260605_p8_protocol_kernel_runtime_retirement/`
- [ ] Output: generate `history/.../receipt.md`
- [ ] Output: clear active_plan/current_handoff
- [ ] Verify: history receipt includes runtime deletion, registry deletion, Qoder proof, docs cutover

### F3 Release Notes

- [ ] Depends: F2
- [ ] Output: CHANGELOG entry
- [ ] Output: README headline reflects protocol kernel target state
- [ ] Verify: install/getting-started path matches post-P8 architecture
