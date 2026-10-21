# T7 + T8 执行报告

结论：已完成本轮受限写入范围，两宿主共用一套扁平 Skill 安装实现；完整测试与 release preflight 均通过。Antigravity 和 Trae 的真实候选版本会话行为尚未验证，两项 Doctor 行为检查均保留 `skip (BLACK_BOX_NOT_VERIFIED)`。

## 基线与边界

- 基线：`feat/sopify-narrow-focus`，`828588892ad16a6a0b91ff0edc9b81fd4b897367`，开始时工作区干净。
- 收尾时 HEAD 为 `6f081006871b652eb63fcedbb38367da7c017a17`：运行期间有其他执行方提交 W2 验收/探针证据及方案状态，diff 仅涉及 `.sopify/plan/20261020_sopify_narrow_focus/`。本 worker 没有提交；本轮 24 个实现文件仍未提交，测试覆盖的代码没有因此变化。
- 输入已读：派工文件、方案 T7/T8 与 Key Decisions、统一验收标准、`docs/host-onboarding.md`、`docs/cursor-host.md`、`t7-probe-gemini.md`、`audits/planning/trae-r6.md`。宿主事实采用派工确认的探针证据，本轮没有重复向真实 home 安装或做加载探针。
- 没有 commit、push；未改 `.sopify/**`、README、Pages、writer/contracts schema、真实 `~/.gemini` 或 `~/.trae`；Git index 未改。所有本轮安装、修复与快照生成使用显式临时 `home_root`，不重定向真实 HOME。

## 实现与公共登记

`installer/hosts/flat.py` 负责两者唯一的扁平投影、资源改写与同步流程。两个 host 模块只声明落点、默认语言和能力，不复制安装实现；继续使用既有 `header_embedded` 指令面，没有新增配置文件、用户开关、Hook 或 MCP 注册。

- 五个阶段注册为 `sopify-analyze/design/develop/kb/templates`；canonical 中英文 Skill 源文件没有复制或修改。header 的原路由表就地加入实际安装路径，没有新增第二份路由清单。
- 共享资源每个宿主只保留 `skills/sopify/references/` 一份；阶段通过 `../sopify/references/` 引用。资源正文中的跨阶段相对引用也会按源文件位置重定位；仓库路径形式的脚本命令改为该宿主的可移植 `~/.../skills/sopify-*/scripts/`。
- 先在临时目录完成渲染并校验 managed block，再写入宿主目录。复用 W1 的公开 `upsert_managed_instruction_block` 和 `skill_tree_matches`，不跨模块引用私有函数。五个阶段目录和共享 references 分别做完整树比对；额外的自有过期文件会清理，其他 Skill 和配置保持不变。
- Antigravity 将 managed block 写入 `~/.gemini/config/AGENTS.md`。Trae 的 `skills/sopify/SKILL.md` 使用一个共用的短入口元数据模板，前置 YAML 保持合法，正文直接承载同一 header managed block。入口身份元数据可修复，块外用户正文保留；不写 Trae 全局 AGENTS。
- 注册、`skills/hosts.yaml`、五个 catalog manifest 的 `host_support`、生成 catalog、显示名和 Doctor 已接入。新增 `docs/antigravity-host.md`、`docs/trae-host.md`，均链接 recipe。
- target 支持 `antigravity:zh-CN|en-US`、`trae:zh-CN|en-US`；裸 target 默认 `en-US`，对齐 Cursor。没有宣称所有既有宿主默认值一致：Codex/Claude 要显式语言，Qoder 默认中文。

## 验证结果

| 检查 | 结果与证据 |
|---|---|
| 临时 home 安装、重装、修复、语言切换、用户内容保留 | 两宿主 × 两语言通过；删除资源、修改规则、加入过期文件、Trae 元数据损坏均修复；用户其他 Skill、配置与块外 CRLF 正文保留 |
| malformed managed block | 两宿主均在任何宿主文件写入前失败，前后文件快照相同 |
| 扁平引用 | 每套 29 处 prompt 资源引用解析成功，0 悬空；包含 5 个 header 路由，阶段内部与共享资源引用；另用实际装入的跨阶段/共享相对链接样本验证资源正文改写 |
| 可执行脚本 | 从无源码依赖的临时项目目录执行安装后的 Analyze 评分脚本，成功返回 JSON |
| description | Trae 顶层 250 字符；中文阶段 25–65、英文阶段 102–137，全部低于 1024 |
| Doctor | prompt、Skill tree、payload 为 pass；行为为 skip/BLACK_BOX_NOT_VERIFIED；删除共享资源后 tree fail 且 installed=no；只有用户 settings 不算 Sopify 已安装 |
| full suite | **406 passed, 97 subtests passed**，52.15 秒；见 [pytest-full.log](t7t8-evidence/pytest-full.log) |
| release preflight | **All checks passed**；包含 golden、catalog drift、全量测试、5 个协议场景、install/payload smoke，见 [release-preflight.log](t7t8-evidence/release-preflight.log) |
| diff 与保护面 | `git diff --check` 通过；受保护路径与暂存区无 diff |

执行环境：`PATH=/opt/homebrew/opt/python@3.11/libexec/bin:$PATH PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS="-p no:cacheprovider"`。首次全量测试只给主进程指定 3.11，release-sync 子进程使用系统 3.9，导致一项发版测试失败；统一 PATH 后同一测试通过，全量与 preflight 随后全部通过，没有为此放宽断言。

新增测试集中于 `tests/test_flat_hosts.py`，避免为两个宿主复制套件。共享注册/catalog 断言已更新；golden 测试覆盖四个实际安装产物。同步补齐 `scripts/regenerate-golden-snapshots.py` 与发版夹具，使下一次 release-sync 保留并刷新新增快照；本轮基线经下述审阅后手工写入，未运行生成器覆盖来消除失败。

## Golden 审阅

四套 prompt 各 24 个文件。审阅确认：AGY 入口位置正确、Trae frontmatter 在首行；没有多余嵌套阶段；路由改名、共享引用和脚本路径正确；共享资源只有一份；不嵌入本机绝对路径。原 8 项 golden 保持原值，仅新增以下四项；catalog diff 仅增加两个 host_support 和生成时间。

| target | flat_prompt_tree SHA-256 |
|---|---|
| antigravity:zh-CN | `5f4e4c94a1c42c83be0f2d8ba6c8cb2e122527c3cbed34b101066bfb22945e90` |
| antigravity:en-US | `acbb5a3670799de5a5f5a10c6b09c8aa3dda102812494555c84e572d4539e714` |
| trae:zh-CN | `20cb5c41d2e5a6bfec471d2010997ad577e9e3706b525b1f74fb4412466e8102` |
| trae:en-US | `787a3e13d45509af13a6666b9fd2559e81abb9fe4962977925e684d49a69edd9` |

原始记录：[安装与 Doctor 汇总](t7t8-evidence/installation-results.json)、[逐条引用检查](t7t8-evidence/reference-checks.json)、[golden 候选值](t7t8-evidence/golden-candidates.json)。同目录保存每套的 `*-file-hashes.json`、`*-doctor.json` 和完整树。

## 与现有宿主的差异及原因

| 差异 | 原因 |
|---|---|
| 阶段由嵌套目录改为同级 `sopify-*` | AGY 探针只发现一层，Trae 嵌套发现未证实；阶段语义与资源源文件一致 |
| AGY 使用 `.gemini/config`，不使用 `.gemini` 根作为安装根 | 已确认的规则/Skill 落点；payload 与 config 同根，沿用 installer 的 host-root 规则 |
| Trae 入口直接嵌入 header，Cursor 顶层入口另读 Plugin Rule | Trae 没有已证明的全局规则读取面，也没有本期 Plugin Rule；直接用已有 header 可避免另一份宿主规则正文 |
| Trae 双语入口 description 固定，正文按选定语言安装 | 一份 250 字符元数据足够发现；避免为同一身份复制两个模板，用户操作不增加 |
| 两者无 hooks；Doctor 只检查现有安装面和待验证行为 | 用户确认的 baseline 范围；不借 Cursor 已有增强扩大实现 |

## 统一验收标准：仅风险与未验证项

1. 两宿主本候选的真实会话闭环尚未运行，尤其是模型选择入口、跨目录读取共享资源、评分工具调用、恢复/finalize。磁盘引用可达仅是安装证据；下一步由 Antigravity 主 dogfood 验收，Trae 按用户决定照常推进、问题后续修复。
2. AGY 探针展示四个全局文件的加载顺序，不证明冲突优先级；Trae 自检没有全局文件正例，也不能证明宿主永远不会读取全局规则。文档将这些结论限定为观察范围，未据此增加其他规则写入。
3. recipe 把 BASELINE_SUPPORTED 与真实黑盒完成关联，本次任务明确允许 Trae 在 BLACK_BOX_NOT_VERIFIED 下实现并发布。该例外来自用户决定；注册 tier 不等于本轮已经完成 protocol 认证。

没有其他发现的不通过项。未验证事项没有提升为安装成功证据。

## 作为使用者的体验

recipe 的能力矩阵、安装/可见/遵循三层证据、注册文件清单、禁止修改设置边界都可直接使用，按它能找到公共安装器、Doctor 和测试入口。两个宿主的差异让“先找真实加载面”比复制 Cursor 适配更有价值。

不足主要在贡献者说明：三种 instruction surface 的描述把 header_embedded 和嵌套 Skill 布局绑在一起，没有说明“同一 header 可承载在入口 Skill 中、Skill 布局独立于规则位置”；本实现只加布局与可选元数据声明，仍复用原指令面。recipe 也没有提示黄金快照生成器需要与快照覆盖范围同步，以及测试子进程要统一 Python PATH。未修改 recipe，供协调者合并 T6b/T10 时决定是否补一句。

## 实际安装文件树

四个显式临时 home 均保留在 `t7t8-evidence/<host>-<locale>-home/`；每套 48 个文件：24 个 prompt/Skill 文件和 24 个既有 payload 文件。先安装 prompt 审阅 golden，再运行完整 installer API，因此安装汇总中首次完整安装显示 prompt=skipped、payload=installed；再次安装两者均 skipped。

以下是中文两套的实际完整文件清单，路径相对各自临时 home。英文路径完全同构，内容由各自 golden/hash 区分，原始清单见 [AGY English](t7t8-evidence/antigravity-en-US-full-tree.txt) 和 [Trae English](t7t8-evidence/trae-en-US-full-tree.txt)。

### Antigravity

```text
.gemini/config/AGENTS.md
.gemini/config/skills/sopify/references/output-contract.md
.gemini/config/skills/sopify/references/shared-writing-dna.md
.gemini/config/skills/sopify-analyze/SKILL.md
.gemini/config/skills/sopify-analyze/assets/question-output.md
.gemini/config/skills/sopify-analyze/assets/success-output.md
.gemini/config/skills/sopify-analyze/references/analyze-rules.md
.gemini/config/skills/sopify-analyze/scripts/score_requirement.py
.gemini/config/skills/sopify-design/SKILL.md
.gemini/config/skills/sopify-design/assets/adr-template.md
.gemini/config/skills/sopify-design/assets/design-template.md
.gemini/config/skills/sopify-design/assets/output-summary.md
.gemini/config/skills/sopify-design/assets/plan-template.md
.gemini/config/skills/sopify-design/assets/tasks-template.md
.gemini/config/skills/sopify-design/references/design-rules.md
.gemini/config/skills/sopify-design/scripts/select_plan_level.py
.gemini/config/skills/sopify-develop/SKILL.md
.gemini/config/skills/sopify-develop/assets/output-partial.md
.gemini/config/skills/sopify-develop/assets/output-quick-fix.md
.gemini/config/skills/sopify-develop/assets/output-success.md
.gemini/config/skills/sopify-develop/references/develop-rules.md
.gemini/config/skills/sopify-develop/scripts/extract_pending_tasks.py
.gemini/config/skills/sopify-kb/SKILL.md
.gemini/config/skills/sopify-templates/SKILL.md
.gemini/config/sopify/bundles/2026-08-30.001152/catalog/builtin_catalog.generated.json
.gemini/config/sopify/bundles/2026-08-30.001152/manifest.json
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_contracts/__init__.py
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_contracts/artifacts.py
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_contracts/core.py
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_contracts/decision.py
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_contracts/handoff.py
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_contracts/plan_package.py
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_contracts/proposal.py
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_contracts/schemas/active_plan.schema.json
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_contracts/schemas/current_handoff.schema.json
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_contracts/schemas/history_receipt.schema.json
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_contracts/schemas/plan_md_sections.schema.json
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_contracts/schemas/plan_receipt.schema.json
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_contracts/skill_schema.py
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_writer/__init__.py
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_writer/_time.py
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_writer/invariants.py
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_writer/io.py
.gemini/config/sopify/bundles/2026-08-30.001152/sopify_writer/store.py
.gemini/config/sopify/helpers/bootstrap_workspace.py
.gemini/config/sopify/payload-manifest.json
.gemini/config/sopify/resources/copilot/full.md
.gemini/config/sopify/resources/copilot/manifest.json
```

### Trae

```text
.trae/skills/sopify/SKILL.md
.trae/skills/sopify/references/output-contract.md
.trae/skills/sopify/references/shared-writing-dna.md
.trae/skills/sopify-analyze/SKILL.md
.trae/skills/sopify-analyze/assets/question-output.md
.trae/skills/sopify-analyze/assets/success-output.md
.trae/skills/sopify-analyze/references/analyze-rules.md
.trae/skills/sopify-analyze/scripts/score_requirement.py
.trae/skills/sopify-design/SKILL.md
.trae/skills/sopify-design/assets/adr-template.md
.trae/skills/sopify-design/assets/design-template.md
.trae/skills/sopify-design/assets/output-summary.md
.trae/skills/sopify-design/assets/plan-template.md
.trae/skills/sopify-design/assets/tasks-template.md
.trae/skills/sopify-design/references/design-rules.md
.trae/skills/sopify-design/scripts/select_plan_level.py
.trae/skills/sopify-develop/SKILL.md
.trae/skills/sopify-develop/assets/output-partial.md
.trae/skills/sopify-develop/assets/output-quick-fix.md
.trae/skills/sopify-develop/assets/output-success.md
.trae/skills/sopify-develop/references/develop-rules.md
.trae/skills/sopify-develop/scripts/extract_pending_tasks.py
.trae/skills/sopify-kb/SKILL.md
.trae/skills/sopify-templates/SKILL.md
.trae/sopify/bundles/2026-08-30.001152/catalog/builtin_catalog.generated.json
.trae/sopify/bundles/2026-08-30.001152/manifest.json
.trae/sopify/bundles/2026-08-30.001152/sopify_contracts/__init__.py
.trae/sopify/bundles/2026-08-30.001152/sopify_contracts/artifacts.py
.trae/sopify/bundles/2026-08-30.001152/sopify_contracts/core.py
.trae/sopify/bundles/2026-08-30.001152/sopify_contracts/decision.py
.trae/sopify/bundles/2026-08-30.001152/sopify_contracts/handoff.py
.trae/sopify/bundles/2026-08-30.001152/sopify_contracts/plan_package.py
.trae/sopify/bundles/2026-08-30.001152/sopify_contracts/proposal.py
.trae/sopify/bundles/2026-08-30.001152/sopify_contracts/schemas/active_plan.schema.json
.trae/sopify/bundles/2026-08-30.001152/sopify_contracts/schemas/current_handoff.schema.json
.trae/sopify/bundles/2026-08-30.001152/sopify_contracts/schemas/history_receipt.schema.json
.trae/sopify/bundles/2026-08-30.001152/sopify_contracts/schemas/plan_md_sections.schema.json
.trae/sopify/bundles/2026-08-30.001152/sopify_contracts/schemas/plan_receipt.schema.json
.trae/sopify/bundles/2026-08-30.001152/sopify_contracts/skill_schema.py
.trae/sopify/bundles/2026-08-30.001152/sopify_writer/__init__.py
.trae/sopify/bundles/2026-08-30.001152/sopify_writer/_time.py
.trae/sopify/bundles/2026-08-30.001152/sopify_writer/invariants.py
.trae/sopify/bundles/2026-08-30.001152/sopify_writer/io.py
.trae/sopify/bundles/2026-08-30.001152/sopify_writer/store.py
.trae/sopify/helpers/bootstrap_workspace.py
.trae/sopify/payload-manifest.json
.trae/sopify/resources/copilot/full.md
.trae/sopify/resources/copilot/manifest.json
```

## 修改文件

共 24 个仓库文件；完整清单如下，未暂存。

- `docs/antigravity-host.md`
- `docs/trae-host.md`
- `installer/distribution.py`
- `installer/hosts/__init__.py`
- `installer/hosts/antigravity.py`
- `installer/hosts/base.py`
- `installer/hosts/flat.py`
- `installer/hosts/trae.py`
- `installer/inspection.py`
- `scripts/regenerate-golden-snapshots.py`
- `skills/catalog/analyze/skill.yaml`
- `skills/catalog/builtin_catalog.generated.json`
- `skills/catalog/design/skill.yaml`
- `skills/catalog/develop/skill.yaml`
- `skills/catalog/kb/skill.yaml`
- `skills/catalog/templates/skill.yaml`
- `skills/hosts.yaml`
- `skills/trae-entry-skill.md.template`
- `tests/golden-snapshots.json`
- `tests/test_flat_hosts.py`
- `tests/test_golden_snapshots.py`
- `tests/test_installer_status_doctor.py`
- `tests/test_plan_contract_assets.py`
- `tests/test_release_hooks.py`
